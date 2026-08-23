"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useReferenceData } from "@/lib/referenceData";

// --- Team ---------------------------------------------------------------
interface TeamMember {
  name: string;
  alias?: string;
  role: string;
  bio?: string;
  photo_url?: string;
}
const TEAM: TeamMember[] = [
  {
    name: "Morrice Nkhoma",
    role: "Co-founder & CEO",
    bio: "Final-year Information Systems student at MUBAS, and founder of YazaIT Malawi, which offers top-notch university lessons. Passionate about academics and helping students in every way he can — one of the minds behind Umata?.",
  },
  {
    name: "Kingsley Chideru",
    alias: "Rasta Kadema",
    role: "Co-founder & CTO",
    bio: "Software developer and final-year Information Technology student. Founder of Chezax Malawi, a platform providing enterprise communication for institutions, and the developer behind Umata?.",
  },
];

const PALETTES = [
  { bg: "var(--forest-100)", text: "var(--forest)" },
  { bg: "#F5EBDF", text: "#8A6A2E" },
  { bg: "#EAF2EC", text: "#2F6B45" },
];
const pal = (name: string) => PALETTES[name.charCodeAt(0) % PALETTES.length];
const initials = (name: string) => name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);

export default function AboutPage() {
  const { categories: cats, schools } = useReferenceData();
  const [bizTotal, setBizTotal] = useState<number | null>(null);

  useEffect(() => {
    api.businesses.search({ limit: 1 }).then(b => setBizTotal(b.total)).catch(() => {});
  }, []);

  const stats = [
    [bizTotal === null ? "—" : String(bizTotal), "Verified businesses"],
    [cats.length === 0 ? "—" : String(cats.length), "Service categories"],
    [schools.length === 0 ? "—" : String(schools.length), "Universities"],
  ];

  return (
    <div style={{ minHeight: "100vh", background: "var(--cream)" }}>
      {/* Intro */}
      <section style={{ padding: "72px 24px 56px" }}>
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <p className="eyebrow" style={{ marginBottom: 12 }}>About</p>
            <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: "clamp(34px,5vw,52px)", color: "var(--forest)", letterSpacing: "-0.025em", lineHeight: 1.05, marginBottom: 20 }}>
              A place for Malawian students to <span style={{ fontWeight: 800 }}>show what they do.</span>
            </h1>
            <p style={{ fontSize: 15, color: "var(--ink-muted)", lineHeight: 1.8, maxWidth: 560 }}>
              Every campus has students quietly running real businesses between classes — designers, photographers, bakers, tutors, developers, tailors. Most of that work never travels further than a WhatsApp status. Umata? exists to give it an actual address: a place people can search, trust, and reach out to directly.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Name origin */}
      <section style={{ padding: "0 24px 56px" }}>
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          <motion.div initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }}
            style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, padding: "32px 28px", display: "flex", gap: 20, alignItems: "flex-start" }}>
            <span style={{ fontFamily: "var(--font-serif)", fontWeight: 800, fontSize: 40, color: "var(--gold-dark)", lineHeight: 1, flexShrink: 0 }}>"</span>
            <div>
              <p style={{ fontFamily: "var(--font-serif)", fontSize: 20, color: "var(--forest)", lineHeight: 1.5, marginBottom: 12 }}>
                <em>Umata?</em> is Chichewa for <strong>"what do you do?"</strong>
              </p>
              <p style={{ fontSize: 14, color: "var(--ink-muted)", lineHeight: 1.75 }}>
                It's the question every student entrepreneur gets asked constantly, and rarely has a good way to answer beyond "let me send you a picture." We built this so the answer could be a link instead.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section style={{ padding: "0 24px 64px" }}>
        <div style={{ maxWidth: 720, margin: "0 auto", display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 1, background: "var(--border)", border: "1px solid var(--border)", borderRadius: 2, overflow: "hidden" }}>
          {stats.map(([n, l]) => (
            <div key={l} style={{ background: "white", padding: "24px 16px", textAlign: "center" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontWeight: 500, fontSize: 26, color: "var(--forest)", lineHeight: 1, marginBottom: 6 }}>{n}</div>
              <div style={{ fontSize: 11, color: "var(--ink-faint)", letterSpacing: "0.06em", textTransform: "uppercase" }}>{l}</div>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section style={{ padding: "0 24px 72px" }}>
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          <p className="eyebrow" style={{ marginBottom: 14 }}>How it works</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
            {[
              ["Verify with a school email", "Sign up with your university email and student ID — that's what keeps every listing tied to a real, currently-enrolled student, not an anonymous account."],
              ["List what you do", "Add your services, a few photos of your work, and how people can reach you. Free, no listing fees, no commission on what you earn."],
              ["Get found", "Visitors browse by category or university and reach out directly on WhatsApp — no middleman, no messages routed through us."],
            ].map(([title, body], i) => (
              <motion.div key={title} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5, delay: i * 0.08 }}
                style={{ display: "flex", gap: 20, padding: "20px 0", borderBottom: i < 2 ? "1px solid var(--border)" : "none" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--gold-dark)", fontWeight: 500, flexShrink: 0, paddingTop: 2 }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <p style={{ fontSize: 15, fontWeight: 600, color: "var(--forest)", marginBottom: 4 }}>{title}</p>
                  <p style={{ fontSize: 13.5, color: "var(--ink-muted)", lineHeight: 1.7 }}>{body}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section style={{ padding: "0 24px 88px" }}>
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          <p className="eyebrow" style={{ marginBottom: 12 }}>Behind the system</p>
          <h2 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: "clamp(26px,3.5vw,34px)", color: "var(--forest)", letterSpacing: "-0.02em", marginBottom: 14 }}>
            Built by students, for students.
          </h2>
          <p style={{ fontSize: 14, color: "var(--ink-muted)", lineHeight: 1.75, marginBottom: TEAM.length ? 32 : 0, maxWidth: 500 }}>
            Umata? is made and run by a small team based in Malawi — the same students it's built for.
          </p>

          {TEAM.length > 0 && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 24 }}>
              {TEAM.map(member => {
                const c = pal(member.name);
                return (
                  <div key={member.name} className="team-card" style={{
                    background: "white", border: "1px solid var(--border)", borderRadius: 2,
                    padding: "32px 28px", position: "relative", overflow: "hidden",
                    transition: "transform 0.2s ease, box-shadow 0.2s ease",
                  }}>
                    {/* Large faded serif initial in the corner — same quote-mark
                        motif as the name-origin card above, so the team section
                        reads as part of one considered page rather than a plain
                        directory box tacked on the end. */}
                    <span style={{
                      position: "absolute", top: -6, right: 10, fontFamily: "var(--font-serif)",
                      fontWeight: 800, fontSize: 96, lineHeight: 1, color: c.bg,
                      userSelect: "none", pointerEvents: "none",
                    }}>
                      {member.name[0]}
                    </span>

                    <div style={{ position: "relative", display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
                      <div style={{
                        width: 72, height: 72, borderRadius: "50%", flexShrink: 0,
                        background: member.photo_url ? "var(--cream)" : c.bg, color: c.text,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 24,
                        overflow: "hidden", position: "relative",
                        border: "3px solid var(--cream)", boxShadow: "0 0 0 1px var(--border)",
                      }}>
                        {member.photo_url
                          ? <Image src={member.photo_url} alt="" fill sizes="72px" style={{ objectFit: "cover" }} />
                          : initials(member.name)}
                      </div>
                      <div>
                        <p style={{ fontFamily: "var(--font-serif)", fontSize: 19, fontWeight: 700, color: "var(--forest)", lineHeight: 1.25 }}>
                          {member.name}
                        </p>
                        {member.alias && (
                          <p style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: 13, color: "var(--ink-faint)", marginTop: 1 }}>
                            "{member.alias}"
                          </p>
                        )}
                        <span className="badge badge-gold" style={{ marginTop: 7, display: "inline-block" }}>{member.role}</span>
                      </div>
                    </div>

                    {member.bio && (
                      <p style={{ position: "relative", fontSize: 13.5, color: "var(--ink-muted)", lineHeight: 1.75 }}>{member.bio}</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* CTA */}
      <section style={{ background: "var(--forest)", padding: "64px 24px" }}>
        <div style={{ maxWidth: 640, margin: "0 auto", textAlign: "center" }}>
          <h2 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: "clamp(26px,4vw,38px)", color: "var(--cream)", letterSpacing: "-0.025em", marginBottom: 16 }}>
            Running something on campus? <span style={{ fontWeight: 800 }}>Umata?</span>
          </h2>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/auth/register" style={{
              display: "inline-flex", alignItems: "center", gap: 8, textDecoration: "none",
              background: "var(--cream)", color: "var(--forest)",
              fontWeight: 700, fontSize: 14, padding: "13px 28px", borderRadius: 2,
              fontFamily: "var(--font-sans)",
            }}>
              List your business, free
            </Link>
            <Link href="/discover" style={{
              display: "inline-flex", alignItems: "center", gap: 8, textDecoration: "none",
              background: "transparent", color: "rgba(250,243,231,0.7)",
              border: "1px solid rgba(250,243,231,0.2)",
              fontWeight: 600, fontSize: 14, padding: "13px 24px", borderRadius: 2,
              fontFamily: "var(--font-sans)",
            }}>
              Browse businesses
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
