"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { useReferenceData } from "@/lib/referenceData";
import { BusinessCard } from "@/components/business/BusinessCard";
import type { BusinessListItem } from "@/types";

const ROTATING_WORDS = ["designs", "bakes", "codes", "photographs", "tutors", "tailors", "repairs", "decorates"];

export default function Home() {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollY } = useScroll();

  const titleY  = useTransform(scrollY, [0, 600], [0, -120]);
  const titleO  = useTransform(scrollY, [0, 400],  [1, 0]);
  const imgScale = useTransform(scrollY, [0, 600], [1, 1.08]);

  const [wordIndex, setWordIndex] = useState(0);
  const [query,     setQuery]     = useState("");
  const [focused,   setFocused]   = useState(false);
  const { categories: cats, schools } = useReferenceData();
  const [bizList,   setBizList]   = useState<BusinessListItem[]>([]);
  const [loading,   setLoading]   = useState(true);

  useEffect(() => {
    const t = setInterval(() => setWordIndex(i => (i + 1) % ROTATING_WORDS.length), 2200);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    api.businesses.search({ limit: 3 })
      .then(b => setBizList(b.items))
      .finally(() => setLoading(false));
  }, []);

  const catMap    = Object.fromEntries(cats.map(c => [c.id, c]));
  const schoolMap = Object.fromEntries(schools.map(s => [s.id, s]));

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    router.push(query.trim() ? `/discover?keyword=${encodeURIComponent(query.trim())}` : "/discover");
  };

  return (
    <div ref={containerRef} style={{ overflowX: "hidden" }}>

      {/* ═══════════════════════════════════════════
          HERO — Full viewport, editorial split
      ═══════════════════════════════════════════ */}
      <section style={{ position: "relative", height: "100vh", minHeight: 640, overflow: "hidden", background: "#0D2118" }}>

        {/* Right-side image panel — hidden on mobile (see media query below):
            the headline box is only capped at 680px, so below that width it
            spans full-bleed, sitting on top of this panel's right 52% with
            no scrim in most of that area. A 50/50 split doesn't work at
            phone widths anyway; hiding it reveals the section's own solid
            dark background instead, which is intentional, not a fallback. */}
        <motion.div className="hero-image-panel" style={{ scale: imgScale, position: "absolute", top: 0, right: 0, width: "52%", height: "100%", overflow: "hidden", background: "#0D2118" }}>
          <Image
            src="https://images.unsplash.com/photo-1687422808384-c896d0efd4ab?q=80&w=1600&auto=format&fit=crop"
            alt=""
            fill
            priority
            sizes="52vw"
            style={{ objectFit: "cover", objectPosition: "center 30%" }}
          />
          {/* Dark scrim — a real photo needs more darkening than a pure
              gradient did, both so the left-edge text-fade below still
              reads cleanly and to keep the same moody, editorial tone
              as the rest of the hero rather than a raw stock photo. */}
          <div style={{ position: "absolute", inset: 0, background: "rgba(13,33,24,0.42)" }} />
          <div style={{
            position: "absolute", inset: 0,
            backgroundImage: `
              radial-gradient(ellipse at 30% 50%, rgba(201,168,76,0.1) 0%, transparent 60%),
              radial-gradient(circle at 70% 20%, rgba(26,58,42,0.55) 0%, transparent 50%)
            `,
          }} />
          {/* Geometric accent lines */}
          <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity: 0.1 }} viewBox="0 0 500 700" fill="none">
            <circle cx="250" cy="350" r="220" stroke="#C9A84C" strokeWidth="0.5"/>
            <circle cx="250" cy="350" r="160" stroke="#C9A84C" strokeWidth="0.5"/>
            <circle cx="250" cy="350" r="100" stroke="#C9A84C" strokeWidth="0.5"/>
            <line x1="0" y1="350" x2="500" y2="350" stroke="#C9A84C" strokeWidth="0.4"/>
            <line x1="250" y1="0" x2="250" y2="700" stroke="#C9A84C" strokeWidth="0.4"/>
          </svg>
          {/* Gold dot grid */}
          <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle, rgba(201,168,76,0.12) 1px, transparent 1px)", backgroundSize: "32px 32px", opacity: 0.6 }} />
          {/* Unsplash License doesn't require attribution, but it's a nice
              courtesy to the photographer and costs nothing visually. */}
          <a href="https://unsplash.com/@mkumbwajr" target="_blank" rel="noopener noreferrer"
            style={{ position: "absolute", bottom: 10, right: 14, fontSize: 9.5, color: "rgba(247,244,239,0.28)", textDecoration: "none", fontFamily: "var(--font-sans)", letterSpacing: "0.02em" }}>
            Photo: Ali Mkumbwa / Unsplash
          </a>
        </motion.div>

        {/* Left gradient fade */}
        <div className="hero-image-panel" style={{ position: "absolute", top: 0, left: "44%", width: "16%", height: "100%", background: "linear-gradient(to right, #0D2118, transparent)", zIndex: 2 }} />

        {/* Headline content */}
        <motion.div style={{ y: titleY, opacity: titleO, position: "absolute", inset: 0, zIndex: 3, display: "flex", flexDirection: "column", justifyContent: "center", padding: "0 6vw", maxWidth: 680 }}>

          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.1 }}>
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: "0.2em",
              textTransform: "uppercase", color: "rgba(201,168,76,0.7)",
              fontFamily: "var(--font-sans)",
            }}>
              Student talent · Malawi
            </span>
          </motion.div>

          <motion.h1 initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, delay: 0.25, ease: [0.16,1,0.3,1] }}
            className="hero-h1"
            style={{
              fontFamily: "var(--font-serif)", fontStyle: "italic",
              fontSize: "clamp(64px, 9vw, 120px)", fontWeight: 700,
              color: "#F7F4EF", lineHeight: 0.92, letterSpacing: "-0.035em",
              margin: "24px 0 0",
            }}>
            Umatani?
          </motion.h1>

          {/* Rotating statement */}
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, margin: "24px 0 0", overflow: "hidden" }}>
            <span style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "clamp(18px, 2.5vw, 26px)", fontWeight: 300, color: "rgba(247,244,239,0.38)", letterSpacing: "-0.02em", whiteSpace: "nowrap" }}>
              Find a student who
            </span>
            <AnimatePresence mode="wait">
              <motion.span key={wordIndex}
                initial={{ y: 24, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -24, opacity: 0 }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "clamp(18px, 2.5vw, 26px)", fontWeight: 700, color: "var(--gold)", letterSpacing: "-0.02em", display: "inline-block" }}>
                {ROTATING_WORDS[wordIndex]}
              </motion.span>
            </AnimatePresence>
          </div>

          {/* Search */}
          <motion.form initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.6, ease: [0.16,1,0.3,1] }}
            onSubmit={handleSearch}
            style={{ marginTop: 44, display: "flex", gap: 0, maxWidth: 500 }}>
            <div style={{
              flex: 1, display: "flex", alignItems: "center",
              background: "rgba(247,244,239,0.07)", backdropFilter: "blur(12px)",
              border: `1px solid ${focused ? "rgba(201,168,76,0.5)" : "rgba(247,244,239,0.12)"}`,
              borderRight: "none", borderRadius: "10px 0 0 10px", padding: "0 16px", gap: 10,
              transition: "border-color 0.2s",
            }}>
              <svg width="15" height="15" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0, opacity: 0.4 }}>
                <circle cx="8.5" cy="8.5" r="5.5" stroke="#F7F4EF" strokeWidth="1.75"/>
                <path d="M13 13l4.5 4.5" stroke="#F7F4EF" strokeWidth="1.75" strokeLinecap="round"/>
              </svg>
              <input value={query} onChange={e => setQuery(e.target.value)}
                onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
                placeholder="Search businesses, skills, services…"
                style={{ flex: 1, background: "transparent", border: "none", outline: "none", fontSize: 14, color: "#F7F4EF", fontFamily: "var(--font-sans)", padding: "13px 0" }} />
            </div>
            <button type="submit" style={{
              background: "var(--gold)", color: "#0D2118", border: "none",
              borderRadius: "0 10px 10px 0", padding: "0 22px",
              fontSize: 13.5, fontWeight: 700, cursor: "pointer",
              fontFamily: "var(--font-sans)", letterSpacing: "0.01em",
              flexShrink: 0, transition: "background 0.15s",
            }}
            onMouseEnter={e => (e.currentTarget.style.background = "#A8882E")}
            onMouseLeave={e => (e.currentTarget.style.background = "var(--gold)")}>
              Search
            </button>
          </motion.form>

          {/* Category pills */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1, duration: 0.6 }}
            style={{ display: "flex", flexWrap: "wrap", gap: 7, marginTop: 20 }}>
            {(cats.length ? cats.slice(0, 6) : ["Graphic Design","Photography","Baking","Tutoring","Programming","Tailoring"].map((n,i) => ({ id: String(i), name: n }))).map(c => (
              <button key={c.id} onClick={() => router.push(cats.length ? `/discover?category_id=${c.id}` : `/discover?keyword=${c.name}`)}
                style={{
                  background: "transparent", border: "1px solid rgba(247,244,239,0.12)",
                  borderRadius: 100, padding: "5px 14px", fontSize: 11.5,
                  color: "rgba(247,244,239,0.5)", cursor: "pointer",
                  fontFamily: "var(--font-sans)", transition: "all 0.18s",
                }}
                onMouseEnter={e => { const el = e.currentTarget; el.style.background = "rgba(201,168,76,0.12)"; el.style.borderColor = "rgba(201,168,76,0.35)"; el.style.color = "rgba(247,244,239,0.85)"; }}
                onMouseLeave={e => { const el = e.currentTarget; el.style.background = "transparent"; el.style.borderColor = "rgba(247,244,239,0.12)"; el.style.color = "rgba(247,244,239,0.5)"; }}>
                {c.name}
              </button>
            ))}
          </motion.div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.4 }}
          style={{ position: "absolute", bottom: 32, left: "6vw", zIndex: 4, display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 1, height: 48, background: "linear-gradient(to bottom, transparent, rgba(201,168,76,0.5))" }} />
          <span style={{ fontSize: 9, letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(247,244,239,0.25)", fontFamily: "var(--font-sans)", writingMode: "vertical-rl" }}>Scroll</span>
        </motion.div>

        {/* Bottom stats bar */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2, duration: 0.7 }}
          style={{
            position: "absolute", bottom: 0, left: 0, right: 0, zIndex: 4,
            borderTop: "1px solid rgba(247,244,239,0.06)",
            background: "rgba(13,33,24,0.6)", backdropFilter: "blur(16px)",
            display: "flex",
          }}>
          {[["3","Verified businesses"],["12","Service categories"],["1","University"],["Free","Always"]].map(([n, l], i) => (
            <div key={n} style={{
              flex: 1, padding: "18px 24px", textAlign: "center",
              borderRight: i < 3 ? "1px solid rgba(247,244,239,0.06)" : "none",
            }}>
              <div style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 22, color: "#F7F4EF", lineHeight: 1, marginBottom: 4 }}>{n}</div>
              <div style={{ fontSize: 10, color: "rgba(247,244,239,0.3)", letterSpacing: "0.08em", fontFamily: "var(--font-sans)", textTransform: "uppercase" }}>{l}</div>
            </div>
          ))}
        </motion.div>
      </section>

      {/* ═══════════════════════════════════════════
          BUSINESSES — Asymmetric editorial grid
      ═══════════════════════════════════════════ */}
      <section style={{ background: "var(--cream)", padding: "96px 0 80px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 6vw" }}>
          {/* Section header — pushed right */}
          <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 52 }}>
            <div>
              <motion.p className="eyebrow" style={{ marginBottom: 12 }}
                initial={{ opacity: 0, x: -12 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }}>
                Discover
              </motion.p>
              <motion.h2 initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.7, ease: [0.16,1,0.3,1] }}
                style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: "clamp(30px, 4vw, 48px)", color: "var(--forest)", letterSpacing: "-0.03em", lineHeight: 1.05 }}>
                Student businesses<br />
                <em style={{ fontStyle: "italic", color: "var(--gold)", fontWeight: 400 }}>near you</em>
              </motion.h2>
            </div>
            <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ delay: 0.3 }}>
              <Link href="/discover" style={{
                display: "flex", alignItems: "center", gap: 10, textDecoration: "none",
                color: "var(--forest)", fontSize: 13, fontWeight: 500,
                borderBottom: "1px solid var(--forest)", paddingBottom: 2,
                transition: "gap 0.2s",
              }}
              onMouseEnter={e => (e.currentTarget.style.gap = "16px")}
              onMouseLeave={e => (e.currentTarget.style.gap = "10px")}>
                Browse all
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </Link>
            </motion.div>
          </div>

          {/* Business cards — magazine-style layout */}
          {loading ? (
            <div className="biz-grid-3" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20 }}>
              {[1,2,3].map(i => <div key={i} className="sk" style={{ height: 280, borderRadius: 16 }} />)}
            </div>
          ) : bizList.length === 0 ? (
            <div style={{ textAlign: "center", padding: "80px 0" }}>
              <p style={{ fontFamily: "var(--font-serif)", fontSize: 24, color: "var(--forest)", fontWeight: 300, marginBottom: 16 }}>No businesses yet</p>
              <Link href="/auth/register" className="btn btn-primary">List your business</Link>
            </div>
          ) : (
            <div className="biz-grid-3" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20 }}>
              {bizList.map((biz, i) => (
                <motion.div key={biz.id}
                  initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-40px" }} transition={{ delay: i * 0.1, duration: 0.6, ease: [0.16,1,0.3,1] }}>
                  <BusinessCard business={biz} school={schoolMap[biz.school_id]} category={catMap[biz.category_id]} />
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          CATEGORIES — Horizontal scroll, architectural
      ═══════════════════════════════════════════ */}
      <section style={{ background: "white", borderTop: "1px solid rgba(26,58,42,0.06)", padding: "80px 0" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 6vw" }}>
          <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 36 }}>
            <div>
              <p className="eyebrow" style={{ marginBottom: 10 }}>Categories</p>
              <h2 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: "clamp(26px,3.5vw,38px)", color: "var(--forest)", letterSpacing: "-0.025em" }}>What do you need?</h2>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(148px, 1fr))", gap: 10 }}>
            {(cats.length ? cats : ["Graphic Design","Photography","Baking","Tutoring","Hair Styling","Programming","Tailoring","Music","Electronics Repair","Event Decoration","Barber Services","Printing"].map((n,i)=>({id:String(i),name:n,slug:n,description:null,icon_url:null,display_order:i}))).map((cat, i) => (
              <motion.button key={cat.id}
                initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ delay: i * 0.025, duration: 0.4 }}
                onClick={() => router.push(cats.length ? `/discover?category_id=${cat.id}` : `/discover?keyword=${cat.name}`)}
                style={{
                  padding: "16px 14px", background: "var(--cream)", border: "1px solid rgba(26,58,42,0.08)",
                  borderRadius: 12, textAlign: "left", cursor: "pointer",
                  fontFamily: "var(--font-sans)", fontSize: 13, fontWeight: 500, color: "var(--forest)",
                  transition: "all 0.2s cubic-bezier(0.16,1,0.3,1)",
                  boxShadow: "0 1px 2px rgba(26,58,42,0.04)",
                }}
                onMouseEnter={e => { const el = e.currentTarget; el.style.background = "var(--forest)"; el.style.color = "var(--cream)"; el.style.transform = "translateY(-2px)"; el.style.boxShadow = "0 8px 24px rgba(26,58,42,0.18)"; el.style.borderColor = "var(--forest)"; }}
                onMouseLeave={e => { const el = e.currentTarget; el.style.background = "var(--cream)"; el.style.color = "var(--forest)"; el.style.transform = ""; el.style.boxShadow = "0 1px 2px rgba(26,58,42,0.04)"; el.style.borderColor = "rgba(26,58,42,0.08)"; }}>
                {cat.name}
              </motion.button>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          CTA — Full bleed, confident
      ═══════════════════════════════════════════ */}
      <section style={{ position: "relative", background: "var(--forest)", padding: "100px 6vw", overflow: "hidden" }}>
        <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle, rgba(201,168,76,0.055) 1px, transparent 1px)", backgroundSize: "28px 28px", pointerEvents: "none" }} />
        <div style={{ position: "absolute", bottom: -80, right: "5%", width: 400, height: 400, borderRadius: "50%", border: "1px solid rgba(201,168,76,0.07)", pointerEvents: "none" }} />
        <div style={{ position: "absolute", bottom: -40, right: "10%", width: 240, height: 240, borderRadius: "50%", border: "1px solid rgba(201,168,76,0.1)", pointerEvents: "none" }} />

        <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.8, ease: [0.16,1,0.3,1] }}
          style={{ maxWidth: 600, position: "relative" }}>
          <p className="eyebrow" style={{ color: "rgba(201,168,76,0.65)", marginBottom: 20 }}>For students</p>
          <h2 style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontWeight: 300, fontSize: "clamp(38px, 6vw, 64px)", color: "var(--cream)", letterSpacing: "-0.03em", lineHeight: 1.0, marginBottom: 20 }}>
            Show Malawi<br />what you do.
          </h2>
          <p style={{ color: "rgba(247,244,239,0.42)", fontSize: 15, lineHeight: 1.8, marginBottom: 40, maxWidth: 440 }}>
            Free for student entrepreneurs. Verified by your university. Reach customers across campus and beyond — always.
          </p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Link href="/auth/register" style={{
              display: "inline-flex", alignItems: "center", gap: 8, textDecoration: "none",
              background: "var(--gold)", color: "#0D2118",
              fontWeight: 700, fontSize: 14, padding: "13px 28px", borderRadius: 10,
              fontFamily: "var(--font-sans)", transition: "all 0.15s",
            }}
            onMouseEnter={e => { e.currentTarget.style.background = "#A8882E"; e.currentTarget.style.transform = "translateY(-1px)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "var(--gold)"; e.currentTarget.style.transform = ""; }}>
              List your business — free
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </Link>
            <Link href="/discover" style={{
              display: "inline-flex", alignItems: "center", gap: 8, textDecoration: "none",
              background: "transparent", color: "rgba(247,244,239,0.6)",
              border: "1px solid rgba(247,244,239,0.15)",
              fontWeight: 500, fontSize: 14, padding: "13px 24px", borderRadius: 10,
              fontFamily: "var(--font-sans)", transition: "all 0.15s",
            }}
            onMouseEnter={e => { e.currentTarget.style.background = "rgba(247,244,239,0.06)"; e.currentTarget.style.color = "rgba(247,244,239,0.9)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(247,244,239,0.6)"; }}>
              Browse businesses
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer style={{ background: "#080F0A", padding: "28px 6vw" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <span style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontWeight: 700, color: "rgba(247,244,239,0.4)", fontSize: 18 }}>umatani</span>
          <div style={{ display: "flex", gap: 24 }}>
            {[["Discover","/discover"],["Register","/auth/register"],["Sign in","/auth/login"]].map(([l,h]) => (
              <Link key={h} href={h} style={{ color: "rgba(247,244,239,0.25)", fontSize: 12, textDecoration: "none", transition: "color 0.15s" }}
              onMouseEnter={e => (e.currentTarget.style.color = "rgba(247,244,239,0.6)")}
              onMouseLeave={e => (e.currentTarget.style.color = "rgba(247,244,239,0.25)")}>{l}</Link>
            ))}
          </div>
          <span style={{ fontSize: 11, color: "rgba(247,244,239,0.15)" }}>© {new Date().getFullYear()} UMATANI · Malawi</span>
        </div>
      </footer>
    </div>
  );
}
