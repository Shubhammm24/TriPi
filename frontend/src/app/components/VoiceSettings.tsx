"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  useVoiceSettings,
  SUPPORTED_LANGUAGES,
} from "@/app/hooks/useVoiceSettings";
import { useTTS } from "@/app/hooks/useTTS";

interface VoiceSettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function VoiceSettings({ isOpen, onClose }: VoiceSettingsProps) {
  const { settings, updateSettings, resetSettings, playChime } = useVoiceSettings();
  const [browserVoices, setBrowserVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [activeTab, setActiveTab] = useState<"tts" | "stt">("tts");

  const { speak, status, stop } = useTTS({
    rate: settings.ttsRate,
    pitch: settings.ttsPitch,
    voiceName: settings.ttsVoice,
    language: settings.sttLanguage,
  });

  // Load browser voices
  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    const loadVoices = () => {
      const v = window.speechSynthesis.getVoices();
      if (v && v.length > 0) {
        setBrowserVoices(v);
      }
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.onvoiceschanged = null;
      }
    };
  }, []);

  const handleTestVoice = () => {
    if (status === "speaking") {
      stop();
    } else {
      playChime("start");
      speak(
        "Welcome to TriPi! I'm your AI travel concierge. Where would you like to travel next?"
      );
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="voice-settings-backdrop" onClick={onClose}>
          <motion.div
            className="voice-settings-modal glass-card"
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 15 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            {/* Header */}
            <div className="voice-settings-header">
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 22 }}>🎙️</span>
                <div>
                  <h3
                    style={{
                      margin: 0,
                      fontFamily: "var(--font-headline)",
                      fontSize: 18,
                      fontWeight: 600,
                      color: "var(--on-surface)",
                    }}
                  >
                    Voice & Speech Settings
                  </h3>
                  <p
                    style={{
                      margin: 0,
                      fontSize: 12,
                      color: "var(--muted)",
                      fontFamily: "var(--font-body)",
                    }}
                  >
                    Customize your voice assistant & speech recognition
                  </p>
                </div>
              </div>

              <button
                className="voice-close-btn"
                onClick={onClose}
                aria-label="Close voice settings"
              >
                ✕
              </button>
            </div>

            {/* Navigation Tabs */}
            <div className="voice-settings-tabs">
              <button
                className={`voice-settings-tab ${
                  activeTab === "tts" ? "voice-settings-tab--active" : ""
                }`}
                onClick={() => setActiveTab("tts")}
              >
                🔊 Text-to-Speech (TTS)
              </button>
              <button
                className={`voice-settings-tab ${
                  activeTab === "stt" ? "voice-settings-tab--active" : ""
                }`}
                onClick={() => setActiveTab("stt")}
              >
                🎤 Speech-to-Text (STT)
              </button>
            </div>

            {/* Tab Body */}
            <div className="voice-settings-body">
              {activeTab === "tts" ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                  {/* Voice Selector */}
                  <div>
                    <label className="input-label" htmlFor="tts-voice-select">
                      Preferred Voice
                    </label>
                    <select
                      id="tts-voice-select"
                      className="input-field"
                      value={settings.ttsVoice}
                      onChange={(e) => updateSettings({ ttsVoice: e.target.value })}
                      style={{ cursor: "pointer" }}
                    >
                      <option value="">Default System Voice</option>
                      {browserVoices.map((voice) => (
                        <option key={voice.name + voice.lang} value={voice.name}>
                          {voice.name} ({voice.lang}) {voice.default ? "★" : ""}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Speech Rate Slider */}
                  <div>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: 6,
                      }}
                    >
                      <label className="input-label" style={{ margin: 0 }}>
                        Playback Speed
                      </label>
                      <span className="badge-pill">{settings.ttsRate}x</span>
                    </div>
                    <input
                      type="range"
                      min="0.75"
                      max="1.75"
                      step="0.05"
                      value={settings.ttsRate}
                      onChange={(e) =>
                        updateSettings({ ttsRate: parseFloat(e.target.value) })
                      }
                      style={{ width: "100%", accentColor: "var(--primary)" }}
                    />
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        fontSize: 11,
                        color: "var(--muted)",
                        marginTop: 2,
                      }}
                    >
                      <span>Slower (0.75x)</span>
                      <span>Normal (1.0x)</span>
                      <span>Faster (1.75x)</span>
                    </div>
                  </div>

                  {/* Speech Pitch Slider */}
                  <div>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: 6,
                      }}
                    >
                      <label className="input-label" style={{ margin: 0 }}>
                        Voice Pitch
                      </label>
                      <span className="badge-pill">{settings.ttsPitch.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min="0.8"
                      max="1.3"
                      step="0.05"
                      value={settings.ttsPitch}
                      onChange={(e) =>
                        updateSettings({ ttsPitch: parseFloat(e.target.value) })
                      }
                      style={{ width: "100%", accentColor: "var(--primary)" }}
                    />
                  </div>

                  {/* Auto-read toggle */}
                  <div className="voice-setting-toggle-row">
                    <div>
                      <div className="voice-toggle-label">Auto-read Concierge Responses</div>
                      <div className="voice-toggle-desc">
                        Automatically speak itinerary refinements & agent replies
                      </div>
                    </div>
                    <label className="voice-switch">
                      <input
                        type="checkbox"
                        checked={settings.autoReadChat}
                        onChange={(e) =>
                          updateSettings({ autoReadChat: e.target.checked })
                        }
                      />
                      <span className="voice-slider" />
                    </label>
                  </div>

                  {/* Test Speech Button */}
                  <div style={{ paddingTop: 6 }}>
                    <button
                      className="btn btn-secondary btn-full"
                      onClick={handleTestVoice}
                      style={{ gap: 8 }}
                    >
                      {status === "speaking" ? "⏹️ Stop Preview" : "🔊 Preview This Voice"}
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                  {/* Language Selector */}
                  <div>
                    <label className="input-label" htmlFor="stt-lang-select">
                      Speech Recognition Language
                    </label>
                    <select
                      id="stt-lang-select"
                      className="input-field"
                      value={settings.sttLanguage}
                      onChange={(e) =>
                        updateSettings({ sttLanguage: e.target.value })
                      }
                      style={{ cursor: "pointer" }}
                    >
                      {SUPPORTED_LANGUAGES.map((lang) => (
                        <option key={lang.code} value={lang.code}>
                          {lang.name} ({lang.code})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Sound feedback chime toggle */}
                  <div className="voice-setting-toggle-row">
                    <div>
                      <div className="voice-toggle-label">Audio Chimes & Cues</div>
                      <div className="voice-toggle-desc">
                        Play subtle audio cue when starting and stopping microphone
                      </div>
                    </div>
                    <label className="voice-switch">
                      <input
                        type="checkbox"
                        checked={settings.soundEffects}
                        onChange={(e) =>
                          updateSettings({ soundEffects: e.target.checked })
                        }
                      />
                      <span className="voice-slider" />
                    </label>
                  </div>

                  {/* Microphone tips */}
                  <div
                    style={{
                      background: "rgba(99, 102, 241, 0.08)",
                      border: "1px solid rgba(99, 102, 241, 0.2)",
                      borderRadius: "var(--radius-md)",
                      padding: 14,
                      fontSize: 13,
                      lineHeight: 1.5,
                      color: "var(--on-surface-variant)",
                    }}
                  >
                    <div style={{ fontWeight: 600, color: "var(--primary)", marginBottom: 4 }}>
                      💡 Voice Input Tips
                    </div>
                    • Speak clearly at normal volume into your microphone.
                    <br />
                    • Chrome, Edge, and Safari have native Web Speech API support.
                    <br />
                    • When speech stops, recognition automatically concludes.
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="voice-settings-footer">
              <button
                className="btn btn-ghost"
                onClick={resetSettings}
                style={{ fontSize: 13, color: "var(--muted)" }}
              >
                Reset to Defaults
              </button>

              <button className="btn btn-primary" onClick={onClose}>
                Done
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
