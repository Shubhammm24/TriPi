"use client";

import Link from "next/link";
import { useTheme } from "@/app/providers/ThemeProvider";
import { motion } from "framer-motion";

export default function Navbar() {
  const { theme, toggleTheme } = useTheme();

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        background: "var(--surface-glass)",
        backdropFilter: "var(--blur-surface)",
        WebkitBackdropFilter: "var(--blur-surface)",
        borderBottom: "1px solid var(--border-glass)",
      }}
    >
      <div
        style={{
          maxWidth: "var(--container-max)",
          margin: "0 auto",
          padding: "0 var(--gutter)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: 64,
        }}
      >
        {/* Logo */}
        <Link href="/" style={{ textDecoration: "none" }}>
          <span
            style={{
              fontFamily: "var(--font-headline)",
              fontSize: 24,
              fontWeight: 700,
              letterSpacing: "-0.02em",
              background: "var(--gradient-glow)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            TriPi
          </span>
        </Link>

        {/* Nav Links */}
        <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
          <Link
            href="/#features"
            style={{
              fontFamily: "var(--font-label)",
              fontSize: 13,
              fontWeight: 500,
              color: "var(--muted)",
              textDecoration: "none",
              letterSpacing: "0.04em",
              textTransform: "uppercase",
              transition: "color 200ms",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.color = "var(--on-surface)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.color = "var(--muted)")
            }
          >
            Features
          </Link>
          <Link
            href="/#how-it-works"
            style={{
              fontFamily: "var(--font-label)",
              fontSize: 13,
              fontWeight: 500,
              color: "var(--muted)",
              textDecoration: "none",
              letterSpacing: "0.04em",
              textTransform: "uppercase",
              transition: "color 200ms",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.color = "var(--on-surface)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.color = "var(--muted)")
            }
          >
            How It Works
          </Link>
          <Link
            href="/plan"
            style={{
              fontFamily: "var(--font-label)",
              fontSize: 13,
              fontWeight: 500,
              color: "var(--primary)",
              textDecoration: "none",
              letterSpacing: "0.04em",
              textTransform: "uppercase",
              transition: "color 200ms",
            }}
          >
            Plan a Trip
          </Link>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--outline)",
              borderRadius: "var(--radius-full)",
              width: 40,
              height: 40,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              transition: "var(--transition)",
              color: "var(--on-surface)",
              fontSize: 18,
            }}
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
        </div>
      </div>
    </motion.nav>
  );
}
