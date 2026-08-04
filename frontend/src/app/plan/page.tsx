"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "@/app/components/Navbar";
import ReactMarkdown from "react-markdown";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
};

const interestOptions = [
  "History & Culture", "Food & Dining", "Nature & Outdoors", "Shopping",
  "Art & Museums", "Nightlife", "Adventure Sports", "Wellness & Spa",
  "Photography", "Local Experiences",
];

const dietaryOptions = ["Vegetarian", "Vegan", "Halal", "Kosher", "Gluten-free"];

const cuisineOptions = ["Local", "Italian", "Japanese", "Indian", "Thai", "French", "Mediterranean", "Mexican"];

const purposeOptions = ["Leisure", "Business", "Adventure", "Cultural", "Relaxation"];

const accommodationOptions = ["Budget", "Mid-range", "Luxury", "Boutique", "Apartment/Airbnb"];

interface FormData {
  destination: string;
  origin: string;
  startDate: string;
  endDate: string;
  budget: string;
  purpose: string;
  interests: string[];
  dietary: string[];
  cuisines: string[];
  mobility: string;
  walkingHours: number;
  accommodation: string;
  hiddenGems: boolean;
}

type Stage = "form" | "loading" | "result";

export default function PlanPage() {
  const [stage, setStage] = useState<Stage>("form");
  const [sessionId, setSessionId] = useState<string>("");
  const [itinerary, setItinerary] = useState<string>("");
  const [toolCalls, setToolCalls] = useState<string[]>([]);
  const [feedback, setFeedback] = useState("");
  const [refining, setRefining] = useState(false);
  const [loadingTools, setLoadingTools] = useState<string[]>([]);

  const [form, setForm] = useState<FormData>({
    destination: "",
    origin: "",
    startDate: "",
    endDate: "",
    budget: "",
    purpose: "Leisure",
    interests: [],
    dietary: [],
    cuisines: [],
    mobility: "No special requirements",
    walkingHours: 4,
    accommodation: "Mid-range",
    hiddenGems: false,
  });

  const toggleChip = (arr: string[], val: string): string[] =>
    arr.includes(val) ? arr.filter((v) => v !== val) : [...arr, val];

  const handleSubmit = async () => {
    if (!form.destination || !form.origin || !form.startDate || !form.endDate || !form.budget) return;

    setStage("loading");
    setLoadingTools(["🌤️ Checking weather…", "🌍 Looking up destination…"]);

    const timer1 = setTimeout(() => setLoadingTools(t => [...t, "📍 Finding attractions…"]), 2000);
    const timer2 = setTimeout(() => setLoadingTools(t => [...t, "💰 Converting currency…"]), 3500);
    const timer3 = setTimeout(() => setLoadingTools(t => [...t, "🔍 Searching the web…"]), 5000);
    const timer4 = setTimeout(() => setLoadingTools(t => [...t, "📚 Checking knowledge base…"]), 6500);

    try {
      const res = await fetch(`${API_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          destination: form.destination,
          origin: form.origin,
          start_date: form.startDate,
          end_date: form.endDate,
          budget: form.budget,
          duration: Math.max(1, Math.round(
            (new Date(form.endDate).getTime() - new Date(form.startDate).getTime()) / 86400000
          )),
          purpose: form.purpose,
          interests: form.interests,
          dietary_preferences: form.dietary,
          mobility_requirements: form.mobility,
          accommodation_type: form.accommodation,
          walking_tolerance: `${form.walkingHours} hours`,
          hidden_gems_preference: form.hiddenGems,
          cuisine_preferences: form.cuisines,
        }),
      });

      if (!res.ok) {
        const errText = await res.text();
        setItinerary(`## ⚠️ Backend Error (${res.status})\n\n${errText}\n\nMake sure the FastAPI server is running:\n\`\`\`\nuvicorn main:app --reload --port 8000\n\`\`\``);
        setStage("result");
        return;
      }

      const data = await res.json();
      setSessionId(data.session_id || "");
      setItinerary(data.itinerary || "No itinerary was generated. Please try again.");
      setToolCalls(data.tool_calls || []);
      setStage("result");
    } catch (err) {
      setItinerary(`## ⚠️ Connection Error\n\nCould not connect to the backend at \`${API_URL}\`.\n\nMake sure the FastAPI server is running:\n\`\`\`\ncd d:\\Projects\\Travel_Agent-main\npython -m uvicorn main:app --reload --port 8000\n\`\`\``);
      setStage("result");
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
    }
  };

  const handleRefine = async () => {
    if (!feedback.trim() || !sessionId) return;
    setRefining(true);

    try {
      const res = await fetch(`${API_URL}/api/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, feedback }),
      });
      const data = await res.json();
      setItinerary(data.itinerary);
      setToolCalls(data.tool_calls || []);
      setFeedback("");
    } catch {
      // Silently handle
    } finally {
      setRefining(false);
    }
  };

  return (
    <>
      <Navbar />
      <main style={{ paddingTop: 96, minHeight: "100vh" }}>
        <div className="container">
          <AnimatePresence mode="wait">
            {/* ═══════════════ FORM STAGE ═══════════════ */}
            {stage === "form" && (
              <motion.div
                key="form"
                initial="hidden"
                animate="visible"
                exit={{ opacity: 0, y: -20, transition: { duration: 0.3 } }}
                variants={fadeUp}
              >
                <div style={{ textAlign: "center", marginBottom: 48 }}>
                  <h1 className="display-sm gradient-text">Plan Your Trip</h1>
                  <p className="body-lg" style={{ color: "var(--muted)", marginTop: 12 }}>
                    Tell us about your dream trip and our AI agents will handle the rest.
                  </p>
                </div>

                {/* ── Card 1: Trip Essentials ── */}
                <div className="glass-card" style={{ marginBottom: 24 }}>
                  <div className="label-sm" style={{ color: "var(--primary)", marginBottom: 20 }}>
                    Trip Essentials
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                    <div>
                      <label className="input-label">Destination</label>
                      <input
                        className="input-field"
                        placeholder="e.g. Kyoto, Japan"
                        value={form.destination}
                        onChange={(e) => setForm({ ...form, destination: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="input-label">Traveling From</label>
                      <input
                        className="input-field"
                        placeholder="e.g. New Delhi"
                        value={form.origin}
                        onChange={(e) => setForm({ ...form, origin: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="input-label">Start Date</label>
                      <input
                        type="date"
                        className="input-field"
                        value={form.startDate}
                        onChange={(e) => setForm({ ...form, startDate: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="input-label">End Date</label>
                      <input
                        type="date"
                        className="input-field"
                        value={form.endDate}
                        onChange={(e) => setForm({ ...form, endDate: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="input-label">Budget</label>
                      <input
                        className="input-field"
                        placeholder="e.g. $2,000 or ₹1,50,000"
                        value={form.budget}
                        onChange={(e) => setForm({ ...form, budget: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="input-label">Purpose</label>
                      <select
                        className="input-field"
                        value={form.purpose}
                        onChange={(e) => setForm({ ...form, purpose: e.target.value })}
                      >
                        {purposeOptions.map((o) => (
                          <option key={o} value={o}>{o}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                {/* ── Card 2: Interests ── */}
                <div className="glass-card" style={{ marginBottom: 24 }}>
                  <div className="label-sm" style={{ color: "var(--primary)", marginBottom: 20 }}>
                    Your Interests
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                    {interestOptions.map((opt) => (
                      <button
                        key={opt}
                        className={`chip ${form.interests.includes(opt) ? "active" : ""}`}
                        onClick={() => setForm({ ...form, interests: toggleChip(form.interests, opt) })}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                  <div style={{ marginTop: 20 }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
                      <input
                        type="checkbox"
                        checked={form.hiddenGems}
                        onChange={(e) => setForm({ ...form, hiddenGems: e.target.checked })}
                        style={{ accentColor: "var(--primary)", width: 18, height: 18 }}
                      />
                      <span className="body-md" style={{ color: "var(--on-surface-variant)" }}>
                        Prefer hidden gems over tourist hotspots
                      </span>
                    </label>
                  </div>
                </div>

                {/* ── Card 3: Dietary & Mobility ── */}
                <div className="glass-card" style={{ marginBottom: 24 }}>
                  <div className="label-sm" style={{ color: "var(--primary)", marginBottom: 20 }}>
                    Dietary & Mobility
                  </div>
                  <div style={{ marginBottom: 20 }}>
                    <label className="input-label">Dietary Restrictions</label>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 6 }}>
                      {dietaryOptions.map((opt) => (
                        <button
                          key={opt}
                          className={`chip ${form.dietary.includes(opt) ? "active" : ""}`}
                          onClick={() => setForm({ ...form, dietary: toggleChip(form.dietary, opt) })}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div style={{ marginBottom: 20 }}>
                    <label className="input-label">Cuisine Preferences</label>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 6 }}>
                      {cuisineOptions.map((opt) => (
                        <button
                          key={opt}
                          className={`chip ${form.cuisines.includes(opt) ? "active" : ""}`}
                          onClick={() => setForm({ ...form, cuisines: toggleChip(form.cuisines, opt) })}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                    <div>
                      <label className="input-label">Walking Tolerance</label>
                      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 6 }}>
                        <input
                          type="range"
                          min={0}
                          max={12}
                          value={form.walkingHours}
                          onChange={(e) => setForm({ ...form, walkingHours: parseInt(e.target.value) })}
                          style={{ flex: 1, accentColor: "var(--primary)" }}
                        />
                        <span className="label-md" style={{ color: "var(--on-surface)", minWidth: 60, textAlign: "right" }}>
                          {form.walkingHours} hrs
                        </span>
                      </div>
                    </div>
                    <div>
                      <label className="input-label">Accommodation</label>
                      <select
                        className="input-field"
                        value={form.accommodation}
                        onChange={(e) => setForm({ ...form, accommodation: e.target.value })}
                      >
                        {accommodationOptions.map((o) => (
                          <option key={o} value={o}>{o}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                {/* ── Submit ── */}
                <button className="btn btn-primary btn-lg btn-full" onClick={handleSubmit}>
                  ✨ Generate My Itinerary
                </button>
                <div style={{ height: 64 }} />
              </motion.div>
            )}

            {/* ═══════════════ LOADING STAGE ═══════════════ */}
            {stage === "loading" && (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  minHeight: "60vh",
                  gap: 32,
                }}
              >
                {/* Spinner */}
                <div style={{ position: "relative", width: 80, height: 80 }}>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                    style={{
                      width: 80,
                      height: 80,
                      borderRadius: "50%",
                      border: "3px solid var(--outline)",
                      borderTopColor: "var(--primary)",
                    }}
                  />
                </div>

                <div style={{ textAlign: "center" }}>
                  <h2 className="headline-sm" style={{ marginBottom: 8 }}>
                    Crafting Your Itinerary
                  </h2>
                  <p className="body-md" style={{ color: "var(--muted)" }}>
                    Our AI agents are gathering real-time data…
                  </p>
                </div>

                {/* Tool Activity Feed */}
                <div className="glass-card" style={{ width: "100%", maxWidth: 400 }}>
                  <div className="label-sm" style={{ color: "var(--secondary)", marginBottom: 16 }}>
                    Agent Activity
                  </div>
                  {loadingTools.map((tool, i) => (
                    <motion.div
                      key={tool}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 }}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        padding: "8px 0",
                        borderBottom: i < loadingTools.length - 1 ? "1px solid var(--outline-variant)" : "none",
                        fontSize: 14,
                        color: "var(--on-surface-variant)",
                      }}
                    >
                      <motion.span
                        animate={{ opacity: [1, 0.4, 1] }}
                        transition={{ repeat: Infinity, duration: 2 }}
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: "50%",
                          background: "var(--secondary)",
                          display: "inline-block",
                        }}
                      />
                      {tool}
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* ═══════════════ RESULT STAGE ═══════════════ */}
            {stage === "result" && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                {/* Header */}
                <div style={{ marginBottom: 32 }}>
                  <h1 className="display-sm gradient-text">
                    Your Trip to {form.destination}
                  </h1>
                  <p className="body-lg" style={{ color: "var(--muted)", marginTop: 8 }}>
                    {form.startDate} — {form.endDate} · {form.purpose}
                  </p>
                  {/* Chips */}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 16 }}>
                    {[
                      ["Budget", form.budget],
                      ["From", form.origin],
                      ["Stay", form.accommodation],
                      ["Walking", `${form.walkingHours} hrs/day`],
                    ].map(([label, value]) => (
                      <span key={label} className="chip">
                        {label}: <span className="chip-value">{value}</span>
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 24, alignItems: "start" }}>
                  {/* Left: Itinerary */}
                  <div className="glass-card" style={{ padding: 32, minHeight: 400 }}>
                    <div
                      style={{
                        fontFamily: "var(--font-body)",
                        fontSize: 15,
                        lineHeight: 1.8,
                        color: "var(--on-surface)",
                      }}
                    >
                      <ReactMarkdown
                        components={{
                          h1: ({ children }) => (
                            <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16, marginTop: 24, fontFamily: "var(--font-headline)", color: "var(--on-surface)" }}>
                              {children}
                            </h1>
                          ),
                          h2: ({ children }) => (
                            <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 12, marginTop: 28, fontFamily: "var(--font-headline)", color: "var(--primary)", borderBottom: "1px solid var(--outline-variant)", paddingBottom: 8 }}>
                              {children}
                            </h2>
                          ),
                          h3: ({ children }) => (
                            <h3 style={{ fontSize: 17, fontWeight: 600, marginBottom: 8, marginTop: 20, fontFamily: "var(--font-headline)", color: "var(--on-surface)", background: "var(--surface-high)", padding: "10px 16px", borderRadius: "var(--radius-md)", borderLeft: "3px solid var(--primary)" }}>
                              {children}
                            </h3>
                          ),
                          p: ({ children }) => <p style={{ marginBottom: 12 }}>{children}</p>,
                          li: ({ children }) => (
                            <li style={{ marginBottom: 6, paddingLeft: 4 }}>{children}</li>
                          ),
                          strong: ({ children }) => (
                            <strong style={{ color: "var(--on-surface)", fontWeight: 600 }}>
                              {children}
                            </strong>
                          ),
                          em: ({ children }) => (
                            <em style={{ color: "var(--secondary)", fontStyle: "italic" }}>
                              {children}
                            </em>
                          ),
                        }}
                      >
                        {itinerary}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {/* Right: Side Panel */}
                  <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    {/* AI Activity */}
                    {toolCalls.length > 0 && (
                      <div className="glass-card">
                        <div className="label-sm" style={{ color: "var(--secondary)", marginBottom: 12 }}>
                          AI Tools Used
                        </div>
                        {toolCalls.map((tool, i) => (
                          <div
                            key={i}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 8,
                              padding: "6px 0",
                              fontSize: 13,
                              color: "var(--on-surface-variant)",
                            }}
                          >
                            <span style={{ color: "var(--secondary)" }}>✓</span>
                            {tool}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Refine */}
                    <div className="glass-card">
                      <div className="label-sm" style={{ color: "var(--primary)", marginBottom: 12 }}>
                        Refine Your Trip
                      </div>
                      <textarea
                        className="input-field"
                        placeholder="E.g. Add more outdoor activities, swap Day 2 lunch…"
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        rows={3}
                        style={{ resize: "vertical", marginBottom: 12 }}
                      />
                      <button
                        className="btn btn-primary btn-full"
                        onClick={handleRefine}
                        disabled={refining}
                      >
                        {refining ? "Refining…" : "Refine ✨"}
                      </button>
                    </div>

                    {/* Actions */}
                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        className="btn btn-ghost"
                        onClick={() => {
                          setStage("form");
                          setItinerary("");
                          setSessionId("");
                          setToolCalls([]);
                        }}
                        style={{ flex: 1 }}
                      >
                        ← Start Over
                      </button>
                    </div>
                  </div>
                </div>
                <div style={{ height: 64 }} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </>
  );
}
