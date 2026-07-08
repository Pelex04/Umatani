"use client";
import Link from "next/link";
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
        padding: "18px", cursor: "pointer", display: "flex", flexDirection: "column", height: "100%",
      }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: 13, marginBottom: 14 }}>
          <div style={{
            width: 46, height: 46, borderRadius: 11, flexShrink: 0,
            background: pal.bg, color: pal.text,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 17,
            letterSpacing: "-0.02em",
          }}>
            {initials(business.name)}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h3 style={{
              fontFamily: "var(--font-serif)", fontWeight: 600, fontSize: 15.5,
              color: "var(--forest)", lineHeight: 1.2, letterSpacing: "-0.01em",
              marginBottom: 5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
            }}>
              {business.name}
            </h3>
            <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
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
          </div>
          {/* Availability dot */}
          <div style={{
            flexShrink: 0, display: "flex", alignItems: "center", gap: 5,
            fontSize: 11, fontWeight: 500, padding: "3px 9px", borderRadius: 100,
            background: business.is_available ? "var(--forest-100)" : "#F1F3F5",
            color: business.is_available ? "var(--forest-600)" : "var(--ink-faint)",
          }}>
            <div style={{
              width: 5, height: 5, borderRadius: "50%",
              background: business.is_available ? "#3D8050" : "#CBD5E1",
            }} />
            {business.is_available ? "Open" : "Busy"}
          </div>
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
      </article>
    </Link>
  );
}
