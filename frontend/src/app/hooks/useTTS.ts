"use client";

import { useState, useCallback, useRef, useEffect } from "react";

/* ═══════════════════════════════════════════════════════════
   useTTS — Text-to-Speech hook using the Web Speech API

   Features:
   - Queue-based playback (speaks chunks sequentially)
   - Play / Pause / Stop / Skip controls
   - Speed & pitch adjustment
   - Voice selection from browser's available voices
   - Word boundary events for text highlighting
   - Strips markdown before speaking
   ═══════════════════════════════════════════════════════════ */

export type TTSStatus = "idle" | "speaking" | "paused";

interface UseTTSOptions {
  /** Playback rate (0.5 – 2.0). Default: 1.0 */
  rate?: number;
  /** Pitch (0.5 – 2.0). Default: 1.0 */
  pitch?: number;
  /** Preferred voice name. If not found, uses browser default. */
  voiceName?: string;
  /** Language BCP-47. Default: "en-US" */
  language?: string;
  /** Called when a chunk starts speaking */
  onStart?: () => void;
  /** Called when all speech finishes */
  onEnd?: () => void;
  /** Called with the char index boundary (for highlighting) */
  onBoundary?: (charIndex: number) => void;
}

interface UseTTSReturn {
  /** Whether the browser supports SpeechSynthesis */
  isSupported: boolean;
  /** Current playback status */
  status: TTSStatus;
  /** Available voices in the browser */
  voices: SpeechSynthesisVoice[];
  /** Speak a string (adds to queue if already speaking) */
  speak: (text: string) => void;
  /** Speak markdown content (strips formatting first) */
  speakMarkdown: (markdown: string) => void;
  /** Pause playback */
  pause: () => void;
  /** Resume playback */
  resume: () => void;
  /** Stop all speech and clear the queue */
  stop: () => void;
  /** Toggle between speaking and paused */
  togglePause: () => void;
  /** Currently speaking text chunk */
  currentText: string;
}

/**
 * Strip markdown syntax to produce clean spoken text.
 * Removes headers (#), bold (**), italic (*), links, images, code blocks, etc.
 */
