"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useReferenceData } from "@/lib/referenceData";
import { Stars } from "@/components/ui/Stars";
import { Skeleton } from "@/components/ui/Skeleton";
import type { Business, Category } from "@/types";

type Tab = "overview" | "profile" | "services";

export default function DashboardPage() {
  const { user, loading: authLoading, refresh } = useAuth();
  const router = useRouter();
  const { categories: cats } = useReferenceData();
  const [biz,     setBiz]     = useState<Business | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab,     setTab]     = useState<Tab>("overview");
  const [saving,  setSaving]  = useState(false);
  const [saved,   setSaved]   = useState(false);
  const [error,   setError]   = useState("");

  const [name,        setName]        = useState("");
  const [description, setDescription] = useState("");
  const [categoryId,  setCategoryId]  = useState("");
  const [whatsapp,    setWhatsapp]    = useState("");
  const [phone,       setPhone]       = useState("");
  const [email,       setEmail]       = useState("");
  const [website,     setWebsite]     = useState("");
  const [instagram,   setInstagram]   = useState("");
  const [available,   setAvailable]   = useState(true);
  const [showCreate,  setShowCreate]  = useState(false);

  useEffect(() => {
    if (!authLoading && !user) { router.push("/auth/login"); return; }
    if (!user) return;
    api.businesses.getMine().catch(() => null)
      .then((b) => {
        setBiz(b);
        if (b) {
          setName(b.name); setDescription(b.description);
          setCategoryId(b.category_id); setWhatsapp(b.whatsapp ?? "");
          setPhone(b.phone ?? ""); setEmail(b.contact_email ?? "");
          setWebsite(b.website ?? ""); setInstagram(b.instagram ?? "");
          setAvailable(b.is_available);
        }
      }).finally(() => setLoading(false));
  }, [user, authLoading]);

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true); setError(""); setSaved(false);
    try {
      const updated = await api.businesses.update({ name, description, category_id: categoryId, whatsapp: whatsapp || null, phone: phone || null, contact_email: email || null, website: website || null, instagram: instagram || null, is_available: available });
      setBiz(updated as any); setSaved(true); setTimeout(() => setSaved(false), 3000);
    } catch (err: any) { setError(err.message ?? "Could not save."); }
    finally { setSaving(false); }
  };

  if (authLoading || loading) return <DashSkeleton />;
  if (!user) return null;

  const statusStyle: Record<string, { bg: string; color: string }> = {
    pending:   { bg: "#FBF4E0", color: "#A8882E" },
    approved:  { bg: "#E8F0EA", color: "#2B6438" },
    suspended: { bg: "#FFF0F0", color: "#C0392B" },
  };
  const ss = statusStyle[biz?.status ?? "pending"] ?? statusStyle.pending;

  return (
    <div style={{ minHeight: "100vh", background: "#FAF3E7" }}>
      {/* Page header */}
      <div style={{ background: "var(--forest)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ maxWidth: 1060, margin: "0 auto", padding: "32px 28px 28px" }}>
          <p style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(67,8,31,0.5)", marginBottom: 8 }}>
            Owner dashboard
          </p>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: "clamp(26px,4vw,36px)", color: "var(--cream)", letterSpacing: "-0.02em" }}>
              Hi, {user.full_name.split(" ")[0]} 👋
            </h1>
            {biz && (
              <Link href={`/businesses/${biz.slug}`} style={{ display: "flex", alignItems: "center", gap: 7, background: "rgba(250,243,231,0.1)", border: "1px solid rgba(250,243,231,0.15)", borderRadius: 2, padding: "8px 14px", textDecoration: "none", fontSize: 12.5, color: "rgba(250,243,231,0.75)", transition: "all 0.15s" }}
              onMouseEnter={e => (e.currentTarget.style.background = "rgba(250,243,231,0.16)")}
              onMouseLeave={e => (e.currentTarget.style.background = "rgba(250,243,231,0.1)")}>
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5" stroke="currentColor" strokeWidth="1.4"/><path d="M8 5.5v5M5.5 8h5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>
                View public profile
              </Link>
            )}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1060, margin: "0 auto", padding: "28px 28px 60px" }}>
        {/* Account status banner */}
        {user.status === "pending_email_verification" && (
          <StatusBanner tone="amber" title="Verify your email address" body="Check your school inbox and click the verification link." />
        )}

        {user.status === "pending_id_review" && !user.student_id_submitted && (
          <div style={{ background: "#F5EBDF", border: "1px solid rgba(67,8,31,0.18)", borderRadius: 2, padding: "18px 20px", marginBottom: 24 }}>
            <p style={{ fontSize: 13.5, fontWeight: 700, color: "var(--forest)", marginBottom: 4 }}>Submit your student ID</p>
            <p style={{ fontSize: 12.5, color: "var(--ink-muted)", marginBottom: 14 }}>
              One last step: upload a photo of your student ID so an admin can verify your account.
            </p>
            <StudentIdUpload onSubmitted={refresh} />
          </div>
        )}

        {user.status === "pending_id_review" && user.student_id_submitted && (
          <StatusBanner tone="indigo" title="Student ID under review" body="Your ID has been submitted. You'll be notified once approved." />
        )}

        {user.status === "suspended" && (
          <StatusBanner tone="red" title="Account suspended" body="Contact support if you believe this is a mistake." />
        )}

        {biz && biz.status === "pending" && (
          <StatusBanner tone="indigo" title="Listing awaiting approval" body="Your business profile is under admin review and won't appear in search results until it's approved. This is normal for new listings." />
        )}

        {biz && biz.status === "suspended" && (
          <StatusBanner tone="red" title="Listing suspended" body="Your business profile has been hidden from search. Contact support if you believe this is a mistake." />
        )}

        {/* No business yet */}
        {!biz && user.status === "verified" && (
          <div style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, padding: "56px 32px", textAlign: "center" }}>
            <div style={{ width: 56, height: 56, borderRadius: 2, background: "var(--forest-100)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" stroke="var(--forest-600)" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/><path d="M9 22V12h6v10" stroke="var(--forest-600)" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </div>
            <h2 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 28, color: "var(--forest)", marginBottom: 8 }}>No business profile yet</h2>
            <p style={{ fontSize: 14, color: "var(--ink-faint)", maxWidth: 360, margin: "0 auto 28px", lineHeight: 1.7 }}>
              Create your profile to start appearing in search results and connect with customers.
            </p>
            {!showCreate
              ? <button onClick={() => setShowCreate(true)} className="btn btn-primary" style={{ fontSize: 14, padding: "11px 24px" }}>Create business profile</button>
              : <CreateForm cats={cats} onCreated={b => setBiz(b)} onCancel={() => setShowCreate(false)} />
            }
          </div>
        )}

        {/* Business dashboard */}
        {biz && (
          <>
            {/* Stats row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12, marginBottom: 24 }}>
              {[
                { label: "Rating", value: biz.average_rating > 0 ? biz.average_rating.toFixed(1) : "N/A", sub: `${biz.review_count} reviews` },
                { label: "Status", value: biz.status ?? "pending", badge: true },
                { label: "Portfolio", value: biz.portfolio_items.length, sub: "items uploaded" },
                { label: "Services", value: biz.services.length, sub: "listed" },
              ].map(stat => (
                <div key={stat.label} style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, padding: "16px" }}>
                  <p style={{ fontSize: 11, color: "var(--ink-faint)", marginBottom: 8, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.06em" }}>{stat.label}</p>
                  {stat.badge
                    ? <span style={{ ...ss, fontSize: 12, fontWeight: 600, padding: "4px 10px", borderRadius: 100, display: "inline-block" }}>{stat.value}</span>
                    : <p style={{ fontFamily: "var(--font-serif)", fontSize: 28, fontWeight: 300, color: "var(--forest)", lineHeight: 1 }}>{stat.value as any}</p>
                  }
                  {stat.sub && <p style={{ fontSize: 11, color: "var(--ink-faint)", marginTop: 4 }}>{stat.sub}</p>}
                </div>
              ))}
            </div>

            {/* Tab panel */}
            <div style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, overflow: "hidden" }}>
              <div style={{ display: "flex", borderBottom: "1px solid var(--border)", overflowX: "auto" }} className="scrollbar-hide">
                {(["overview","profile","services"] as Tab[]).map(t => (
                  <button key={t} onClick={() => setTab(t)} style={{
                    padding: "14px 20px", fontSize: 13.5, fontWeight: 500, textTransform: "capitalize",
                    background: "none", border: "none", cursor: "pointer", fontFamily: "var(--font-sans)",
                    color: tab === t ? "var(--forest)" : "var(--ink-faint)",
                    borderBottom: `2px solid ${tab === t ? "var(--forest)" : "transparent"}`,
                    marginBottom: -1, transition: "color 0.15s", flexShrink: 0,
                  }}>{t}</button>
                ))}
              </div>

              <div style={{ padding: 24 }}>
                {/* Overview */}
                {tab === "overview" && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    <div style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
                      <div style={{ width: 52, height: 52, borderRadius: 2, background: "var(--forest-100)", color: "var(--forest)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 20, flexShrink: 0 }}>
                        {biz.name[0]}
                      </div>
                      <div>
                        <h2 style={{ fontFamily: "var(--font-serif)", fontWeight: 400, fontSize: 20, color: "var(--forest)", marginBottom: 4 }}>{biz.name}</h2>
                        <Stars rating={biz.average_rating} count={biz.review_count} size={12} />
                      </div>
                    </div>
                    {/* Quick actions */}
                    <div className="dash-form-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      {[
                        { label: "Edit profile", icon: "M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z", action: () => setTab("profile") },
                        { label: "View live profile", icon: "M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3", action: () => window.open(`/businesses/${biz.slug}`, "_blank") },
                      ].map(q => (
                        <button key={q.label} onClick={q.action} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 16px", borderRadius: 2, border: "1px solid var(--border)", background: "var(--cream)", cursor: "pointer", transition: "all 0.15s" }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(67,8,31,0.2)"; e.currentTarget.style.background = "var(--forest-50)"; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.background = "var(--cream)"; }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--forest-600)" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d={q.icon}/></svg>
                            <span style={{ fontSize: 13, fontWeight: 500, color: "var(--forest)" }}>{q.label}</span>
                          </div>
                          <svg width="14" height="14" viewBox="0 0 12 12" fill="none"><path d="M2.5 6h7M7 3.5 9.5 6 7 8.5" stroke="var(--ink-faint)" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>
                        </button>
                      ))}
                    </div>
                    {/* Availability toggle */}
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 16px", background: "var(--cream)", borderRadius: 2, border: "1px solid var(--border)" }}>
                      <div>
                        <p style={{ fontSize: 13.5, fontWeight: 500, color: "var(--forest)", marginBottom: 2 }}>Availability</p>
                        <p style={{ fontSize: 12, color: "var(--ink-faint)" }}>{available ? "Shown as open to customers" : "Shown as currently busy"}</p>
                      </div>
                      <button onClick={async () => { const n = !available; setAvailable(n); await api.businesses.update({ is_available: n }); }}
                        style={{ width: 44, height: 24, borderRadius: 100, background: available ? "var(--forest)" : "#D1D5DB", border: "none", cursor: "pointer", position: "relative", transition: "background 0.2s" }}>
                        <div style={{ position: "absolute", top: 3, left: available ? 22 : 3, width: 18, height: 18, borderRadius: "50%", background: "white", transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)" }} />
                      </button>
                    </div>
                  </div>
                )}

                {/* Edit profile */}
                {tab === "profile" && (
                  <form onSubmit={saveProfile} style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 600 }}>
                    <BusinessImageUpload biz={biz} onUpdated={b => setBiz(b)} />
                    <div className="dash-form-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                      <div>
                        <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 6 }}>Business name</label>
                        <input value={name} onChange={e => setName(e.target.value)} className="input" required />
                      </div>
                      <div>
                        <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 6 }}>Category</label>
                        <select value={categoryId} onChange={e => setCategoryId(e.target.value)} className="input">
                          {cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                        </select>
                      </div>
                    </div>
                    <div>
                      <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 6 }}>Description</label>
                      <textarea value={description} onChange={e => setDescription(e.target.value)} rows={4} className="input" style={{ resize: "vertical" }} required />
                    </div>
                    <div className="dash-form-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                      {([["WhatsApp", whatsapp, setWhatsapp, "+265991234567"], ["Phone", phone, setPhone, "+265..."], ["Contact email", email, setEmail, ""], ["Website", website, setWebsite, "https://..."], ["Instagram", instagram, setInstagram, "@username"]] as [string, string, (v: string) => void, string][]).map(([l, v, fn, ph]) => (
                        <div key={l}>
                          <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 6 }}>{l}</label>
                          <input value={v} onChange={e => fn(e.target.value)} placeholder={ph} className="input" />
                        </div>
                      ))}
                    </div>
                    {error && <p style={{ fontSize: 13, color: "#C53030" }}>{error}</p>}
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <button type="submit" disabled={saving} className="btn btn-primary" style={{ fontSize: 13.5 }}>
                        {saving ? "Saving…" : "Save changes"}
                      </button>
                      {saved && <span style={{ fontSize: 13, color: "var(--forest-600)", display: "flex", alignItems: "center", gap: 6 }}>
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 8l4 4 6-6" stroke="var(--forest-600)" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/></svg>
                        Saved
                      </span>}
                    </div>
                  </form>
                )}

                {/* Services */}
                {tab === "services" && (
                  <div>
                    {biz.services.length === 0
                      ? <div style={{ textAlign: "center", padding: "40px 0", color: "var(--ink-faint)" }}>
                          <p style={{ fontFamily: "var(--font-serif)", fontSize: 18, color: "var(--forest)", marginBottom: 6 }}>No services listed</p>
                          <p style={{ fontSize: 13.5, marginBottom: 16 }}>Add services when editing your profile.</p>
                          <button onClick={() => setTab("profile")} className="btn btn-outline" style={{ fontSize: 13 }}>Go to profile</button>
                        </div>
                      : <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          {biz.services.map(svc => (
                            <div key={svc.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 16px", background: "var(--cream)", border: "1px solid var(--border)", borderRadius: 2 }}>
                              <div>
                                <p style={{ fontWeight: 500, fontSize: 13.5, color: "var(--forest)" }}>{svc.name}</p>
                                {svc.description && <p style={{ fontSize: 12, color: "var(--ink-faint)", marginTop: 2 }}>{svc.description}</p>}
                              </div>
                              {svc.price_range && <span style={{ fontSize: 12, fontWeight: 500, background: "var(--gold-light)", color: "var(--gold-dark)", padding: "4px 10px", borderRadius: 2, flexShrink: 0, marginLeft: 12 }}>{svc.price_range}</span>}
                            </div>
                          ))}
                        </div>
                    }
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StatusBanner({ tone, title, body }: { tone: "amber" | "indigo" | "red"; title: string; body: string }) {
  const palette = {
    amber:  { bg: "#FBF4E0", border: "rgba(201,168,76,0.3)",  iconBg: "rgba(201,168,76,0.15)", strong: "#A8882E", soft: "#856A1A" },
    indigo: { bg: "#F5EBDF", border: "rgba(67,8,31,0.18)",    iconBg: "rgba(67,8,31,0.08)",    strong: "var(--forest)", soft: "var(--ink-muted)" },
    red:    { bg: "#FFF0F0", border: "rgba(192,57,43,0.2)",   iconBg: "rgba(192,57,43,0.1)",   strong: "#C0392B",       soft: "#C0392B" },
  }[tone];
  return (
    <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
      style={{ background: palette.bg, border: `1px solid ${palette.border}`, borderRadius: 2, padding: "14px 18px", marginBottom: 24, display: "flex", alignItems: "flex-start", gap: 12 }}>
      <div style={{ width: 32, height: 32, borderRadius: "50%", background: palette.iconBg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke={palette.strong} strokeWidth="1.5"/><path d="M8 5v3.5M8 11h.01" stroke={palette.strong} strokeWidth="1.5" strokeLinecap="round"/></svg>
      </div>
      <div>
        <p style={{ fontSize: 13.5, fontWeight: 600, color: palette.strong, marginBottom: 2 }}>{title}</p>
        <p style={{ fontSize: 12.5, color: palette.soft, opacity: 0.8 }}>{body}</p>
      </div>
    </motion.div>
  );
}

function BusinessImageUpload({ biz, onUpdated }: { biz: Business; onUpdated: (b: Business) => void }) {
  const [uploading, setUploading] = useState<"logo" | "cover" | null>(null);
  const [error, setError] = useState("");

  const handleUpload = async (file: File, kind: "logo" | "cover") => {
    setUploading(kind); setError("");
    try {
      const { storage_key } = await api.media.upload(file, kind === "logo" ? "business_logo" : "business_cover");
      const updated = kind === "logo"
        ? await api.businesses.updateLogo(storage_key)
        : await api.businesses.updateCover(storage_key);
      onUpdated(updated);
    } catch (err: any) {
      setError(err.message ?? `Could not upload ${kind}. Try again.`);
    } finally {
      setUploading(null);
    }
  };

  return (
    <div style={{ marginBottom: 4 }}>
      <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 8 }}>Business photos</label>

      {/* Cover band with logo overlapping, mirrors the public profile layout */}
      <div style={{ position: "relative", height: 120, borderRadius: 2, overflow: "hidden", background: "var(--forest-50)", border: "1px solid var(--border)" }}>
        {biz.cover_url && (
          <Image src={biz.cover_url} alt="" fill sizes="600px" style={{ objectFit: "cover" }} />
        )}
        <UploadTrigger
          label={uploading === "cover" ? "Uploading…" : biz.cover_url ? "Change cover" : "Add cover photo"}
          onFile={f => handleUpload(f, "cover")}
          disabled={uploading !== null}
          style={{ position: "absolute", bottom: 8, right: 8 }}
        />
        <div style={{
          position: "absolute", left: 14, bottom: -22, width: 56, height: 56, borderRadius: 2,
          border: "3px solid white", overflow: "hidden", background: "white", boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
        }}>
          {biz.logo_url && (
            <Image src={biz.logo_url} alt="" fill sizes="56px" style={{ objectFit: "cover" }} />
          )}
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 28 }}>
        <UploadTrigger
          label={uploading === "logo" ? "Uploading…" : biz.logo_url ? "Change logo" : "Add logo"}
          onFile={f => handleUpload(f, "logo")}
          disabled={uploading !== null}
        />
      </div>

      {error && <p style={{ fontSize: 12, color: "#C53030", marginTop: 6 }}>{error}</p>}
      <p style={{ fontSize: 11.5, color: "var(--ink-faint)", marginTop: 4 }}>JPG, PNG, or WebP.</p>
    </div>
  );
}

function UploadTrigger({ label, onFile, disabled, style }: { label: string; onFile: (f: File) => void; disabled?: boolean; style?: React.CSSProperties }) {
  return (
    <label style={{
      display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 500,
      color: "var(--forest)", background: "white", border: "1px solid var(--border-med)",
      borderRadius: 2, padding: "6px 12px", cursor: disabled ? "default" : "pointer",
      opacity: disabled ? 0.6 : 1, boxShadow: "0 1px 3px rgba(0,0,0,0.06)", ...style,
    }}>
      <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M8 11V3M8 3L5 6M8 3l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M2.5 11v1.5A1.5 1.5 0 004 14h8a1.5 1.5 0 001.5-1.5V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
      {label}
      <input type="file" accept="image/jpeg,image/png,image/webp" disabled={disabled}
        onChange={e => { const f = e.target.files?.[0]; if (f) onFile(f); e.target.value = ""; }}
        style={{ display: "none" }} />
    </label>
  );
}

function StudentIdUpload({ onSubmitted }: { onSubmitted: () => void | Promise<void> }) {
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setSubmitting(true); setError("");
    try {
      const { storage_key } = await api.media.upload(file, "student_id");
      await api.auth.submitStudentId(storage_key);
      await onSubmitted();
    } catch (err: any) {
      setError(err.message ?? "Could not submit your student ID. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={submit} style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10 }}>
      <label style={{
        display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, fontWeight: 500,
        color: "#4338CA", background: "white", border: "1px solid rgba(99,102,241,0.3)",
        borderRadius: 2, padding: "9px 14px", cursor: "pointer",
      }}>
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M8 11V3M8 3L5 6M8 3l3 3" stroke="#4338CA" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M2.5 11v1.5A1.5 1.5 0 004 14h8a1.5 1.5 0 001.5-1.5V11" stroke="#4338CA" strokeWidth="1.5" strokeLinecap="round"/></svg>
        {file ? file.name : "Choose photo"}
        <input type="file" accept="image/jpeg,image/png,image/webp" onChange={e => setFile(e.target.files?.[0] ?? null)} style={{ display: "none" }} />
      </label>
      <button type="submit" disabled={!file || submitting} className="btn btn-primary" style={{ padding: "9px 18px", fontSize: 12.5, opacity: (!file || submitting) ? 0.6 : 1 }}>
        {submitting ? "Uploading…" : "Submit for review"}
      </button>
      {error && <p style={{ width: "100%", fontSize: 12, color: "#C53030", marginTop: 2 }}>{error}</p>}
    </form>
  );
}

function CreateForm({ cats, onCreated, onCancel }: { cats: Category[]; onCreated: (b: Business) => void; onCancel: () => void }) {
  const [name, setName] = useState(""); const [desc, setDesc] = useState(""); const [catId, setCatId] = useState(""); const [saving, setSaving] = useState(false); const [error, setError] = useState("");
  const submit = async (e: React.FormEvent) => { e.preventDefault(); setSaving(true); setError(""); try { const b = await api.businesses.create({ name, description: desc, category_id: catId, services: [] }); onCreated(b as any); } catch (err: any) { setError(err.message ?? "Failed."); } finally { setSaving(false); } };
  return (
    <form onSubmit={submit} style={{ maxWidth: 440, margin: "0 auto", textAlign: "left", display: "flex", flexDirection: "column", gap: 14 }}>
      <div><label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 6 }}>Business name</label><input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Rasta Designs" required className="input" /></div>
      <div><label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 6 }}>Category</label><select value={catId} onChange={e => setCatId(e.target.value)} className="input" required><option value="">Select…</option>{cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
      <div><label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 6 }}>Description</label><textarea value={desc} onChange={e => setDesc(e.target.value)} rows={3} placeholder="What does your business do?" required className="input" style={{ resize: "none" }} /></div>
      {error && <p style={{ fontSize: 12.5, color: "#C53030" }}>{error}</p>}
      <div style={{ display: "flex", gap: 10 }}>
        <button type="button" onClick={onCancel} className="btn btn-outline" style={{ flex: 1, justifyContent: "center" }}>Cancel</button>
        <button type="submit" disabled={saving} className="btn btn-primary" style={{ flex: 1, justifyContent: "center" }}>{saving ? "Creating…" : "Create"}</button>
      </div>
    </form>
  );
}

function DashSkeleton() {
  return <div style={{ minHeight: "100vh", background: "#FAF3E7" }}><div style={{ background: "var(--forest)", height: 120 }} /><div style={{ maxWidth: 1060, margin: "0 auto", padding: 28, display: "flex", flexDirection: "column", gap: 16 }}><div className="dash-skeleton-stats" style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12 }}>{[1,2,3,4].map(i => <Skeleton key={i} h={80} r={2} />)}</div><Skeleton h={400} r={2} /></div></div>;
}
