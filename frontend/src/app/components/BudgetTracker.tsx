"use client";

import { motion } from "framer-motion";

interface BudgetBreakdown {
  accommodation: number;
  food: number;
  activities: number;
  transport: number;
  miscellaneous: number;
}

interface BudgetSummary {
  total_estimated: number;
  user_budget: number;
  currency: string;
  breakdown: BudgetBreakdown;
}

interface BudgetTrackerProps {
  budget: BudgetSummary;
}

const CATEGORIES: { key: keyof BudgetBreakdown; label: string; icon: string; color: string }[] = [
  { key: "accommodation", label: "Accommodation", icon: "🏨", color: "#6366f1" },
  { key: "food", label: "Food & Dining", icon: "🍽️", color: "#06b6d4" },
  { key: "activities", label: "Activities", icon: "🎭", color: "#8b5cf6" },
  { key: "transport", label: "Transport", icon: "🚗", color: "#f59e0b" },
  { key: "miscellaneous", label: "Miscellaneous", icon: "📦", color: "#64748b" },
];

function DonutChart({ breakdown, total }: { breakdown: BudgetBreakdown; total: number }) {
  const size = 200;
  const strokeWidth = 28;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  let cumulativeOffset = 0;

  const segments = CATEGORIES.map((cat) => {
    const value = breakdown[cat.key] || 0;
    const percentage = total > 0 ? value / total : 0;
    const dashLength = percentage * circumference;
    const dashOffset = circumference - cumulativeOffset;
    cumulativeOffset += dashLength;

    return {
      ...cat,
      value,
      percentage,
      dashLength,
      dashOffset,
    };
  }).filter((s) => s.value > 0);

  return (
    <div style={{ position: "relative", width: size, height: size, margin: "0 auto" }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background ring */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--surface-high)"
          strokeWidth={strokeWidth}
        />
        {/* Data segments */}
        {segments.map((seg, i) => {
          const prevOffset = segments.slice(0, i).reduce((sum, s) => sum + s.dashLength, 0);
          return (
            <motion.circle
              key={seg.key}
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke={seg.color}
              strokeWidth={strokeWidth}
              strokeDasharray={`${seg.dashLength} ${circumference - seg.dashLength}`}
              strokeDashoffset={circumference - prevOffset}
              strokeLinecap="round"
              transform={`rotate(-90 ${center} ${center})`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
            />
          );
        })}
      </svg>
      {/* Center text */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 700, fontFamily: "var(--font-headline)", color: "var(--on-surface)" }}>
          ${total.toLocaleString()}
        </span>
        <span style={{ fontSize: 11, color: "var(--muted)", fontFamily: "var(--font-label)" }}>
          ESTIMATED
        </span>
      </div>
    </div>
  );
}

export default function BudgetTracker({ budget }: BudgetTrackerProps) {
  const { total_estimated, user_budget, breakdown } = budget;
  const percentage = user_budget > 0 ? (total_estimated / user_budget) * 100 : 0;
  const isOverBudget = percentage > 100;
  const isWarning = percentage > 85 && percentage <= 100;
  const barColor = isOverBudget ? "#ef4444" : isWarning ? "#f59e0b" : "#10b981";
  const statusLabel = isOverBudget
    ? `$${(total_estimated - user_budget).toLocaleString()} over budget`
    : `$${(user_budget - total_estimated).toLocaleString()} remaining`;
  const statusIcon = isOverBudget ? "🔴" : isWarning ? "🟡" : "🟢";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{ display: "flex", flexDirection: "column", gap: 24 }}
    >
      {/* Summary Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
        <div className="glass-card" style={{ textAlign: "center", padding: 20 }}>
          <div className="label-sm" style={{ color: "var(--muted)", marginBottom: 8 }}>Your Budget</div>
          <div style={{ fontSize: 24, fontWeight: 700, fontFamily: "var(--font-headline)", color: "var(--on-surface)" }}>
            ${user_budget.toLocaleString()}
          </div>
        </div>
        <div className="glass-card" style={{ textAlign: "center", padding: 20 }}>
          <div className="label-sm" style={{ color: "var(--muted)", marginBottom: 8 }}>Estimated Cost</div>
          <div style={{ fontSize: 24, fontWeight: 700, fontFamily: "var(--font-headline)", color: "var(--primary)" }}>
            ${total_estimated.toLocaleString()}
          </div>
        </div>
        <div className="glass-card" style={{ textAlign: "center", padding: 20 }}>
          <div className="label-sm" style={{ color: "var(--muted)", marginBottom: 8 }}>Status</div>
          <div style={{ fontSize: 16, fontWeight: 600, fontFamily: "var(--font-headline)", color: barColor }}>
            {statusIcon} {statusLabel}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="glass-card">
        <div className="label-sm" style={{ color: "var(--secondary)", marginBottom: 16 }}>
          Budget Utilization
        </div>
        <div
          style={{
            height: 12,
            borderRadius: "var(--radius-full)",
            background: "var(--surface-high)",
            overflow: "hidden",
            position: "relative",
          }}
        >
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(percentage, 100)}%` }}
            transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
            style={{
              height: "100%",
              borderRadius: "var(--radius-full)",
              background: `linear-gradient(90deg, ${barColor}cc, ${barColor})`,
              boxShadow: `0 0 12px ${barColor}44`,
            }}
          />
          {/* Budget limit marker */}
          {user_budget > 0 && (
            <div
              style={{
                position: "absolute",
                top: -4,
                bottom: -4,
                left: "100%",
                width: 2,
                background: "var(--on-surface)",
                borderRadius: 1,
              }}
            />
          )}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontSize: 12, color: "var(--muted)" }}>
          <span>$0</span>
          <span style={{ fontWeight: 600, color: barColor }}>{percentage.toFixed(0)}% used</span>
          <span>${user_budget.toLocaleString()}</span>
        </div>
      </div>

      {/* Donut + Category List */}
      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: 32, alignItems: "center" }}>
        <div className="glass-card" style={{ padding: 24 }}>
          <DonutChart breakdown={breakdown} total={total_estimated} />
        </div>

        <div className="glass-card" style={{ padding: 24 }}>
          <div className="label-sm" style={{ color: "var(--primary)", marginBottom: 16 }}>
            Spending by Category
          </div>
          {CATEGORIES.map((cat, i) => {
            const value = breakdown[cat.key] || 0;
            const pct = total_estimated > 0 ? (value / total_estimated) * 100 : 0;
            if (value === 0) return null;
            return (
              <motion.div
                key={cat.key}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "10px 0",
                  borderBottom: i < CATEGORIES.length - 1 ? "1px solid var(--outline-variant)" : "none",
                }}
              >
                <span style={{ fontSize: 20 }}>{cat.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: 14, fontWeight: 500, color: "var(--on-surface)" }}>{cat.label}</span>
                    <span style={{ fontSize: 14, fontWeight: 600, color: cat.color }}>${value.toLocaleString()}</span>
                  </div>
                  <div style={{ height: 4, borderRadius: 2, background: "var(--surface-high)" }}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.6, delay: i * 0.1 }}
                      style={{
                        height: "100%",
                        borderRadius: 2,
                        background: cat.color,
                      }}
                    />
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
