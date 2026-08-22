"use client";
import Link from "next/link";
import Image from "next/image";
import type { BusinessListItem } from "@/types";

// Burgundy-toned variations only — Direction 3 runs on one committed
// ink color rather than a rainbow of pastel category hues, so these
// differ in warmth/depth, not hue.
const PALETTES = [
  { bg: "#F5EBDF", text: "#43081F" },
  { bg: "#EDE0D3", text: "#5C1129" },
  { bg: "#F0E4D3", text: "#2B0512" },
];

function palette(name: string) { return PALETTES[name.charCodeAt(0) % PALETTES.length]; }
function initials(name: string) { return name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2); }

interface Props {
  business: BusinessListItem;
  school?: { name: string; city: string };
  category?: { name: string };
}

export function BusinessCard({ business, school, category }: Props) {
  const pal = palette(business.name);

  return (
    <Link href={`/businesses/${business.slug}`} style={{ textDecoration: "none", display: "block" }}>
      <article className="card f-card" style={{
        overflow: "hidden", cursor: "pointer", display: "flex", flexDirection: "column", height: "100%", padding: 0,
      }}>
        {/* Image band. Business logos are small square marks, not wide
            hero photos — the list endpoint doesn't even return a cover
            image, only logo_url. So a logo is shown the same way the
            initials fallback is: a small centered square badge on a
            flat background, never stretched full-bleed across the
            band (that crops/zooms square art into something illegible,
            especially for a portrait or off-center icon). */}
        <div style={{
          position: "relative", height: 108, flexShrink: 0,
          background: pal.bg, display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <div style={{
            width: 84, height: 84, borderRadius: 2,
            background: "var(--white)", color: pal.text,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "var(--font-serif)", fontWeight: 800, fontSize: 24,
            letterSpacing: "-0.01em", border: "1px solid var(--border)",
            overflow: "hidden", position: "relative",
          }}>
            {business.logo_url ? (
              <Image
                className="f-photo-img"
                src={business.logo_url}
                alt=""
                fill
                sizes="84px"
                style={{ objectFit: "cover" }}
                // Grid cards are almost always below the initial viewport
                // fold — default lazy loading means the browser doesn't
                // fetch these until they're about to scroll into view,
                // instead of downloading every card's image up front.
              />
            ) : (
              initials(business.name)
            )}
          </div>

          {/* Availability status, floated over the image band — plain
              text tag, no dot/glow */}
          <span className={`status-tag ${business.is_available ? "is-open" : "is-closed"}`} style={{
            position: "absolute", top: 10, right: 10, backdropFilter: "blur(4px)",
          }}>
            {business.is_available ? "Open" : "Busy"}
          </span>
        </div>

        <div style={{ padding: "16px 18px 18px", display: "flex", flexDirection: "column", flex: 1 }}>
          {/* Header */}
          <h3 style={{
            fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 15.5,
            color: "var(--forest)", lineHeight: 1.25, letterSpacing: "-0.01em",
            marginBottom: 6, overflow: "hidden", textOverflow: "ellipsis",
            display: "-webkit-box", WebkitLineClamp: 1, WebkitBoxOrient: "vertical",
          }}>
            {business.name}
          </h3>
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 12 }}>
            {category && (
              <span style={{
                fontSize: 11, fontWeight: 600, padding: "2px 9px",
                borderRadius: 100, background: pal.bg, color: pal.text,
              }}>
                {category.name}
              </span>
            )}
            {school && (
              <span style={{ fontSize: 11, color: "var(--ink-faint)" }}>{school.city}</span>
            )}
          </div>

          {/* Description */}
          <p className="lc-2" style={{
            fontSize: 13, color: "var(--ink-muted)", lineHeight: 1.65,
            flex: 1, marginBottom: 16,
          }}>
            {business.description}
          </p>

          {/* Footer */}
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "flex-end",
            paddingTop: 14, borderTop: "1px solid var(--border)",
          }}>
            <span style={{
              fontSize: 11, fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--forest)",
              display: "flex", alignItems: "center", gap: 4,
            }}>
              View
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2.5 6h7M7 3.5 9.5 6 7 8.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </span>
          </div>
        </div>
      </article>
    </Link>
  );
}
