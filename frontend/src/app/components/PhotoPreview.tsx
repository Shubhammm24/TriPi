"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface Place {
  name: string;
  day: number;
  category: string;
}

interface Photo {
  id: string;
  url_small: string;
  url_regular: string;
  alt: string;
  author: string;
  author_url: string;
}

interface PhotoPreviewProps {
  places: Place[];
  destination: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function PhotoPreview({ places, destination }: PhotoPreviewProps) {
  const [photos, setPhotos] = useState<(Photo & { placeName: string; day: number })[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPhoto, setSelectedPhoto] = useState<(Photo & { placeName: string }) | null>(null);

  useEffect(() => {
    const fetchPhotos = async () => {
      setLoading(true);

      // Get unique place names (limit to 8 to avoid rate limits)
      const uniquePlaces = places
        .filter((p) => p.category === "attraction" || p.category === "restaurant" || p.category === "entertainment")
        .slice(0, 8);

      // Also fetch destination-level photos
      const queries = [
        { query: `${destination} travel`, placeName: destination, day: 0 },
        ...uniquePlaces.map((p) => ({
          query: `${p.name} ${destination}`,
          placeName: p.name,
          day: p.day,
        })),
      ];

      const allPhotos: (Photo & { placeName: string; day: number })[] = [];

      // Fetch in parallel (batch of 3 to avoid rate limit)
      for (let i = 0; i < queries.length; i += 3) {
        const batch = queries.slice(i, i + 3);
        const results = await Promise.allSettled(
          batch.map(async (q) => {
            try {
              const res = await fetch(
                `${API_URL}/api/unsplash?query=${encodeURIComponent(q.query)}&per_page=2`
              );
              if (!res.ok) return [];
              const data = await res.json();
              return (data.results || []).map((photo: Photo) => ({
                ...photo,
                placeName: q.placeName,
                day: q.day,
              }));
            } catch {
              return [];
            }
          })
        );

        results.forEach((r) => {
          if (r.status === "fulfilled" && r.value.length > 0) {
            allPhotos.push(...r.value);
          }
        });
      }

      setPhotos(allPhotos);
      setLoading(false);
    };

    if (places.length > 0) {
      fetchPhotos();
    } else {
      setLoading(false);
    }
  }, [places, destination]);

  if (loading) {
    return (
      <div style={{ display: "flex", gap: 16, overflowX: "auto", padding: "8px 0" }}>
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="skeleton"
            style={{
              minWidth: 280,
              height: 200,
              borderRadius: "var(--radius-lg)",
              flexShrink: 0,
            }}
          />
        ))}
      </div>
    );
  }

  if (photos.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass-card"
        style={{ textAlign: "center", padding: 48 }}
      >
        <div style={{ fontSize: 48, marginBottom: 16 }}>📷</div>
        <h3 className="headline-sm" style={{ marginBottom: 8 }}>No Photos Available</h3>
        <p className="body-md" style={{ color: "var(--muted)" }}>
          Add an <code>UNSPLASH_ACCESS_KEY</code> to your <code>.env</code> file to see destination photos.
          <br />
          Get a free key at{" "}
          <a
            href="https://unsplash.com/developers"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "var(--primary)" }}
          >
            unsplash.com/developers
          </a>
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      {/* Scrollable Photo Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 16,
        }}
      >
        {photos.map((photo, i) => (
          <motion.div
            key={`${photo.id}-${i}`}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.05, duration: 0.3 }}
            onClick={() => setSelectedPhoto(photo)}
            style={{
              position: "relative",
              borderRadius: "var(--radius-lg)",
              overflow: "hidden",
              cursor: "pointer",
              aspectRatio: "16/10",
              border: "1px solid var(--border-glass)",
            }}
          >
            <img
              src={photo.url_small}
              alt={photo.alt || photo.placeName}
              loading="lazy"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transition: "transform 300ms ease",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
              onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
            />
            {/* Overlay */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: "linear-gradient(transparent 50%, rgba(0,0,0,0.7))",
                display: "flex",
                flexDirection: "column",
                justifyContent: "flex-end",
                padding: 16,
              }}
            >
              <div style={{ fontSize: 15, fontWeight: 600, color: "#fff" }}>{photo.placeName}</div>
              {photo.day > 0 && (
                <div
                  style={{
                    position: "absolute",
                    top: 12,
                    right: 12,
                    background: "var(--gradient-primary)",
                    color: "#fff",
                    fontSize: 11,
                    fontWeight: 600,
                    padding: "3px 10px",
                    borderRadius: "var(--radius-full)",
                    fontFamily: "var(--font-label)",
                  }}
                >
                  Day {photo.day}
                </div>
              )}
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.6)", marginTop: 2 }}>
                📸 {photo.author}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Lightbox */}
      {selectedPhoto && (
        <div
          onClick={() => setSelectedPhoto(null)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 1000,
            background: "rgba(0,0,0,0.85)",
            backdropFilter: "blur(20px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "zoom-out",
            padding: 40,
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            style={{ maxWidth: "90vw", maxHeight: "85vh", position: "relative" }}
          >
            <img
              src={selectedPhoto.url_regular}
              alt={selectedPhoto.alt || selectedPhoto.placeName}
              style={{
                maxWidth: "100%",
                maxHeight: "80vh",
                borderRadius: "var(--radius-lg)",
                boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
              }}
            />
            <div
              style={{
                textAlign: "center",
                marginTop: 16,
                color: "#fff",
                fontFamily: "var(--font-headline)",
              }}
            >
              <div style={{ fontSize: 18, fontWeight: 600 }}>{selectedPhoto.placeName}</div>
              <a
                href={selectedPhoto.author_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                style={{ color: "var(--secondary)", fontSize: 13 }}
              >
                📸 Photo by {selectedPhoto.author} on Unsplash
              </a>
            </div>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}
