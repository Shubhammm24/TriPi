"use client";

import { useCallback, useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useVoice, VoiceStatus } from "@/app/hooks/useVoice";
import { useVoiceSettings } from "@/app/hooks/useVoiceSettings";

/* ═══════════════════════════════════════════════════════════
   VoiceInput — Microphone button with real-time waveform

   A reusable component that:
   1. Shows a 🎤 mic button (hides if browser doesn't support STT)
   2. When recording: pulsing ring + real-time waveform visualizer
   3. Pipes final transcript to the parent via onTranscript callback
   4. Interim text shown in real-time as the user speaks
   ═══════════════════════════════════════════════════════════ */

interface VoiceInputProps {
  /** Called with the final recognized text */
  onTranscript: (text: string) => void;
  /** Optional: append to existing text instead of replacing */
  appendMode?: boolean;
  /** Optional: current text value (used in append mode) */
  currentValue?: string;
  /** Optional: custom tooltip text */
  tooltip?: string;
  /** Optional: compact mode (smaller button, no label) */
  compact?: boolean;
  /** Optional: language for recognition */
  language?: string;
}

export default function VoiceInput({
  onTranscript,
  appendMode = true,
  currentValue = "",
  tooltip,
  compact = false,
  language,
}: VoiceInputProps) {
  const { settings, playChime } = useVoiceSettings();
  const [showError, setShowError] = useState(false);

  const {
    isSupported,
    status,
    transcript,
    interimTranscript,
    toggleListening,
    stopListening,
    clearTranscript,
    errorMessage,
  } = useVoice({
    language: language || settings.sttLanguage,
    continuous: true,
    interimResults: true,
    onResult: (text) => {
      playChime("stop");
      if (appendMode && currentValue) {
        const separator = currentValue.endsWith(" ") ? "" : " ";
        onTranscript(currentValue + separator + text);
      } else {
        onTranscript(text);
      }
    },
    onError: () => {
      playChime("pop");
      setShowError(true);
      setTimeout(() => setShowError(false), 4000);
    },
  });

  // Audio analyser for waveform visualization
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);

  /** Set up audio analyser when recording starts */
  useEffect(() => {
    if (status === "listening") {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          streamRef.current = stream;
          const audioCtx = new AudioContext();
          const source = audioCtx.createMediaStreamSource(stream);
          const analyser = audioCtx.createAnalyser();
          analyser.fftSize = 64;
          source.connect(analyser);
          analyserRef.current = analyser;

          drawWaveform();
        })
        .catch(() => {
          // Microphone already captured by SpeechRecognition — draw fallback
          drawFallbackWaveform();
        });
    } else {
      // Cleanup
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      analyserRef.current = null;
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    }

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  /** Draw real audio waveform bars */
  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const barCount = 20;

    const draw = () => {
      animFrameRef.current = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barWidth = canvas.width / barCount;
      const gap = 2;

      for (let i = 0; i < barCount; i++) {
        const dataIndex = Math.floor((i / barCount) * bufferLength);
        const value = dataArray[dataIndex] / 255;
        const barHeight = Math.max(3, value * canvas.height * 0.8);

        const x = i * barWidth + gap / 2;
        const y = (canvas.height - barHeight) / 2;

        // Gradient from primary to secondary
        const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
        gradient.addColorStop(0, "#a3a6ff");
        gradient.addColorStop(1, "#4cd7f6");

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth - gap, barHeight, 2);
        ctx.fill();
      }
    };

    draw();
  }, []);

  /** Fallback animated waveform when real audio data isn't available */
  const drawFallbackWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const barCount = 20;
    let frame = 0;

    const draw = () => {
      animFrameRef.current = requestAnimationFrame(draw);
      frame++;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barWidth = canvas.width / barCount;
      const gap = 2;

      for (let i = 0; i < barCount; i++) {
        const value = 0.3 + 0.7 * Math.abs(Math.sin((frame * 0.05) + (i * 0.4)));
        const barHeight = Math.max(3, value * canvas.height * 0.7);

        const x = i * barWidth + gap / 2;
        const y = (canvas.height - barHeight) / 2;

        const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
        gradient.addColorStop(0, "#a3a6ff");
        gradient.addColorStop(1, "#4cd7f6");

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth - gap, barHeight, 2);
        ctx.fill();
      }
    };

    draw();
  }, []);

  // Don't render if browser doesn't support speech recognition
  if (!isSupported) return null;

  const isListening = status === "listening";

  return (
    <div className="voice-input-wrapper">
      {/* Mic Button */}
      <motion.button
        type="button"
        className={`voice-mic-btn ${isListening ? "voice-mic-btn--active" : ""} ${compact ? "voice-mic-btn--compact" : ""}`}
        onClick={() => {
          playChime(isListening ? "stop" : "start");
          toggleListening();
        }}
        whileTap={{ scale: 0.92 }}
        title={tooltip || (isListening ? "Stop listening" : "Click to speak")}
        aria-label={isListening ? "Stop voice input" : "Start voice input"}
      >
        {/* Pulsing ring when active */}
        {isListening && (
          <motion.span
            className="voice-pulse-ring"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
          />
        )}

        {/* Icon */}
        <span className="voice-mic-icon">
          {isListening ? "⏹" : "🎤"}
        </span>
      </motion.button>

      {/* Expanded recording panel */}
      <AnimatePresence>
        {isListening && (
          <motion.div
            className="voice-recording-panel"
            initial={{ opacity: 0, y: 8, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: 8, height: 0 }}
            transition={{ duration: 0.25 }}
          >
            {/* Waveform */}
            <canvas
              ref={canvasRef}
              width={200}
              height={32}
              className="voice-waveform"
            />

            {/* Live transcript */}
            {(interimTranscript || transcript) && (
              <div className="voice-live-transcript">
                <span className="voice-transcript-text">
                  {interimTranscript || transcript}
                </span>
              </div>
            )}

            {/* Recording indicator */}
            <div className="voice-recording-indicator">
              <span className="voice-recording-dot" />
              <span className="voice-recording-label">Listening…</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error toast */}
      <AnimatePresence>
        {showError && errorMessage && (
          <motion.div
            className="voice-error-toast"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
          >
            ⚠️ {errorMessage}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
