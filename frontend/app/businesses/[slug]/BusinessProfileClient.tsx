"use client";
import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useReferenceData } from "@/lib/referenceData";
import { Skeleton } from "@/components/ui/Skeleton";
import { ShareButton } from "@/components/ui/ShareButton";
import { formatDate } from "@/lib/utils";
import type { Business, PortfolioItem } from "@/types";

const PALETTES = [
  { bg: "#F5EBDF", text: "#43081F" }, { bg: "#EDE0D3", text: "#5C1129" },
  { bg: "#F0E4D3", text: "#2B0512" },
];
const pal = (name: string) => PALETTES[name.charCodeAt(0) % PALETTES.length];
const initials = (name: string) => name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);

// These fields are free text on the backend (no format enforced), so an
// owner might type "@handle" or a full profile URL either way. Build a
// working link regardless: pass full URLs through untouched, otherwise
// treat it as a handle and prepend the platform's base URL.
const SOCIAL_BASE: Record<string, string> = {
  instagram: "https://instagram.com/",
  twitter: "https://x.com/",
  facebook: "https://facebook.com/",
  tiktok: "https://tiktok.com/@",
};
const socialUrl = (platform: keyof typeof SOCIAL_BASE, value: string) => {
  if (/^https?:\/\//i.test(value)) return value;
  return SOCIAL_BASE[platform] + value.replace(/^@/, "");
};

export default function BusinessProfileClient() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const { user } = useAuth();

  const { schoolById, categoryById } = useReferenceData();
  const [biz,      setBiz]      = useState<Business | null>(null);
  const [loading,  setLoading]  = useState(true);
  const [tab,      setTab]      = useState<"about"|"portfolio">("about");

  const [showReport, setShowReport] = useState(false);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [reportReason, setReportReason] = useState("");
  const [reportDetails, setReportDetails] = useState("");
  const [reportHoneypot, setReportHoneypot] = useState(""); // spam trap — see form below
  const [reportSubmitting, setReportSubmitting] = useState(false);
  const [reportError, setReportError] = useState("");
  const [reportDone, setReportDone] = useState(false);

  useEffect(() => {
    if (!slug) return;
    api.businesses.getBySlug(slug as string)
      .then(b => setBiz(b))
      .catch(() => router.push("/discover"))
      .finally(() => setLoading(false));
  }, [slug]);

  const school = biz ? schoolById(biz.school_id) ?? null : null;
  const category = biz ? categoryById(biz.category_id) ?? null : null;

  const submitReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (reportHoneypot) return; // a real person never sees or fills this field
    if (reportReason.trim().length < 5) { setReportError("Please give a brief reason (at least 5 characters)."); return; }
    if (!biz) return;
    setReportSubmitting(true); setReportError("");
    try {
      await api.support.createReport({
        report_type: "business",
        target_id: biz.id,
        reason: reportReason.trim(),
        details: reportDetails.trim() || undefined,
      });
      setReportDone(true);
    } catch (e: any) {
      setReportError(e.message ?? "Could not submit report. Try again.");
    } finally {
      setReportSubmitting(false);
    }
  };

  if (loading) return <ProfileSkeleton />;
  if (!biz)    return null;

  const color = pal(biz.name);
  const isOwner = user?.id === (biz as any).owner_id;

  return (
    <div style={{ minHeight: "100vh", background: "var(--cream)" }}>
      {/* Utility bar — back + share live here, in the page's own background,
          instead of floating on top of a cover photo where legibility and
          hit-target size depend on whatever image an owner uploads. */}
      <div style={{ maxWidth: 960, margin: "0 auto", padding: "16px 24px 12px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <button onClick={() => router.back()} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ink-muted)", fontSize: 13, fontFamily: "var(--font-sans)", display: "flex", alignItems: "center", gap: 6, padding: "6px 4px", transition: "color 0.15s" }}
        onMouseEnter={e => (e.currentTarget.style.color = "var(--forest)")}
        onMouseLeave={e => (e.currentTarget.style.color = "var(--ink-muted)")}>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M7.5 2L3.5 6l4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Back
        </button>
        <ShareButton
          title={biz.name}
          text={`Check out ${biz.name} on Umata?`}
          url={typeof window !== "undefined" ? window.location.href : `https://umatani.vercel.app/businesses/${biz.slug}`}
        />
      </div>

      {/* Cover bar */}
      <div style={{ height: 220, background: "var(--forest)", position: "relative", overflow: "hidden" }}>
        {biz.cover_url ? (
          <Image
            src={biz.cover_url}
            alt=""
            fill
            priority
            sizes="100vw"
            style={{ objectFit: "cover" }}
          />
        ) : (
          <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle, rgba(250,243,231,0.08) 1px, transparent 1px)", backgroundSize: "24px 24px" }} />
        )}
      </div>

      <div style={{ maxWidth: 960, margin: "0 auto", padding: "0 24px" }}>
        {/* Logo + header. Only the logo overlaps the cover (a fixed, bounded
            36px via its own offset) — the title never does, so a long or
            wrapping business name can't end up rendered partly over the
            photo where it'd be hard to read. */}
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginTop: 16, marginBottom: 28, flexWrap: "wrap", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 16 }}>
            <div style={{
              width: 72, height: 72, borderRadius: 2,
              background: biz.logo_url ? "var(--cream)" : color.bg, color: color.text,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 26,
              border: "3px solid var(--cream)", flexShrink: 0, boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
              overflow: "hidden", position: "relative", top: -36, marginBottom: -36,
            }}>
              {biz.logo_url
                ? <Image src={biz.logo_url} alt="" fill priority sizes="72px" style={{ objectFit: "cover" }} />
                : initials(biz.name)}
            </div>
            <div style={{ paddingBottom: 4 }}>
              <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 400, fontSize: "clamp(22px,4vw,34px)", color: "var(--forest)", marginBottom: 4, letterSpacing: "-0.02em" }}>{biz.name}</h1>
              <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
                {category && <span className="badge badge-gold">{category.name}</span>}
                {school && <span style={{ fontSize: 12, color: "var(--ink-faint)", display: "flex", alignItems: "center", gap: 4 }}>
                  <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M8 2C5.79 2 4 3.79 4 6c0 3.5 4 8 4 8s4-4.5 4-8c0-2.21-1.79-4-4-4zm0 5.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3z" fill="var(--ink-faint)"/></svg>
                  {school.name} · {school.city}
                </span>}
              </div>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <span className={`status-tag ${biz.is_available ? "is-open" : "is-closed"}`}>
              {biz.is_available ? "Available" : "Busy"}
            </span>
            {isOwner && <Link href="/dashboard" style={{ fontSize: 12.5, padding: "7px 16px" }} className="btn btn-gold">Edit profile</Link>}
          </div>
        </div>

        <div className="biz-detail-grid" style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 28, alignItems: "start" }}>
          {/* Left */}
          <div className="biz-detail-main">
            {/* Tabs */}
            <div style={{ display: "flex", gap: 0, borderBottom: "1px solid var(--border)", marginBottom: 28 }}>
              {(["about","portfolio"] as const).map(t => (
                <button key={t} onClick={() => setTab(t)} style={{
                  padding: "10px 18px", fontSize: 13.5, fontWeight: 500,
                  background: "none", border: "none", cursor: "pointer",
                  color: tab === t ? "var(--forest)" : "var(--ink-faint)",
                  borderBottom: tab === t ? "2px solid var(--forest)" : "2px solid transparent",
                  marginBottom: -1, transition: "color 0.15s", textTransform: "capitalize",
                  fontFamily: "var(--font-sans)",
                }}>
                  {t}
                  {t === "portfolio" && biz.portfolio_items.length > 0 && <span style={{ marginLeft: 6, fontSize: 11, background: "#F1F3F5", color: "var(--ink-faint)", padding: "1px 6px", borderRadius: 100 }}>{biz.portfolio_items.length}</span>}
                </button>
              ))}
            </div>

            {/* About */}
            {tab === "about" && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                <p className="eyebrow" style={{ marginBottom: 12 }}>About</p>
                <p style={{ fontSize: 14.5, color: "var(--ink-muted)", lineHeight: 1.8, whiteSpace: "pre-line", marginBottom: 36 }}>{biz.description}</p>
                {biz.services.length > 0 && (
                  <>
                    <p className="eyebrow" style={{ marginBottom: 14 }}>Services</p>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {biz.services.map(svc => (
                        <div key={svc.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 16px", background: "white", borderRadius: 2, border: "1px solid var(--border)" }}>
                          <div>
                            <p style={{ fontWeight: 500, fontSize: 13.5, color: "var(--forest)", marginBottom: svc.description ? 2 : 0 }}>{svc.name}</p>
                            {svc.description && <p style={{ fontSize: 12, color: "var(--ink-faint)" }}>{svc.description}</p>}
                          </div>
                          {svc.price_range && <span style={{ fontSize: 12, fontWeight: 500, color: "var(--gold-dark)", background: "var(--gold-light)", padding: "4px 10px", borderRadius: 2, flexShrink: 0, marginLeft: 12 }}>{svc.price_range}</span>}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </motion.div>
            )}

            {/* Portfolio */}
            {tab === "portfolio" && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                {biz.portfolio_items.length === 0
                  ? <EmptyState text="No portfolio items yet" />
                  : <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12 }}>
                      {biz.portfolio_items.map(item => {
                        const imageItems = biz.portfolio_items.filter(i => i.item_type === "image");
                        const imageIndex = imageItems.findIndex(i => i.id === item.id);
                        return (
                        <div key={item.id} className="portfolio-tile" style={{ aspectRatio: "1", borderRadius: 2, overflow: "hidden", background: "var(--forest-100)", border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center", position: "relative", transition: "box-shadow 0.2s, transform 0.2s", cursor: item.item_type === "image" ? "pointer" : "default" }}
                          onClick={() => { if (item.item_type === "image") setLightboxIndex(imageIndex); }}>
                          {item.item_type === "image"
                            ? <>
                                <Image src={item.display_url} alt={item.caption ?? ""} fill sizes="(max-width: 640px) 50vw, 200px" style={{ objectFit: "cover" }} />
                                <div className="portfolio-tile-zoom" style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(33,4,16,0)", transition: "background 0.15s" }}>
                                  <svg width="22" height="22" viewBox="0 0 20 20" fill="none" className="portfolio-tile-zoom-icon" style={{ opacity: 0, transition: "opacity 0.15s" }}>
                                    <circle cx="8.5" cy="8.5" r="6" stroke="white" strokeWidth="1.6"/><path d="M13 13l4 4" stroke="white" strokeWidth="1.6" strokeLinecap="round"/>
                                    <path d="M8.5 6v5M6 8.5h5" stroke="white" strokeWidth="1.4" strokeLinecap="round"/>
                                  </svg>
                                </div>
                                {item.caption && (
                                  <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, padding: "18px 10px 8px", background: "linear-gradient(0deg, rgba(33,4,16,0.75), transparent)" }}>
                                    <p style={{ fontSize: 11.5, color: "var(--cream)", lineHeight: 1.3 }} className="lc-1">{item.caption}</p>
                                  </div>
                                )}
                              </>
                            : <a href={item.display_url} target="_blank" rel="noopener" style={{ textDecoration: "none", display: "flex", flexDirection: "column", alignItems: "center", gap: 6, color: "var(--forest-600)", padding: 16, textAlign: "center" }}>
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M11 3H17V9M17 3L9 11M8 4H4C3.45 4 3 4.45 3 5V16C3 16.55 3.45 17 4 17H15C15.55 17 16 16.55 16 16V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                                <span style={{ fontSize: 11 }}>{item.caption ?? "Link"}</span>
                              </a>
                          }
                        </div>
                        );
                      })}
                    </div>
                }
              </motion.div>
            )}

            {lightboxIndex !== null && (
              <PortfolioLightbox
                items={biz.portfolio_items.filter(i => i.item_type === "image")}
                index={lightboxIndex}
                onClose={() => setLightboxIndex(null)}
                onNavigate={setLightboxIndex}
              />
            )}

          </div>

          {/* Right — contact sidebar */}
          <div className="biz-detail-sidebar" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, padding: 18 }}>
              <p className="eyebrow" style={{ marginBottom: 14 }}>Contact</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {biz.whatsapp && (
                  <a href={`https://wa.me/${biz.whatsapp.replace(/\D/g,"")}`} target="_blank" rel="noopener" className="btn btn-primary" style={{ width: "100%", justifyContent: "center", fontSize: 13.5, gap: 8 }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                    WhatsApp
                  </a>
                )}
                {biz.phone && (
                  <a href={`tel:${biz.phone}`} className="btn btn-outline" style={{ width: "100%", justifyContent: "center", fontSize: 13.5 }}>
                    {biz.phone}
                  </a>
                )}
                {biz.contact_email && (
                  <a href={`mailto:${biz.contact_email}`} style={{ fontSize: 13, color: "var(--ink-muted)", textDecoration: "none", display: "flex", alignItems: "center", gap: 7, padding: "6px 2px" }}
                  onMouseEnter={e => (e.currentTarget.style.color = "var(--forest)")}
                  onMouseLeave={e => (e.currentTarget.style.color = "var(--ink-muted)")}>
                    <svg width="14" height="14" viewBox="0 0 20 20" fill="none"><path d="M3 5h14l-7 6-7-6zm0 0v10h14V5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    {biz.contact_email}
                  </a>
                )}
                {biz.website && (
                  <a href={biz.website} target="_blank" rel="noopener" style={{ fontSize: 13, color: "var(--ink-muted)", textDecoration: "none", display: "flex", alignItems: "center", gap: 7, padding: "6px 2px" }}
                  onMouseEnter={e => (e.currentTarget.style.color = "var(--forest)")}
                  onMouseLeave={e => (e.currentTarget.style.color = "var(--ink-muted)")}>
                    <svg width="14" height="14" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5"/><path d="M2 10h16M10 2c-2 3-3 5.5-3 8s1 5 3 8M10 2c2 3 3 5.5 3 8s-1 5-3 8" stroke="currentColor" strokeWidth="1.5"/></svg>
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{biz.website.replace(/^https?:\/\//, "")}</span>
                  </a>
                )}
              </div>

              {(biz.instagram || biz.twitter || biz.facebook || biz.tiktok) && (
                <div style={{ display: "flex", gap: 8, marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
                  {biz.instagram && (
                    <a href={socialUrl("instagram", biz.instagram)} target="_blank" rel="noopener" aria-label="Instagram"
                      style={{ width: 32, height: 32, borderRadius: 2, border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--ink-muted)", transition: "color 0.15s, border-color 0.15s" }}
                      onMouseEnter={e => { e.currentTarget.style.color = "var(--forest)"; e.currentTarget.style.borderColor = "var(--forest-400)"; }}
                      onMouseLeave={e => { e.currentTarget.style.color = "var(--ink-muted)"; e.currentTarget.style.borderColor = "var(--border)"; }}>
                      <svg width="15" height="15" viewBox="0 0 20 20" fill="none"><rect x="2.5" y="2.5" width="15" height="15" rx="4" stroke="currentColor" strokeWidth="1.5"/><circle cx="10" cy="10" r="3.5" stroke="currentColor" strokeWidth="1.5"/><circle cx="14.2" cy="5.8" r="1" fill="currentColor"/></svg>
                    </a>
                  )}
                  {biz.twitter && (
                    <a href={socialUrl("twitter", biz.twitter)} target="_blank" rel="noopener" aria-label="Twitter / X"
                      style={{ width: 32, height: 32, borderRadius: 2, border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--ink-muted)", transition: "color 0.15s, border-color 0.15s" }}
                      onMouseEnter={e => { e.currentTarget.style.color = "var(--forest)"; e.currentTarget.style.borderColor = "var(--forest-400)"; }}
                      onMouseLeave={e => { e.currentTarget.style.color = "var(--ink-muted)"; e.currentTarget.style.borderColor = "var(--border)"; }}>
                      <svg width="13" height="13" viewBox="0 0 20 20" fill="none"><path d="M2 2l7 8.5L2.4 18h2l6-6.9 4.6 6.9h3l-7.3-9L17.6 2h-2l-5.6 6.4L4.9 2H2z" fill="currentColor"/></svg>
                    </a>
                  )}
                  {biz.facebook && (
                    <a href={socialUrl("facebook", biz.facebook)} target="_blank" rel="noopener" aria-label="Facebook"
                      style={{ width: 32, height: 32, borderRadius: 2, border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--ink-muted)", transition: "color 0.15s, border-color 0.15s" }}
                      onMouseEnter={e => { e.currentTarget.style.color = "var(--forest)"; e.currentTarget.style.borderColor = "var(--forest-400)"; }}
                      onMouseLeave={e => { e.currentTarget.style.color = "var(--ink-muted)"; e.currentTarget.style.borderColor = "var(--border)"; }}>
                      <svg width="14" height="14" viewBox="0 0 20 20" fill="none"><path d="M12.5 3h-2A3.5 3.5 0 007 6.5V9H5v3h2v6h3v-6h2.5l.5-3H10V6.75c0-.69.56-.75 1-.75h1.5V3z" fill="currentColor"/></svg>
                    </a>
                  )}
                  {biz.tiktok && (
                    <a href={socialUrl("tiktok", biz.tiktok)} target="_blank" rel="noopener" aria-label="TikTok"
                      style={{ width: 32, height: 32, borderRadius: 2, border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--ink-muted)", transition: "color 0.15s, border-color 0.15s" }}
                      onMouseEnter={e => { e.currentTarget.style.color = "var(--forest)"; e.currentTarget.style.borderColor = "var(--forest-400)"; }}
                      onMouseLeave={e => { e.currentTarget.style.color = "var(--ink-muted)"; e.currentTarget.style.borderColor = "var(--border)"; }}>
                      <svg width="14" height="14" viewBox="0 0 20 20" fill="none"><path d="M14.5 2.5c.35 2 1.6 3.3 3.5 3.5v2.6a6.3 6.3 0 01-3.5-1.1v5.6a4.6 4.6 0 11-4-4.55v2.7a2 2 0 102.4 1.95V2.5h1.6z" fill="currentColor"/></svg>
                    </a>
                  )}
                </div>
              )}
            </div>

            <div style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, padding: 16 }}>
              <p style={{ fontSize: 11, color: "var(--ink-faint)", marginBottom: 4 }}>Member since</p>
              <p style={{ fontSize: 13, fontWeight: 500, color: "var(--forest)" }}>{formatDate(biz.created_at)}</p>
            </div>

            <button onClick={() => setShowReport(true)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, color: "var(--ink-faint)", padding: "8px 0", transition: "color 0.15s" }}
            onMouseEnter={e => (e.currentTarget.style.color = "#C53030")}
            onMouseLeave={e => (e.currentTarget.style.color = "var(--ink-faint)")}>
              Report this business
            </button>
          </div>
        </div>
      </div>

      {/* Report modal */}
      {showReport && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(33,4,16,0.5)", zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}
          onClick={() => !reportSubmitting && setShowReport(false)}>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            onClick={e => e.stopPropagation()}
            style={{ background: "white", borderRadius: 2, padding: 28, maxWidth: 420, width: "100%" }}>
            {reportDone ? (
              <>
                <h3 style={{ fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 20, color: "var(--forest)", marginBottom: 10 }}>Report submitted</h3>
                <p style={{ fontSize: 13.5, color: "var(--ink-muted)", lineHeight: 1.7, marginBottom: 20 }}>
                  Thanks for flagging this. An admin will review it shortly.
                </p>
                <button onClick={() => { setShowReport(false); setReportDone(false); setReportReason(""); setReportDetails(""); }} className="btn btn-outline" style={{ width: "100%", justifyContent: "center" }}>
                  Close
                </button>
              </>
            ) : (
              <form onSubmit={submitReport}>
                <h3 style={{ fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 20, color: "var(--forest)", marginBottom: 4 }}>Report this business</h3>
                <p style={{ fontSize: 12.5, color: "var(--ink-faint)", marginBottom: 18 }}>Tell us what's wrong. Reports are reviewed by an admin.</p>

                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--forest)", marginBottom: 6 }}>Reason *</label>
                <input value={reportReason} onChange={e => setReportReason(e.target.value)} placeholder="e.g. Scam, fake listing, inappropriate content" className="input" style={{ marginBottom: 14 }} maxLength={255} required />

                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--forest)", marginBottom: 6 }}>Additional details (optional)</label>
                <textarea value={reportDetails} onChange={e => setReportDetails(e.target.value)} rows={3} maxLength={2000} className="input" style={{ resize: "none", marginBottom: 14 }} placeholder="Anything else that would help us look into this" />

                {/* Honeypot — invisible to real users, styled off-screen
                    rather than display:none (some bots skip hidden fields
                    but still fill visually-offscreen ones, so this one's
                    positioned off-canvas instead). Any value here means
                    it was filled by an automated script, not a person. */}
                <input
                  type="text"
                  name="website"
                  value={reportHoneypot}
                  onChange={e => setReportHoneypot(e.target.value)}
                  tabIndex={-1}
                  autoComplete="off"
                  style={{ position: "absolute", left: "-9999px", width: 1, height: 1, opacity: 0 }}
                  aria-hidden="true"
                />

                {reportError && <p style={{ fontSize: 12.5, color: "#C53030", marginBottom: 14 }}>{reportError}</p>}

                <div style={{ display: "flex", gap: 10 }}>
                  <button type="button" onClick={() => setShowReport(false)} className="btn btn-outline" style={{ flex: 1, justifyContent: "center" }}>Cancel</button>
                  <button type="submit" disabled={reportSubmitting} className="btn btn-primary" style={{ flex: 1, justifyContent: "center" }}>
                    {reportSubmitting ? "Submitting…" : "Submit report"}
                  </button>
                </div>
              </form>
            )}
          </motion.div>
        </div>
      )}
    </div>
  );
}

function PortfolioLightbox({
  items, index, onClose, onNavigate,
}: {
  items: PortfolioItem[]; index: number;
  onClose: () => void; onNavigate: (i: number) => void;
}) {
  const item = items[index];
  const hasMultiple = items.length > 1;

  useEffect(() => {
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight" && hasMultiple) onNavigate((index + 1) % items.length);
      if (e.key === "ArrowLeft" && hasMultiple) onNavigate((index - 1 + items.length) % items.length);
    };
    window.addEventListener("keydown", handleKey);
    return () => { document.body.style.overflow = prevOverflow; window.removeEventListener("keydown", handleKey); };
  }, [index, items.length, hasMultiple, onClose, onNavigate]);

  if (!item) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}
        onClick={onClose}
        style={{ position: "fixed", inset: 0, zIndex: 100, background: "rgba(20,3,10,0.94)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>

        <button onClick={onClose} aria-label="Close" style={{
          position: "absolute", top: 20, right: 20, width: 40, height: 40, borderRadius: 2,
          background: "rgba(250,243,231,0.08)", border: "none", cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center", color: "var(--cream)",
        }}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M2 2l14 14M16 2L2 16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
        </button>

        {hasMultiple && (
          <>
            <button onClick={e => { e.stopPropagation(); onNavigate((index - 1 + items.length) % items.length); }} aria-label="Previous image" style={{
              position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", width: 44, height: 44, borderRadius: 2,
              background: "rgba(250,243,231,0.08)", border: "none", cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", color: "var(--cream)",
            }}>
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M11 3L5 9l6 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </button>
            <button onClick={e => { e.stopPropagation(); onNavigate((index + 1) % items.length); }} aria-label="Next image" style={{
              position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", width: 44, height: 44, borderRadius: 2,
              background: "rgba(250,243,231,0.08)", border: "none", cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", color: "var(--cream)",
            }}>
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M7 3l6 6-6 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </button>
          </>
        )}

        <motion.div
          key={item.id}
          initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.18 }}
          onClick={e => e.stopPropagation()}
          style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14, maxWidth: "min(90vw, 900px)", maxHeight: "88vh" }}>
          <div style={{ position: "relative", width: "min(90vw, 900px)", height: "min(74vh, 700px)" }}>
            <Image src={item.display_url} alt={item.caption ?? ""} fill sizes="90vw" style={{ objectFit: "contain" }} />
          </div>
          {(item.caption || hasMultiple) && (
            <div style={{ display: "flex", alignItems: "center", gap: 12, color: "rgba(250,243,231,0.75)", fontSize: 13, textAlign: "center" }}>
              {item.caption && <span>{item.caption}</span>}
              {hasMultiple && <span style={{ color: "rgba(250,243,231,0.4)" }}>{index + 1} / {items.length}</span>}
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div style={{ textAlign: "center", padding: "52px 0" }}><p style={{ fontFamily: "var(--font-serif)", fontSize: 20, color: "var(--forest)", fontWeight: 300 }}>{text}</p></div>;
}
function ProfileSkeleton() {
  return (
    <div style={{ minHeight: "100vh", background: "var(--cream)" }}>
      <div style={{ height: 220, background: "var(--forest)" }} />
      <div style={{ maxWidth: 960, margin: "0 auto", padding: "0 24px" }}>
        <div style={{ marginTop: -36, display: "flex", gap: 16, marginBottom: 28 }}>
          <Skeleton w="72px" h={72} r={16} />
          <div style={{ flex: 1 }}><Skeleton h={28} r={6} /><div style={{ marginTop: 8 }}><Skeleton w="60%" h={14} r={6} /></div></div>
        </div>
        <Skeleton h={200} r={12} />
      </div>
    </div>
  );
}
