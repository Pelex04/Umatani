"use client";
import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useReferenceData } from "@/lib/referenceData";
import { Stars } from "@/components/ui/Stars";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatDate, timeAgo } from "@/lib/utils";
import type { Business, Review } from "@/types";

const PALETTES = [
  { bg: "#F5EBDF", text: "#43081F" }, { bg: "#EDE0D3", text: "#5C1129" },
  { bg: "#F0E4D3", text: "#2B0512" },
];
const pal = (name: string) => PALETTES[name.charCodeAt(0) % PALETTES.length];
const initials = (name: string) => name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);

export default function BusinessProfile() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const { user } = useAuth();

  const { schoolById, categoryById } = useReferenceData();
  const [biz,      setBiz]      = useState<Business | null>(null);
  const [reviews,  setReviews]  = useState<Review[]>([]);
  const [revTotal, setRevTotal] = useState(0);
  const [loading,  setLoading]  = useState(true);
  const [revLoad,  setRevLoad]  = useState(false);
  const [tab,      setTab]      = useState<"about"|"portfolio"|"reviews">("about");
  const [rating,   setRating]   = useState(0);
  const [hover,    setHover]    = useState(0);
  const [comment,  setComment]  = useState("");
  const [service,  setService]  = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [revError, setRevError] = useState("");
  const [revDone,  setRevDone]  = useState(false);

  const [showReport, setShowReport] = useState(false);
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

  const loadReviews = async (off = 0) => {
    if (!biz) return;
    setRevLoad(true);
    const r = await api.reviews.list(biz.id, off, 10);
    if (off === 0) setReviews(r.items); else setReviews(prev => [...prev, ...r.items]);
    setRevTotal(r.total);
    setRevLoad(false);
  };

  useEffect(() => { if (biz && tab === "reviews") loadReviews(0); }, [biz, tab]);

  const submitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!biz || rating === 0) { setRevError("Please select a rating."); return; }
    if (comment.length < 10)  { setRevError("Comment must be at least 10 characters."); return; }
    setSubmitting(true); setRevError("");
    try {
      await api.reviews.create({ business_id: biz.id, rating, comment, service_received: service || null, photo_storage_keys: [] });
      setRevDone(true); setRating(0); setComment(""); setService("");
      loadReviews(0);
    } catch (e: any) { setRevError(e.message ?? "Could not submit review."); }
    finally { setSubmitting(false); }
  };

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
        {/* Gradient scrim so the back button / edit link stay legible over any cover photo */}
        {biz.cover_url && <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(33,4,16,0.35), rgba(33,4,16,0.05) 40%)" }} />}
        <div style={{ position: "absolute", top: 20, left: 24, display: "flex", alignItems: "center", gap: 8 }}>
          <button onClick={() => router.back()} style={{ background: "rgba(250,243,231,0.1)", border: "none", borderRadius: 2, padding: "7px 14px", cursor: "pointer", color: "rgba(250,243,231,0.7)", fontSize: 12.5, fontFamily: "var(--font-sans)", display: "flex", alignItems: "center", gap: 6, transition: "background 0.15s" }}
          onMouseEnter={e => (e.currentTarget.style.background = "rgba(250,243,231,0.16)")}
          onMouseLeave={e => (e.currentTarget.style.background = "rgba(250,243,231,0.1)")}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M7.5 2L3.5 6l4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Back
          </button>
        </div>
        {isOwner && <Link href="/dashboard" style={{ position: "absolute", top: 20, right: 24, fontSize: 12.5, padding: "7px 16px" }} className="btn btn-gold">Edit profile</Link>}
      </div>

      <div style={{ maxWidth: 960, margin: "0 auto", padding: "0 24px" }}>
        {/* Logo + header */}
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginTop: -36, marginBottom: 28, flexWrap: "wrap", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 16 }}>
            <div style={{
              width: 72, height: 72, borderRadius: 2,
              background: biz.logo_url ? "var(--cream)" : color.bg, color: color.text,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 26,
              border: "3px solid var(--cream)", flexShrink: 0, boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
              overflow: "hidden", position: "relative",
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
            <Stars rating={biz.average_rating} count={biz.review_count} size={14} />
            <span className={`status-tag ${biz.is_available ? "is-open" : "is-closed"}`}>
              {biz.is_available ? "Available" : "Busy"}
            </span>
          </div>
        </div>

        <div className="biz-detail-grid" style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 28, alignItems: "start" }}>
          {/* Left */}
          <div className="biz-detail-main">
            {/* Tabs */}
            <div style={{ display: "flex", gap: 0, borderBottom: "1px solid var(--border)", marginBottom: 28 }}>
              {(["about","portfolio","reviews"] as const).map(t => (
                <button key={t} onClick={() => setTab(t)} style={{
                  padding: "10px 18px", fontSize: 13.5, fontWeight: 500,
                  background: "none", border: "none", cursor: "pointer",
                  color: tab === t ? "var(--forest)" : "var(--ink-faint)",
                  borderBottom: tab === t ? "2px solid var(--forest)" : "2px solid transparent",
                  marginBottom: -1, transition: "color 0.15s", textTransform: "capitalize",
                  fontFamily: "var(--font-sans)",
                }}>
                  {t}
                  {t === "reviews" && revTotal > 0 && <span style={{ marginLeft: 6, fontSize: 11, background: "var(--forest-100)", color: "var(--forest-600)", padding: "1px 6px", borderRadius: 100 }}>{revTotal}</span>}
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
                  : <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 10 }}>
                      {biz.portfolio_items.map(item => (
                        <div key={item.id} style={{ aspectRatio: "1", borderRadius: 2, overflow: "hidden", background: "var(--forest-100)", border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
                          {item.item_type === "image"
                            ? <Image src={item.display_url} alt={item.caption ?? ""} fill sizes="(max-width: 640px) 50vw, 200px" style={{ objectFit: "cover" }} />
                            : <a href={item.display_url} target="_blank" rel="noopener" style={{ textDecoration: "none", display: "flex", flexDirection: "column", alignItems: "center", gap: 6, color: "var(--forest-600)", padding: 16, textAlign: "center" }}>
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M11 3H17V9M17 3L9 11M8 4H4C3.45 4 3 4.45 3 5V16C3 16.55 3.45 17 4 17H15C15.55 17 16 16.55 16 16V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                                <span style={{ fontSize: 11 }}>{item.caption ?? "Link"}</span>
                              </a>
                          }
                        </div>
                      ))}
                    </div>
                }
              </motion.div>
            )}

            {/* Reviews */}
            {tab === "reviews" && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                {user && !isOwner && !revDone && (
                  <form onSubmit={submitReview} style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, padding: 18, marginBottom: 20, display: "flex", flexDirection: "column", gap: 12 }}>
                    <p className="eyebrow">Write a review</p>
                    <div style={{ display: "flex", gap: 4 }}>
                      {[1,2,3,4,5].map(i => (
                        <button key={i} type="button" onClick={() => setRating(i)} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(0)}
                          style={{ background: "none", border: "none", cursor: "pointer", padding: 2, transition: "transform 0.1s" }}
                          onMouseDown={e => (e.currentTarget.style.transform = "scale(0.9)")}
                          onMouseUp={e => (e.currentTarget.style.transform = "")}>
                          <svg width="26" height="26" viewBox="0 0 16 16" fill={(hover || rating) >= i ? "#C9A84C" : "#E5E7EB"}><path d="M8 1l1.85 3.75L14 5.5l-3 2.92.7 4.08L8 10.35 4.3 12.5l.7-4.08L2 5.5l4.15-.75z"/></svg>
                        </button>
                      ))}
                    </div>
                    <input value={service} onChange={e => setService(e.target.value)} placeholder="Service received (optional)" className="input" style={{ fontSize: 13 }} />
                    <div>
                      <textarea value={comment} onChange={e => setComment(e.target.value)} placeholder="Share your experience…" rows={3} maxLength={2000} className="input" style={{ resize: "none", fontSize: 13 }} />
                      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
                        <span style={{ fontSize: 11, color: comment.length > 0 && comment.length < 10 ? "#C53030" : "var(--ink-faint)" }}>
                          {comment.length < 10 ? `${10 - comment.length} more characters needed` : " "}
                        </span>
                        <span style={{ fontSize: 11, color: "var(--ink-faint)" }}>{comment.length}/2000</span>
                      </div>
                    </div>
                    {revError && <p style={{ fontSize: 12.5, color: "#C53030" }}>{revError}</p>}
                    <button type="submit" disabled={submitting} className="btn btn-primary" style={{ alignSelf: "flex-start", fontSize: 13 }}>
                      {submitting ? "Submitting…" : "Submit review"}
                    </button>
                  </form>
                )}
                {revDone && <div style={{ background: "var(--forest-100)", borderRadius: 2, padding: "12px 14px", fontSize: 13.5, color: "var(--forest-600)", marginBottom: 20, fontWeight: 500 }}>✓ Review submitted. Thank you!</div>}
                {!user && <div style={{ background: "var(--forest-50)", border: "1px solid var(--border)", borderRadius: 2, padding: "12px 14px", fontSize: 13.5, color: "var(--ink-muted)", marginBottom: 20 }}>
                  <Link href="/auth/login" style={{ color: "var(--forest)", fontWeight: 500 }}>Sign in</Link> to leave a review.
                </div>}
                {revLoad && reviews.length === 0
                  ? <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>{[1,2].map(i => <Skeleton key={i} h={80} />)}</div>
                  : reviews.length === 0
                  ? <EmptyState text="No reviews yet" />
                  : <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                      {reviews.map(rev => (
                        <div key={rev.id} style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, padding: 16 }}>
                          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 8 }}>
                            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                              <Stars rating={rev.rating} size={13} />
                              {rev.service_received && <span className="badge badge-slate" style={{ fontSize: 10.5, alignSelf: "flex-start" }}>{rev.service_received}</span>}
                            </div>
                            <span style={{ fontSize: 11.5, color: "var(--ink-faint)", flexShrink: 0 }}>{timeAgo(rev.created_at)}</span>
                          </div>
                          <p style={{ fontSize: 13.5, color: "var(--ink-muted)", lineHeight: 1.65, whiteSpace: "pre-line" }}>{rev.comment}</p>
                          {rev.reply && (
                            <div style={{ marginTop: 12, background: "var(--forest-50)", borderRadius: 2, padding: "10px 12px", borderLeft: "3px solid var(--forest-400)" }}>
                              <p style={{ fontSize: 11.5, fontWeight: 600, color: "var(--forest)", marginBottom: 4 }}>{biz.name} replied</p>
                              <p style={{ fontSize: 13, color: "var(--ink-muted)" }}>{rev.reply.content}</p>
                            </div>
                          )}
                        </div>
                      ))}
                      {reviews.length < revTotal && (
                        <button onClick={() => loadReviews(reviews.length)} disabled={revLoad} className="btn btn-outline" style={{ alignSelf: "center", fontSize: 13 }}>
                          {revLoad ? "Loading…" : "Load more reviews"}
                        </button>
                      )}
                    </div>
                }
              </motion.div>
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
