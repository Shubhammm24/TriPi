"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useVoice } from "@/app/hooks/useVoice";
import { useTTS } from "@/app/hooks/useTTS";
import { useVoiceSettings } from "@/app/hooks/useVoiceSettings";
import VoiceSettings from "@/app/components/VoiceSettings";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  id: string;
  sender: "user" | "concierge";
  text: string;
  timestamp: string;
}

interface VoiceChatPanelProps {
  sessionId?: string;
  destination?: string;
  itinerary?: string;
  onItineraryUpdated?: (newItinerary: string) => void;
}

export default function VoiceChatPanel({
  sessionId,
  destination,
  itinerary,
  onItineraryUpdated,
}: VoiceChatPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const { settings, playChime } = useVoiceSettings();

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "concierge",
      text: destination
        ? `Hi! I'm your TriPi Voice Concierge for ${destination}. You can tap the mic to ask me questions, adjust your schedule, or ask for local recommendations!`
        : "Hi! I'm your TriPi Voice Concierge. Ask me anything about planning your dream trip, finding hidden spots, or optimizing your travel budget!",
      timestamp: "Just now",
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // Text to Speech
  const {
    speak,
    stop: stopTTS,
    status: ttsStatus,
  } = useTTS({
    rate: settings.ttsRate,
    pitch: settings.ttsPitch,
    voiceName: settings.ttsVoice,
    language: settings.sttLanguage,
  });

  const isSpeaking = ttsStatus === "speaking";

  // Auto scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  // Handle agent conversation request
  const handleSendMessage = useCallback(
    async (messageText: string) => {
      const trimmed = messageText.trim();
      if (!trimmed || isProcessing) return;

      stopTTS();
      const userMsg: Message = {
        id: `user-${Date.now()}`,
        sender: "user",
        text: trimmed,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, userMsg]);
      setTextInput("");
      setIsProcessing(true);

      try {
        const validSessionId =
          sessionId &&
          /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(sessionId)
            ? sessionId
            : undefined;

        const isRefineRequest =
          /change|swap|replace|modify|update|more|less|add|remove|budget/i.test(trimmed) &&
          !!validSessionId &&
          !!itinerary;

        const endpoint = isRefineRequest ? `${API_URL}/api/refine` : `${API_URL}/api/chat`;
        const body: Record<string, string> = isRefineRequest && validSessionId
          ? { session_id: validSessionId, feedback: trimmed }
          : validSessionId
          ? { session_id: validSessionId, message: trimmed }
          : { message: trimmed };

        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          throw new Error("Unable to reach TriPi agent service.");
        }

        const data = await res.json();

        // Django returns task ID for background Celery processing or direct reply
        let replyText = "";

        if (data.task_id) {
          // Poll for task completion
          const POLL_INTERVAL = 1500;
          const MAX_POLLS = 40;
          let polls = 0;

          while (polls < MAX_POLLS) {
            await new Promise((r) => setTimeout(r, POLL_INTERVAL));
            polls++;

            try {
              const pollRes = await fetch(`${API_URL}/api/tasks/${data.task_id}/`);
              if (!pollRes.ok) continue;
              const taskData = await pollRes.json();

              if (taskData.status === "completed" && taskData.result) {
                if (isRefineRequest && taskData.result.itinerary) {
                  onItineraryUpdated?.(taskData.result.itinerary);
                  replyText =
                    "I've updated your itinerary based on your request! Check out the itinerary tab to see the latest schedule.";
                } else {
                  replyText =
                    taskData.result.reply ||
                    taskData.result.itinerary ||
                    taskData.result.message ||
                    "I've processed your travel request!";
                }
                break;
              } else if (taskData.status === "failed") {
                replyText = `Sorry, I encountered an issue: ${taskData.error || "Unknown error"}`;
                break;
              }
            } catch {
              // Retry next poll
            }
          }

          if (!replyText) {
            replyText = "I'm still organizing the travel details. Please check the itinerary in a moment!";
          }
        } else {
          replyText =
            data.reply ||
            data.message ||
            data.itinerary ||
            "Here's what I recommend for your journey!";
        }

        const conciergeMsg: Message = {
          id: `concierge-${Date.now()}`,
          sender: "concierge",
          text: replyText,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };

        setMessages((prev) => [...prev, conciergeMsg]);

        // Automatically speak response if enabled
        if (settings.autoReadChat) {
          speak(replyText);
        }
      } catch (err: unknown) {
        const errorMsg =
          err instanceof Error
            ? err.message
            : "Trouble connecting to the travel concierge. Please try again.";

        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            sender: "concierge",
            text: `⚠️ ${errorMsg}`,
            timestamp: "Now",
          },
        ]);
      } finally {
        setIsProcessing(false);
      }
    },
    [isProcessing, sessionId, itinerary, onItineraryUpdated, settings.autoReadChat, speak, stopTTS]
  );

  // Speech to Text hook
  const {
    isSupported,
    status: sttStatus,
    interimTranscript,
    startListening,
    stopListening,
    errorMessage,
  } = useVoice({
    language: settings.sttLanguage,
    continuous: false,
    onResult: (transcript) => {
      playChime("stop");
      if (transcript.trim()) {
        handleSendMessage(transcript);
      }
    },
    onError: () => {
      playChime("pop");
    },
  });

  const isListening = sttStatus === "listening";

  // Mic toggle handler
  const toggleMic = () => {
    if (isListening) {
      playChime("stop");
      stopListening();
    } else {
      stopTTS();
      playChime("start");
      startListening();
    }
  };

  // Dynamic visualizer canvas when listening or speaking
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let angle = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const height = canvas.height;
      const centerY = height / 2;

      if (isListening || isSpeaking || isProcessing) {
        ctx.beginPath();
        const bars = 24;
        const barWidth = 3;
        const spacing = (width - bars * barWidth) / (bars + 1);

        for (let i = 0; i < bars; i++) {
          const x = spacing + i * (barWidth + spacing);
          const freq = Math.sin(angle + i * 0.45) * 0.5 + 0.5;
          const barHeight = Math.max(4, freq * (height * 0.75));

          const grad = ctx.createLinearGradient(0, centerY - barHeight / 2, 0, centerY + barHeight / 2);
          if (isListening) {
            grad.addColorStop(0, "#FF6E84");
            grad.addColorStop(1, "#FF9BB0");
          } else if (isSpeaking) {
            grad.addColorStop(0, "#00E5FF");
            grad.addColorStop(1, "#6366F1");
          } else {
            grad.addColorStop(0, "#A855F7");
            grad.addColorStop(1, "#6366F1");
          }

          ctx.fillStyle = grad;
          ctx.beginPath();
          if (typeof ctx.roundRect === "function") {
            ctx.roundRect(x, centerY - barHeight / 2, barWidth, barHeight, 2);
          } else {
            ctx.rect(x, centerY - barHeight / 2, barWidth, barHeight);
          }
          ctx.fill();
        }

        angle += isListening ? 0.18 : 0.12;
      } else {
        // Idle gentle horizon line
        ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, centerY);
        ctx.lineTo(width, centerY);
        ctx.stroke();
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isListening, isSpeaking, isProcessing]);

  // Suggested prompts
  const suggestedPrompts = [
    "Recommend 3 hidden cafes",
    "Swap Day 2 lunch with seafood",
    "Best evening walks nearby",
    "How should I dress for the weather?",
  ];

  return (
    <>
      {/* Floating Concierge Launcher Pill */}
      <motion.button
        className="voice-concierge-pill"
        onClick={() => setIsOpen(true)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        aria-label="Open Voice Concierge"
      >
        <span className="voice-concierge-pill-glow" />
        <span className="voice-concierge-pill-icon">🎙️</span>
        <span className="voice-concierge-pill-label">Voice Concierge</span>
        {isSpeaking && <span className="voice-concierge-speaking-dot" />}
      </motion.button>

      {/* Main Voice Concierge Sheet / Modal */}
      <AnimatePresence>
        {isOpen && (
          <div className="voice-chat-backdrop" onClick={() => setIsOpen(false)}>
            <motion.div
              className="voice-chat-panel glass-card"
              initial={{ opacity: 0, y: 40, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 40, scale: 0.96 }}
              transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="voice-chat-header">
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div className="voice-avatar-orb">
                    <span style={{ fontSize: 18 }}>✨</span>
                    <span
                      className={`voice-orb-glow ${
                        isListening
                          ? "voice-orb-glow--listening"
                          : isSpeaking
                          ? "voice-orb-glow--speaking"
                          : isProcessing
                          ? "voice-orb-glow--thinking"
                          : ""
                      }`}
                    />
                  </div>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <h4
                        style={{
                          margin: 0,
                          fontFamily: "var(--font-headline)",
                          fontSize: 16,
                          fontWeight: 600,
                          color: "var(--on-surface)",
                        }}
                      >
                        TriPi Voice Concierge
                      </h4>
                      <span className="voice-status-badge">
                        {isListening
                          ? "🔴 Listening..."
                          : isProcessing
                          ? "⚡ Thinking..."
                          : isSpeaking
                          ? "🔊 Speaking..."
                          : "Online"}
                      </span>
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        color: "var(--muted)",
                        fontFamily: "var(--font-body)",
                      }}
                    >
                      {destination ? `Tailored for ${destination}` : "Hands-free travel planning"}
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <button
                    className="voice-player-btn"
                    onClick={() => setIsSettingsOpen(true)}
                    title="Voice Settings"
                    aria-label="Open voice settings"
                  >
                    ⚙️
                  </button>

                  {isSpeaking && (
                    <button
                      className="voice-player-btn"
                      onClick={stopTTS}
                      title="Stop speaking"
                      aria-label="Stop audio playback"
                    >
                      ⏹️
                    </button>
                  )}

                  <button
                    className="voice-player-btn"
                    onClick={() => setIsOpen(false)}
                    aria-label="Close concierge"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Visualizer Waveform Bar */}
              <div className="voice-chat-waveform-container">
                <canvas
                  ref={canvasRef}
                  width={380}
                  height={32}
                  className="voice-chat-waveform-canvas"
                />
              </div>

              {/* Message Transcript Stream */}
              <div className="voice-chat-messages">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`voice-bubble-row ${
                      msg.sender === "user"
                        ? "voice-bubble-row--user"
                        : "voice-bubble-row--concierge"
                    }`}
                  >
                    {msg.sender === "concierge" && (
                      <div className="voice-bubble-avatar">🤖</div>
                    )}
                    <div
                      className={`voice-chat-bubble ${
                        msg.sender === "user"
                          ? "voice-chat-bubble--user"
                          : "voice-chat-bubble--concierge"
                      }`}
                    >
                      <div className="voice-bubble-text">{msg.text}</div>
                      <div className="voice-bubble-meta">
                        <span>{msg.timestamp}</span>
                        {msg.sender === "concierge" && (
                          <button
                            className="voice-bubble-speak-btn"
                            onClick={() => speak(msg.text)}
                            title="Listen to this message"
                          >
                            🔊 Listen
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Interim Live Speech Stream */}
                {isListening && interimTranscript && (
                  <div className="voice-bubble-row voice-bubble-row--user">
                    <div className="voice-chat-bubble voice-chat-bubble--user voice-chat-bubble--interim">
                      <div className="voice-bubble-text">
                        {interimTranscript}
                        <span className="voice-blinking-cursor">|</span>
                      </div>
                      <div className="voice-bubble-meta">Listening live…</div>
                    </div>
                  </div>
                )}

                {/* Thinking / Processing skeleton */}
                {isProcessing && (
                  <div className="voice-bubble-row voice-bubble-row--concierge">
                    <div className="voice-bubble-avatar">🤖</div>
                    <div className="voice-chat-bubble voice-chat-bubble--concierge">
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div className="voice-typing-dots">
                          <span />
                          <span />
                          <span />
                        </div>
                        <span style={{ fontSize: 12, color: "var(--muted)" }}>
                          Consulting travel databases…
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Quick Prompts Chips */}
              <div className="voice-quick-chips">
                {suggestedPrompts.map((p, idx) => (
                  <button
                    key={idx}
                    className="voice-quick-chip"
                    onClick={() => handleSendMessage(p)}
                    disabled={isProcessing}
                  >
                    💬 {p}
                  </button>
                ))}
              </div>

              {/* Error Alert */}
              {errorMessage && (
                <div className="voice-chat-error-bar">
                  <span>⚠️ {errorMessage}</span>
                </div>
              )}

              {/* Bottom Input Area */}
              <div className="voice-chat-footer">
                {/* Main Mic Button */}
                <div style={{ display: "flex", justifyContent: "center", marginBottom: 12 }}>
                  <button
                    className={`voice-hero-mic-btn ${
                      isListening ? "voice-hero-mic-btn--active" : ""
                    }`}
                    onClick={toggleMic}
                    disabled={!isSupported}
                    title={
                      !isSupported
                        ? "Voice recognition requires Chrome, Edge or Safari"
                        : isListening
                        ? "Tap to send speech"
                        : "Tap to talk with Concierge"
                    }
                  >
                    <span className="voice-hero-mic-icon">
                      {isListening ? "🛑" : "🎙️"}
                    </span>
                    <span className="voice-hero-mic-text">
                      {isListening ? "Tap when Done" : "Tap to Speak"}
                    </span>
                    {isListening && <span className="voice-pulse-ring" />}
                  </button>
                </div>

                {/* Optional Text Input fallback */}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage(textInput);
                  }}
                  style={{ display: "flex", gap: 8 }}
                >
                  <input
                    type="text"
                    className="input-field"
                    placeholder="Or type a question or change..."
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    disabled={isProcessing}
                    style={{ fontSize: 13 }}
                  />
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!textInput.trim() || isProcessing}
                    style={{ padding: "0 18px", flexShrink: 0 }}
                  >
                    Send
                  </button>
                </form>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Voice Settings Modal */}
      <VoiceSettings
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </>
  );
}
