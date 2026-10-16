"use client";

import { useState, useEffect, useCallback } from "react";

/* ═══════════════════════════════════════════════════════════
   useVoiceSettings — Global Voice & Speech Configuration
   
   Manages user preferences for:
   - Text-to-Speech (TTS voice, rate, pitch, auto-read)
   - Speech-to-Text (STT language, push-to-talk)
   - Sound feedback chimes (Web Audio API synthesis)
   - LocalStorage persistence & cross-component sync
   ═══════════════════════════════════════════════════════════ */

export interface VoiceSettingsState {
  enabled: boolean;
  ttsVoice: string;
  ttsRate: number;
  ttsPitch: number;
  autoReadChat: boolean;
  sttLanguage: string;
  soundEffects: boolean;
}

export const DEFAULT_VOICE_SETTINGS: VoiceSettingsState = {
  enabled: true,
  ttsVoice: "",
  ttsRate: 1.0,
  ttsPitch: 1.0,
  autoReadChat: true,
  sttLanguage: "en-US",
  soundEffects: true,
};

const STORAGE_KEY = "tripi_voice_settings";
const SETTINGS_CHANGE_EVENT = "tripi_voice_settings_change";

export const SUPPORTED_LANGUAGES = [
  { code: "en-US", name: "English (US)" },
  { code: "en-GB", name: "English (UK)" },
  { code: "en-IN", name: "English (India)" },
  { code: "en-AU", name: "English (Australia)" },
  { code: "es-ES", name: "Español (España)" },
  { code: "es-MX", name: "Español (México)" },
  { code: "fr-FR", name: "Français (France)" },
  { code: "de-DE", name: "Deutsch" },
  { code: "it-IT", name: "Italiano" },
  { code: "ja-JP", name: "日本語 (Japanese)" },
  { code: "ko-KR", name: "한국어 (Korean)" },
  { code: "zh-CN", name: "中文 (Mandarin)" },
  { code: "hi-IN", name: "हिन्दी (Hindi)" },
  { code: "pt-BR", name: "Português (Brasil)" },
  { code: "ar-SA", name: "العربية (Arabic)" },
];

/**
 * Play subtle, elegant UI chimes using pure Web Audio oscillator synthesis.
 * Zero external audio files required.
 */
export function playVoiceChime(type: "start" | "stop" | "success" | "pop") {
  if (typeof window === "undefined") return;

  try {
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!AudioCtx) return;

    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;

    if (type === "start") {
      // Ascending pleasant major 3rd chime
      osc.type = "sine";
      osc.frequency.setValueAtTime(523.25, now); // C5
      osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.12); // E5
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.start(now);
      osc.stop(now + 0.24);
    } else if (type === "stop") {
      // Descending soft chime
      osc.type = "sine";
      osc.frequency.setValueAtTime(659.25, now); // E5
      osc.frequency.exponentialRampToValueAtTime(440.0, now + 0.14); // A4
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.start(now);
      osc.stop(now + 0.24);
    } else if (type === "success") {
      // Two-tone cheerful success
      osc.type = "triangle";
      osc.frequency.setValueAtTime(587.33, now); // D5
      osc.frequency.exponentialRampToValueAtTime(880.0, now + 0.16); // A5
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
      osc.start(now);
      osc.stop(now + 0.32);
    } else {
      // Short subtle pop
      osc.type = "sine";
      osc.frequency.setValueAtTime(800, now);
      gain.gain.setValueAtTime(0.04, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      osc.start(now);
      osc.stop(now + 0.09);
    }

    setTimeout(() => {
      ctx.close().catch(() => {});
    }, 400);
  } catch {
    // Ignore audio context errors if blocked by browser policy
  }
}

export function useVoiceSettings() {
  const [settings, setSettings] = useState<VoiceSettingsState>(DEFAULT_VOICE_SETTINGS);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setSettings({ ...DEFAULT_VOICE_SETTINGS, ...parsed });
      }
    } catch {
      // Fallback to defaults
    } finally {
      setIsLoaded(true);
    }

    const handleSync = (e: Event) => {
      const customEvent = e as CustomEvent<VoiceSettingsState>;
      if (customEvent.detail) {
        setSettings(customEvent.detail);
      }
    };

    window.addEventListener(SETTINGS_CHANGE_EVENT, handleSync);
    return () => window.removeEventListener(SETTINGS_CHANGE_EVENT, handleSync);
  }, []);

  // Update settings and broadcast
  const updateSettings = useCallback((updates: Partial<VoiceSettingsState>) => {
    setSettings((prev) => {
      const next = { ...prev, ...updates };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        window.dispatchEvent(
          new CustomEvent<VoiceSettingsState>(SETTINGS_CHANGE_EVENT, { detail: next })
        );
      } catch {
        // Storage quota / private mode fallback
      }
      return next;
    });
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_VOICE_SETTINGS);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_VOICE_SETTINGS));
      window.dispatchEvent(
        new CustomEvent<VoiceSettingsState>(SETTINGS_CHANGE_EVENT, { detail: DEFAULT_VOICE_SETTINGS })
      );
    } catch {
      // Fallback
    }
  }, []);

  return {
    settings,
    updateSettings,
    resetSettings,
    isLoaded,
    playChime: (type: "start" | "stop" | "success" | "pop") => {
      if (settings.soundEffects) {
        playVoiceChime(type);
      }
    },
  };
}