function stripMarkdown(md: string): string {
  return md
    // Remove code blocks
    .replace(/```[\s\S]*?```/g, "")
    // Remove inline code
    .replace(/`([^`]+)`/g, "$1")
    // Remove images
    .replace(/!\[.*?\]\(.*?\)/g, "")
    // Remove links but keep text
    .replace(/\[([^\]]+)\]\(.*?\)/g, "$1")
    // Remove headers
    .replace(/^#{1,6}\s+/gm, "")
    // Remove bold/italic markers
    .replace(/\*{1,3}(.*?)\*{1,3}/g, "$1")
    .replace(/_{1,3}(.*?)_{1,3}/g, "$1")
    // Remove strikethrough
    .replace(/~~(.*?)~~/g, "$1")
    // Remove horizontal rules
    .replace(/^[-*_]{3,}$/gm, "")
    // Remove blockquotes
    .replace(/^>\s+/gm, "")
    // Remove list markers
    .replace(/^[\s]*[-*+]\s+/gm, "")
    .replace(/^[\s]*\d+\.\s+/gm, "")
    // Remove HTML tags
    .replace(/<[^>]+>/g, "")
    // Collapse multiple newlines
    .replace(/\n{3,}/g, "\n\n")
    // Trim
    .trim();
}

/**
 * Split text into chunks suitable for SpeechSynthesis.
 * The browser API can choke on very long utterances, so we split
 * at paragraph boundaries (double newline) or at ~200 chars.
 */
function splitIntoChunks(text: string, maxLen = 200): string[] {
  // First split by paragraphs
  const paragraphs = text.split(/\n\n+/).filter((p) => p.trim().length > 0);
  const chunks: string[] = [];

  for (const para of paragraphs) {
    if (para.length <= maxLen) {
      chunks.push(para.trim());
    } else {
      // Split long paragraphs at sentence boundaries
      const sentences = para.match(/[^.!?]+[.!?]+/g) || [para];
      let current = "";

      for (const sentence of sentences) {
        if ((current + sentence).length > maxLen && current.length > 0) {
          chunks.push(current.trim());
          current = sentence;
        } else {
          current += sentence;
        }
      }
      if (current.trim()) {
        chunks.push(current.trim());
      }
    }
  }

  return chunks;
}

export function useTTS(options: UseTTSOptions = {}): UseTTSReturn {
  const {
    rate = 1.0,
    pitch = 1.0,
    voiceName,
    language = "en-US",
    onStart,
    onEnd,
    onBoundary,
  } = options;

  const isSupported = typeof window !== "undefined" && "speechSynthesis" in window;

  const [status, setStatus] = useState<TTSStatus>("idle");
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [currentText, setCurrentText] = useState("");

  const queueRef = useRef<string[]>([]);
  const isSpeakingRef = useRef(false);

  // Keep callback refs fresh
  const onStartRef = useRef(onStart);
  const onEndRef = useRef(onEnd);
  const onBoundaryRef = useRef(onBoundary);
  useEffect(() => {
    onStartRef.current = onStart;
    onEndRef.current = onEnd;
    onBoundaryRef.current = onBoundary;
  }, [onStart, onEnd, onBoundary]);

  // Load available voices (they load asynchronously in some browsers)
  useEffect(() => {
    if (!isSupported) return;

    const loadVoices = () => {
      const available = window.speechSynthesis.getVoices();
      if (available.length > 0) {
        setVoices(available);
      }
    };

    loadVoices();
    window.speechSynthesis.addEventListener("voiceschanged", loadVoices);
    return () => {
      window.speechSynthesis.removeEventListener("voiceschanged", loadVoices);
    };
  }, [isSupported]);

  /**
   * Find the best matching voice. Priority:
   * 1. Exact voiceName match
   * 2. A "natural" or "enhanced" voice in the target language
   * 3. Any voice matching the language
   * 4. Browser default
   */
  const findVoice = useCallback((): SpeechSynthesisVoice | null => {
    if (voices.length === 0) return null;

    // Exact name match
    if (voiceName) {
      const exact = voices.find((v) => v.name === voiceName);
      if (exact) return exact;
    }

    // Prefer "natural" or "premium" voices in the target language
    const langVoices = voices.filter((v) => v.lang.startsWith(language.split("-")[0]));
    const premium = langVoices.find(
      (v) =>
        v.name.toLowerCase().includes("natural") ||
        v.name.toLowerCase().includes("neural") ||
        v.name.toLowerCase().includes("enhanced")
    );
    if (premium) return premium;

    // Any voice in the language
    if (langVoices.length > 0) return langVoices[0];

    // Browser default
    return null;
  }, [voices, voiceName, language]);

  /** Speak the next chunk from the queue */
  const speakNext = useCallback(() => {
    if (!isSupported) return;
    if (queueRef.current.length === 0) {
      isSpeakingRef.current = false;
      setStatus("idle");
      setCurrentText("");
      onEndRef.current?.();
      return;
    }

    const text = queueRef.current.shift()!;
    setCurrentText(text);

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = rate;
    utterance.pitch = pitch;

    const voice = findVoice();
    if (voice) utterance.voice = voice;
    utterance.lang = language;

    utterance.onstart = () => {
      setStatus("speaking");
      isSpeakingRef.current = true;
    };

    utterance.onend = () => {
      // Speak next chunk in queue
      speakNext();
    };

    utterance.onerror = (e) => {
      if (e.error === "canceled" || e.error === "interrupted") return;
      console.warn("TTS error:", e.error);
      speakNext(); // Skip to next chunk on error
    };

    utterance.onboundary = (e) => {
      if (e.name === "word") {
        onBoundaryRef.current?.(e.charIndex);
      }
    };

    window.speechSynthesis.speak(utterance);
  }, [isSupported, rate, pitch, findVoice, language]);

  const speak = useCallback(
    (text: string) => {
      if (!isSupported || !text.trim()) return;

      const chunks = splitIntoChunks(text);
      queueRef.current.push(...chunks);

      onStartRef.current?.();

      if (!isSpeakingRef.current) {
        speakNext();
      }
    },
    [isSupported, speakNext]
  );

  const speakMarkdown = useCallback(
    (markdown: string) => {
      speak(stripMarkdown(markdown));
    },
    [speak]
  );

  const pause = useCallback(() => {
    if (!isSupported) return;
    window.speechSynthesis.pause();
    setStatus("paused");
  }, [isSupported]);

  const resume = useCallback(() => {
    if (!isSupported) return;
    window.speechSynthesis.resume();
    setStatus("speaking");
  }, [isSupported]);

  const stop = useCallback(() => {
    if (!isSupported) return;
    queueRef.current = [];
    window.speechSynthesis.cancel();
    isSpeakingRef.current = false;
    setStatus("idle");
    setCurrentText("");
  }, [isSupported]);

  const togglePause = useCallback(() => {
    if (status === "speaking") {
      pause();
    } else if (status === "paused") {
      resume();
    }
  }, [status, pause, resume]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isSupported) {
        window.speechSynthesis.cancel();
      }
    };
  }, [isSupported]);

  return {
    isSupported,
    status,
    voices,
    speak,
    speakMarkdown,
    pause,
    resume,
    stop,
    togglePause,
    currentText,
  };
}
