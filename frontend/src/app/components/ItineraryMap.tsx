"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Place {
  name: string;
  lat: number;
  lon: number;
  day: number;
  time: string;
  category: string;
  cost: number;
  cost_usd: number;
  currency: string;
  description: string;
}

interface ItineraryMapProps {
  places: Place[];
  destination: string;
}

const DAY_COLORS = [
  "#6366f1", // indigo
  "#06b6d4", // cyan
  "#f59e0b", // amber
  "#10b981", // emerald
  "#ef4444", // red
  "#8b5cf6", // violet
  "#ec4899", // pink
  "#14b8a6", // teal
  "#f97316", // orange
  "#3b82f6", // blue
];

const CATEGORY_ICONS: Record<string, string> = {
  attraction: "🏛️",
  restaurant: "🍽️",
  hotel: "🏨",
  transport: "🚗",
  shopping: "🛍️",
  entertainment: "🎭",
};

export default function ItineraryMap({ places, destination }: ItineraryMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const [activeDays, setActiveDays] = useState<Set<number>>(new Set());
  const [isClient, setIsClient] = useState(false);

  // Get unique days
  const days = [...new Set(places.map((p) => p.day))].sort((a, b) => a - b);

  useEffect(() => {
    setIsClient(true);
    setActiveDays(new Set(days));
  }, []);

  useEffect(() => {
    if (!isClient || !mapRef.current || places.length === 0) return;

    // Dynamically import leaflet (SSR-safe)
    const initMap = async () => {
      const L = (await import("leaflet")).default;

      // Import leaflet CSS
      if (!document.querySelector('link[href*="leaflet.css"]')) {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(link);
      }

      // Destroy previous map
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }

      const map = L.map(mapRef.current!, {
        zoomControl: false,
        attributionControl: false,
      });

      // Add dark-themed tiles
      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        {
          attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
          maxZoom: 19,
        }
      ).addTo(map);

      // Add zoom control to bottom-right
      L.control.zoom({ position: "bottomright" }).addTo(map);

      const markers: any[] = [];
      const dayGroups: Record<number, any[]> = {};

      // Filter places by active days
      const filteredPlaces = places.filter((p) => activeDays.has(p.day));

      filteredPlaces.forEach((place) => {
        if (place.lat === 0 && place.lon === 0) return;

        const color = DAY_COLORS[(place.day - 1) % DAY_COLORS.length];
        const icon = CATEGORY_ICONS[place.category] || "📍";

        // Create custom marker
        const markerIcon = L.divIcon({
          className: "tripi-marker",
          html: `<div style="
            background: ${color};
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            border: 2px solid rgba(255,255,255,0.3);
          ">${icon}</div>`,
          iconSize: [32, 32],
          iconAnchor: [16, 16],
          popupAnchor: [0, -20],
        });

        const marker = L.marker([place.lat, place.lon], { icon: markerIcon });

        // Popup content
        const costStr = place.cost > 0
          ? `<br/><span style="color:#4cd7f6">💰 ${place.currency} ${place.cost.toLocaleString()}${place.cost_usd > 0 ? ` (~$${place.cost_usd})` : ""}</span>`
          : "";

        marker.bindPopup(
          `<div style="font-family: Inter, sans-serif; font-size: 13px; min-width: 180px;">
            <strong style="font-size: 14px; color: #dae2fd;">${icon} ${place.name}</strong>
            <br/><span style="color: #908fa0;">Day ${place.day} · ${place.time}</span>
            ${costStr}
            ${place.description ? `<br/><span style="color: #c7c4d7; font-size: 12px;">${place.description}</span>` : ""}
          </div>`,
          {
            className: "tripi-popup",
          }
        );

        marker.addTo(map);
        markers.push(marker);

        // Group by day for polylines
        if (!dayGroups[place.day]) dayGroups[place.day] = [];
        dayGroups[place.day].push([place.lat, place.lon]);
      });

      // Draw polylines between places per day
      Object.entries(dayGroups).forEach(([dayStr, coords]) => {
        const day = parseInt(dayStr);
        if (coords.length < 2) return;
        const color = DAY_COLORS[(day - 1) % DAY_COLORS.length];
        L.polyline(coords, {
          color,
          weight: 2,
          opacity: 0.5,
          dashArray: "6 4",
        }).addTo(map);
      });

      // Fit bounds
      if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.15));
      }

      mapInstanceRef.current = map;
    };

    initMap();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [isClient, places, activeDays]);

  const toggleDay = (day: number) => {
    setActiveDays((prev) => {
      const next = new Set(prev);
      if (next.has(day)) {
        next.delete(day);
      } else {
        next.add(day);
      }
      return next;
    });
  };

  if (!isClient) {
    return (
      <div className="map-container skeleton" style={{ height: 500 }} />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Day Filter */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
        <span className="label-sm" style={{ color: "var(--muted)", alignSelf: "center", marginRight: 8 }}>
          Filter by Day
        </span>
        {days.map((day) => {
          const color = DAY_COLORS[(day - 1) % DAY_COLORS.length];
          const active = activeDays.has(day);
          return (
            <button
              key={day}
              onClick={() => toggleDay(day)}
              style={{
                padding: "6px 14px",
                borderRadius: "var(--radius-full)",
                fontSize: 13,
                fontFamily: "var(--font-label)",
                fontWeight: 500,
                cursor: "pointer",
                transition: "all 200ms",
                border: `1px solid ${active ? color : "var(--outline)"}`,
                background: active ? `${color}22` : "var(--surface)",
                color: active ? color : "var(--muted)",
              }}
            >
              Day {day}
            </button>
          );
        })}
      </div>

      {/* Map */}
      <div
        ref={mapRef}
        className="map-container"
        style={{
          height: 500,
          borderRadius: "var(--radius-lg)",
          border: "1px solid var(--border-glass)",
          overflow: "hidden",
        }}
      />

      {/* Legend */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginTop: 12, fontSize: 12, color: "var(--muted)" }}>
        {Object.entries(CATEGORY_ICONS).map(([cat, icon]) => (
          <span key={cat} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            {icon} {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </span>
        ))}
      </div>
    </motion.div>
  );
}
