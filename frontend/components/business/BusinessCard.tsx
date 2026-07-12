"use client";
import Link from "next/link";
import Image from "next/image";
import { Stars } from "@/components/ui/Stars";
import type { BusinessListItem } from "@/types";

const PALETTES = [
  { bg: "#E8F0EA", text: "#1A3A2A", accent: "#2B6438" },
  { bg: "#FBF4E0", text: "#A8882E", accent: "#C9A84C" },
  { bg: "#EEF2FF", text: "#3730A3", accent: "#4F46E5" },
  { bg: "#FDF2F8", text: "#9D174D", accent: "#DB2777" },
  { bg: "#F0F9FF", text: "#075985", accent: "#0EA5E9" },
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
      <article className="card" style={{
        overflow: "hidden", cursor: "pointer", display: "flex", flexDirection: "column", height: "100%", padding: 0,
      }}>
        {/* Image band — real logo when present, soft gradient fallback otherwise */}
        <div style={{
          position: "relative", height: 108, flexShrink: 0,
          background: business.logo_url ? "var(--cream)" : `linear-gradient(135deg, ${pal.bg}, white)`,
        }}>
          {business.logo_url ? (
            <Image
              src={business.logo_url}
              alt=""
              fill
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
              style={{ objectFit: "cover" }}
              // Grid cards are almost always below the initial viewport
              // fold — default lazy loading means the browser doesn't
              // fetch these until they're about to scroll into view,
              // instead of downloading every card's image up front.
            />
          ) : (
            <div style={{
              position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <div style={{
                width: 52, height: 52, borderRadius: 14,
                background: pal.bg, color: pal.text,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 19,
                letterSpacing: "-0.02em", boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
              }}>
                {initials(business.name)}
              </div>
            </div>
          )}

          {/* Availability pill, floated over the image band */}
          <div style={{
            position: "absolute", top: 10, right: 10,
            display: "flex", alignItems: "center", gap: 5,
            fontSize: 11, fontWeight: 500, padding: "3px 9px", borderRadius: 100,
            background: business.is_available ? "rgba(240,245,241,0.95)" : "rgba(255,255,255,0.9)",
            color: business.is_available ? "var(--forest-600)" : "var(--ink-faint)",
            backdropFilter: "blur(4px)",
          }}>
            <div style={{
              width: 5, height: 5, borderRadius: "50%",
              background: business.is_available ? "#3D8050" : "#CBD5E1",
            }} />
            {business.is_available ? "Open" : "Busy"}
          </div>
        </div>

        <div style={{ padding: "16px 18px 18px", display: "flex", flexDirection: "column", flex: 1 }}>
          {/* Header */}
          <h3 style={{
            fontFamily: "var(--font-serif)", fontWeight: 600, fontSize: 15.5,
            color: "var(--forest)", lineHeight: 1.25, letterSpacing: "-0.01em",
            marginBottom: 6, overflow: "hidden", textOverflow: "ellipsis",
            display: "-webkit-box", WebkitLineClamp: 1, WebkitBoxOrient: "vertical",
          }}>
            {business.name}
          </h3>
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 12 }}>
            {category && (
              <span style={{
                fontSize: 11, fontWeight: 500, padding: "2px 8px",
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
            display: "flex", alignItems: "center", justifyContent: "space-between",
            paddingTop: 14, borderTop: "1px solid var(--border)",
          }}>
            <Stars rating={business.average_rating} count={business.review_count} size={12} />
            <span style={{
              fontSize: 12, fontWeight: 500, color: "var(--forest)",
              display: "flex", alignItems: "center", gap: 4,
            }}>
              View profile
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
