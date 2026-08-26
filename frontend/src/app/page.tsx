"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import Navbar from "@/app/components/Navbar";

const EASE_CURVE = [0.4, 0, 0.2, 1] as const;

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.12, duration: 0.5, ease: [...EASE_CURVE] as [number, number, number, number] },
  }),
};

const features = [
  {
    icon: "⚡",
    title: "Real-Time Intelligence",
    description:
      "Live weather forecasts, currency conversion, and destination data pulled from multiple APIs in real-time.",
  },
  {
    icon: "📋",
    title: "Smart Itineraries",
    description:
      "AI agents build optimized day-by-day plans with precise timing, restaurant suggestions, and cost estimates.",
  },
  {
    icon: "🗺️",
    title: "Local Expertise",
    description:
      "Discover hidden gems, safety tips, and packing guides from our curated knowledge base and web search.",
  },
];

const steps = [
  {
    num: "01",
    title: "Tell Us Your Dream Trip",
    description: "Fill in your destination, budget, dates, and interests.",
  },
  {
    num: "02",
    title: "AI Gathers Real Data",
    description: "Our agents check weather, search attractions, and optimize your budget.",
  },
  {
    num: "03",
    title: "Get Your Perfect Itinerary",
    description: "Receive a detailed day-by-day plan you can refine through chat.",
  },
];

export default function Home() {
  return (
    <>
      <Navbar />

      {/* ═══ HERO ═══ */}
      <section
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
          overflow: "hidden",
          paddingTop: 64,
        }}
      >
        {/* Animated background mesh */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `
              radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,102,241,0.15), transparent),
              radial-gradient(ellipse 60% 40% at 80% 80%, rgba(6,182,212,0.08), transparent),
              radial-gradient(ellipse 40% 30% at 10% 60%, rgba(99,102,241,0.06), transparent)
            `,
            pointerEvents: "none",
          }}
        />
        {/* Grid overlay */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage: `
              linear-gradient(rgba(99,102,241,0.03) 1px, transparent 1px),
              linear-gradient(90deg, rgba(99,102,241,0.03) 1px, transparent 1px)
            `,
            backgroundSize: "60px 60px",
            pointerEvents: "none",
            maskImage: "radial-gradient(ellipse 70% 70% at 50% 50%, black, transparent)",
            WebkitMaskImage: "radial-gradient(ellipse 70% 70% at 50% 50%, black, transparent)",
          }}
        />

        <div className="container" style={{ textAlign: "center", position: "relative", zIndex: 1 }}>
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            custom={0}
            style={{ marginBottom: 16 }}
          >
            <span
              className="label-sm"
              style={{
                color: "var(--secondary)",
                padding: "6px 16px",
                border: "1px solid rgba(6,182,212,0.2)",
                borderRadius: "var(--radius-full)",
                background: "rgba(6,182,212,0.06)",
              }}
            >
              Powered by AI Agents
            </span>
          </motion.div>

          <motion.h1
            className="display-lg"
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            custom={1}
            style={{ maxWidth: 800, margin: "24px auto" }}
          >
            Plan Your Next{" "}
            <span className="gradient-text">Adventure</span>
            {" "}with AI
          </motion.h1>

          <motion.p
            className="body-lg"
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            custom={2}
            style={{
              color: "var(--muted)",
              maxWidth: 580,
              margin: "0 auto 40px",
            }}
          >
            TriPi uses intelligent agents to craft personalized itineraries with
            real-time weather, local insights, and budget optimization.
          </motion.p>

          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            custom={3}
          >
            <Link href="/plan" className="btn btn-primary btn-lg">
              Start Planning →
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ═══ FEATURES ═══ */}
      <section id="features" className="section" style={{ position: "relative" }}>
        <div className="container">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeUp}
            custom={0}
            style={{ textAlign: "center", marginBottom: 64 }}
          >
            <span className="label-sm" style={{ color: "var(--primary)", marginBottom: 12, display: "block" }}>
              Features
            </span>
            <h2 className="headline-lg">Intelligence at Every Step</h2>
          </motion.div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
              gap: 24,
            }}
          >
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                className="glass-card"
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-50px" }}
                variants={fadeUp}
                custom={i + 1}
                style={{ padding: 32 }}
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: "var(--radius-md)",
                    background: "rgba(99,102,241,0.1)",
                    border: "1px solid rgba(99,102,241,0.15)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 22,
                    marginBottom: 20,
                  }}
                >
                  {f.icon}
                </div>
                <h3 className="title-md" style={{ marginBottom: 12 }}>
                  {f.title}
                </h3>
                <p className="body-md" style={{ color: "var(--muted)" }}>
                  {f.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ HOW IT WORKS ═══ */}
      <section id="how-it-works" className="section" style={{ background: "var(--bg-dim)" }}>
        <div className="container">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeUp}
            custom={0}
            style={{ textAlign: "center", marginBottom: 64 }}
          >
            <span className="label-sm" style={{ color: "var(--secondary)", marginBottom: 12, display: "block" }}>
              How It Works
            </span>
            <h2 className="headline-lg">Three Steps to Your Perfect Trip</h2>
          </motion.div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: 32,
              position: "relative",
            }}
          >
            {steps.map((s, i) => (
              <motion.div
                key={s.num}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-50px" }}
                variants={fadeUp}
                custom={i + 1}
                style={{ textAlign: "center" }}
              >
                <div
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: "var(--radius-full)",
                    background: "var(--gradient-primary)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 auto 20px",
                    fontFamily: "var(--font-headline)",
                    fontSize: 20,
                    fontWeight: 700,
                    color: "#fff",
                    boxShadow: "var(--shadow-glow)",
                  }}
                >
                  {s.num}
                </div>
                <h3 className="title-md" style={{ marginBottom: 8 }}>
                  {s.title}
                </h3>
                <p className="body-md" style={{ color: "var(--muted)", maxWidth: 300, margin: "0 auto" }}>
                  {s.description}
                </p>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={fadeUp}
            custom={4}
            style={{ textAlign: "center", marginTop: 64 }}
          >
            <Link href="/plan" className="btn btn-primary btn-lg">
              Start Planning Your Trip →
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer
        style={{
          borderTop: "1px solid var(--border-glass)",
          padding: "48px 0",
          textAlign: "center",
        }}
      >
        <div className="container">
          <span
            style={{
              fontFamily: "var(--font-headline)",
              fontSize: 20,
              fontWeight: 700,
              background: "var(--gradient-glow)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            TriPi
          </span>
          <p className="body-md" style={{ color: "var(--muted)", marginTop: 12 }}>
            AI-powered travel planning • Built with LangGraph + Gemini
          </p>
          <p style={{ color: "var(--outline)", fontSize: 13, marginTop: 16 }}>
            © {new Date().getFullYear()} TriPi. All rights reserved.
          </p>
        </div>
      </footer>
    </>
  );
}
