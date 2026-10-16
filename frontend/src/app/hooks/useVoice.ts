"use client";

import { useState, useCallback, useRef, useEffect } from "react";

/* ═══════════════════════════════════════════════════════════
   useVoice — Speech-to-Text hook using the Web Speech API

   Why browser-native?
   - Zero cost (no API keys or billing)
   - Zero backend changes (runs entirely client-side)
   - Good quality for English; serviceable for 80+ languages
   - Graceful fallback: isSupported=false for Firefox
   ═══════════════════════════════════════════════════════════ */

export type VoiceStatus = "idle" | "listening" | "error";

interface UseVoiceOptions {
  /** Language BCP-47 code (e.g. "en-US", "hi-IN"). Defaults to browser locale. */
  language?: string;
  /** Continuous recognition (keeps listening after pauses). Default: true */
  continuous?: boolean;
  /** Show interim (in-progress) results. Default: true */
  interimResults?: boolean;
  /** Called with the final transcript when recognition ends or produces a final result */
  onResult?: (transcript: string) => void;
  /** Called with interim transcript as user speaks */
  onInterim?: (transcript: string) => void;
  /** Called when an error occurs */
  onError?: (error: string) => void;
}

interface UseVoiceReturn {
  /** Whether the browser supports SpeechRecognition */
  isSupported: boolean;
  /** Current recording status */
  status: VoiceStatus;
  /** The final recognized transcript */
  transcript: string;
  /** Interim (in-progress) transcript shown while user is speaking */
  interimTranscript: string;
  /** Start listening */
  startListening: () => void;
  /** Stop listening */
  stopListening: () => void;
  /** Toggle listening on/off */
  toggleListening: () => void;
  /** Clear the transcript */
  clearTranscript: () => void;
  /** Human-readable error message, if any */
  errorMessage: string;
}

/**
 * Get the SpeechRecognition constructor, accounting for vendor prefixes.
 * Returns null in environments where it's not available (Firefox, SSR).
 */
function getSpeechRecognition(): SpeechRecognitionConstructor | null {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}


export function useVoice(options: UseVoiceOptions = {}): UseVoiceReturn {
  const {
    language,
    continuous = true,
    interimResults = true,
    onResult,
    onInterim,
    onError,
  } = options;

  const SpeechRecognitionCtor = getSpeechRecognition();
  const isSupported = SpeechRecognitionCtor !== null;

  const [status, setStatus] = useState<VoiceStatus>("idle");
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  // Track whether user explicitly requested stop (vs browser auto-stop)
  const manualStopRef = useRef(false);

  // Keep callback refs fresh without re-creating recognition
  const onResultRef = useRef(onResult);
  const onInterimRef = useRef(onInterim);
  const onErrorRef = useRef(onError);
  useEffect(() => {
    onResultRef.current = onResult;
    onInterimRef.current = onInterim;
    onErrorRef.current = onError;
  }, [onResult, onInterim, onError]);

  const startListening = useCallback(() => {
    if (!SpeechRecognitionCtor) {
      const msg = "Speech recognition is not supported in this browser. Try Chrome or Edge.";
      setErrorMessage(msg);
      setStatus("error");
      onErrorRef.current?.(msg);
      return;
    }

    // Tear down any existing instance
    if (recognitionRef.current) {
      recognitionRef.current.abort();
      recognitionRef.current = null;
    }

    manualStopRef.current = false;
    setErrorMessage("");
    setInterimTranscript("");

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = language || navigator.language || "en-US";
    recognition.continuous = continuous;
    recognition.interimResults = interimResults;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setStatus("listening");
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalText = "";
      let interimText = "";

      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalText += result[0].transcript;
        } else {
          interimText += result[0].transcript;
        }
      }

      if (interimText) {
        setInterimTranscript(interimText);
        onInterimRef.current?.(interimText);
      }

      if (finalText) {
        setTranscript(finalText);
        setInterimTranscript("");
        onResultRef.current?.(finalText);
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      // "aborted" fires when we call .abort() — not a real error
      if (event.error === "aborted") return;

      const messages: Record<string, string> = {
        "not-allowed": "Microphone access was denied. Please allow microphone permissions.",
        "no-speech": "No speech detected. Please try again.",
        "audio-capture": "No microphone found. Please connect a microphone.",
        "network": "Network error occurred. Check your connection.",
      };

      const msg = messages[event.error] || `Speech recognition error: ${event.error}`;
      setErrorMessage(msg);
      setStatus("error");
      onErrorRef.current?.(msg);
    };

    recognition.onend = () => {
      // If user didn't manually stop and we're in continuous mode,
      // the browser may auto-stop — restart automatically
      if (!manualStopRef.current && continuous) {
        try {
          recognition.start();
          return;
        } catch {
          // Already running or disposed — fall through
        }
      }
      setStatus("idle");
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch {
      setErrorMessage("Failed to start speech recognition.");
      setStatus("error");
    }
  }, [SpeechRecognitionCtor, language, continuous, interimResults]);

  const stopListening = useCallback(() => {
    manualStopRef.current = true;
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setStatus("idle");
    setInterimTranscript("");
  }, []);

  const toggleListening = useCallback(() => {
    if (status === "listening") {
      stopListening();
    } else {
      startListening();
    }
  }, [status, startListening, stopListening]);

  const clearTranscript = useCallback(() => {
    setTranscript("");
    setInterimTranscript("");
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        manualStopRef.current = true;
        recognitionRef.current.abort();
        recognitionRef.current = null;
      }
    };
  }, []);

  return {
    isSupported,
    status,
    transcript,
    interimTranscript,
    startListening,
    stopListening,
    toggleListening,
    clearTranscript,
    errorMessage,
  };
}
