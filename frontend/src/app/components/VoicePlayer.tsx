"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTTS, TTSStatus } from "@/app/hooks/useTTS";
import { useVoiceSettings } from "@/app/hooks/useVoiceSettings";
import VoiceSettings from "@/app/components/VoiceSettings";

/* ═══════════════════════════════════════════════════════════
   VoicePlayer — TTS playback control bar for itineraries

   Shows a floating control bar when the user clicks "Read Aloud":
   - Play / Pause / Stop
   - Speed selector (0.75x, 1x, 1.25x, 1.5x)
   - Currently speaking text preview
   - Progress indication
   ═══════════════════════════════════════════════════════════ */

interface VoicePlayerProps {
  /** The markdown itinerary text to read */
  markdown: string;
  /** Optional: compact inline button mode (just a small 🔊 icon) */
  inline?: boolean;
}

const SPEED_OPTIONS = [0.75, 1, 1.25, 1.5];

export default function VoicePlayer({ markdown, inline = false }: VoicePlayerProps) {
  const { settings } = useVoiceSettings();
  const [selectedSpeed, setSelectedSpeed] = useState(settings.ttsRate || 1);
  const [showControls, setShowControls] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const {
    isSupported,
    status,
    speakMarkdown,
    pause,
    resume,
    stop,
    togglePause,
    currentText,
  } = useTTS({
    rate: selectedSpeed,
    pitch: settings.ttsPitch,
    voiceName: settings.ttsVoice,
    language: settings.sttLanguage,
    onStart: () => setShowControls(true),
    onEnd: () => setShowControls(false),
  });

  const handlePlay = useCallback(() => {
    if (status === "idle") {
      speakMarkdown(markdown);
    } else if (status === "paused") {
      resume();
    } else {
      pause();
    }
  }, [status, speakMarkdown, markdown, resume, pause]);

  const handleStop = useCallback(() => {
    stop();
    setShowControls(false);
  }, [stop]);

  const handleSpeedChange = useCallback(
    (speed: number) => {
      setSelectedSpeed(speed);
      // If currently speaking, restart with new speed
      if (status === "speaking" || status === "paused") {
        stop();
        // Small delay to let the synth clear, then restart
        setTimeout(() => speakMarkdown(markdown), 100);
      }
    },
    [status, stop, speakMarkdown, markdown]
  );

  if (!isSupported) return null;

  // Compact inline button mode — just a small icon
  if (inline) {
    return (
      <motion.button
        type="button"
        className="voice-inline-btn"
        onClick={handlePlay}
        whileTap={{ scale: 0.9 }}
        title={status === "speaking" ? "Pause" : "Read aloud"}
        aria-label={status === "speaking" ? "Pause reading" : "Read this section aloud"}
      >
        {status === "speaking" ? "⏸️" : "🔊"}
      </motion.button>
    );
  }

  const isSpeaking = status === "speaking";
  const isPaused = status === "paused";
  const isActive = isSpeaking || isPaused;

  return (
    <>
      {/* Trigger button */}
      <button
        className="btn btn-secondary btn-full"
        onClick={handlePlay}
        style={{ gap: 8 }}
      >
        {isSpeaking ? "⏸️ Pause" : isPaused ? "▶️ Resume" : "🔊 Read Aloud"}
      </button>

      {/* Floating control bar */}
      <AnimatePresence>
        {(isActive || showControls) && (
          <motion.div
            className="voice-player-bar"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
          >
            {/* Left: Playback controls */}
            <div className="voice-player-controls">
              <motion.button
                className="voice-player-btn voice-player-btn--primary"
                onClick={handlePlay}
                whileTap={{ scale: 0.9 }}
                title={isSpeaking ? "Pause" : "Play"}
              >
                {isSpeaking ? "⏸" : "▶"}
              </motion.button>

              <motion.button
                className="voice-player-btn"
                onClick={handleStop}
                whileTap={{ scale: 0.9 }}
                title="Stop"
              >
                ⏹
              </motion.button>
            </div>

            {/* Center: Currently speaking text */}
            <div className="voice-player-text">
              {isSpeaking && (
                <motion.div
                  className="voice-player-equalizer"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  {[...Array(4)].map((_, i) => (
                    <motion.span
                      key={i}
                      className="voice-eq-bar"
                      animate={{
                        scaleY: [0.3, 1, 0.3],
                      }}
                      transition={{
                        repeat: Infinity,
                        duration: 0.6,
                        delay: i * 0.1,
                        ease: "easeInOut",
                      }}
                    />
                  ))}
                </motion.div>
              )}
              <span className="voice-player-current">
                {currentText
                  ? currentText.substring(0, 60) + (currentText.length > 60 ? "…" : "")
                  : isPaused
                    ? "Paused"
                    : "Reading itinerary…"}
              </span>
            </div>

            {/* Right: Speed selector & settings */}
            <div className="voice-player-speed">
              {SPEED_OPTIONS.map((speed) => (
                <button
                  key={speed}
                  className={`voice-speed-chip ${selectedSpeed === speed ? "voice-speed-chip--active" : ""}`}
                  onClick={() => handleSpeedChange(speed)}
                >
                  {speed}x
                </button>
              ))}

              <button
                className="voice-player-btn"
                style={{ width: 28, height: 28, fontSize: 13, marginLeft: 4 }}
                onClick={() => setIsSettingsOpen(true)}
                title="Voice Settings"
              >
                ⚙️
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <VoiceSettings
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </>
  );
}
