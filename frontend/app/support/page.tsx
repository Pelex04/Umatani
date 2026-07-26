"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatDate } from "@/lib/utils";
import type { SupportTicket } from "@/types";

const STATUS_LABEL: Record<SupportTicket["status"], { label: string; bg: string; color: string }> = {
  open:        { label: "Open",        bg: "#F5EBDF", color: "var(--forest)" },
  in_progress: { label: "In progress", bg: "#FBF4E0", color: "#A8882E" },
  resolved:    { label: "Resolved",    bg: "#EAF2EC", color: "#2F6B45" },
  closed:      { label: "Closed",      bg: "#F1EBE3", color: "var(--ink-faint)" },
};

export default function SupportPage() {
  const { user, loading: authLoading } = useAuth();

  const [ticketType, setTicketType] = useState<"support" | "feature_request">("support");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [honeypot, setHoneypot] = useState(""); // spam trap, see input below
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [justSubmitted, setJustSubmitted] = useState(false);

  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(true);

  const loadTickets = () => {
    setLoadingTickets(true);
    api.support.myTickets()
      .then(setTickets)
      .finally(() => setLoadingTickets(false));
  };

  useEffect(() => {
    if (user) loadTickets();
    else setLoadingTickets(false);
  }, [user]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (honeypot) return; // a real person never sees or fills this field
    if (subject.trim().length < 5) { setError("Subject must be at least 5 characters."); return; }
    if (description.trim().length < 20) { setError("Please give a bit more detail (at least 20 characters)."); return; }
    setSubmitting(true); setError("");
    try {
      await api.support.createTicket({ ticket_type: ticketType, subject: subject.trim(), description: description.trim() });
      setSubject(""); setDescription(""); setJustSubmitted(true);
      loadTickets();
    } catch (err: any) {
      setError(err.message ?? "Could not submit your request. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--cream)", padding: "56px 24px 80px" }}>
      <div style={{ maxWidth: 640, margin: "0 auto" }}>
        <p className="eyebrow" style={{ marginBottom: 10 }}>Support</p>
        <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: "clamp(30px,4vw,42px)", color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 12 }}>
          Need <span style={{ fontWeight: 800 }}>help?</span>
        </h1>
        <p style={{ fontSize: 14.5, color: "var(--ink-muted)", lineHeight: 1.7, marginBottom: 36, maxWidth: 480 }}>
          Trouble with your account, a question about how something works, or an idea for what we should build next — send it here and an admin will get back to you.
        </p>

        {authLoading ? (
          <Skeleton h={200} />
        ) : !user ? (
          <div style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, padding: 28, textAlign: "center" }}>
            <p style={{ fontSize: 14, color: "var(--ink-muted)", marginBottom: 16 }}>Sign in to contact support.</p>
            <Link href="/auth/login" className="btn btn-primary">Sign in</Link>
          </div>
        ) : (
          <>
            <form onSubmit={submit} style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, padding: 24, marginBottom: 40, display: "flex", flexDirection: "column", gap: 14 }}>
              <div style={{ display: "flex", gap: 8 }}>
                {(["support", "feature_request"] as const).map(t => (
                  <button key={t} type="button" onClick={() => setTicketType(t)} style={{
                    flex: 1, padding: "10px 14px", fontSize: 12.5, fontWeight: 600,
                    borderRadius: 2, cursor: "pointer",
                    border: `1px solid ${ticketType === t ? "var(--forest)" : "var(--border-med)"}`,
                    background: ticketType === t ? "var(--forest)" : "white",
                    color: ticketType === t ? "var(--cream)" : "var(--ink-muted)",
                    transition: "all 0.15s",
                  }}>
                    {t === "support" ? "Something's wrong" : "Feature idea"}
                  </button>
                ))}
              </div>

              <input value={subject} onChange={e => setSubject(e.target.value)} placeholder="Brief subject" className="input" maxLength={255} required />
              <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Tell us what's going on, with as much detail as helps" rows={5} maxLength={5000} className="input" style={{ resize: "none" }} required />
              <div style={{ textAlign: "right", fontSize: 11, color: "var(--ink-faint)", marginTop: -8 }}>{description.length}/5000</div>

              {/* Honeypot — invisible to real users; positioned off-canvas
                  rather than display:none, since some bots skip hidden
                  fields but still fill visually-offscreen ones. */}
              <input
                type="text" name="website" value={honeypot} onChange={e => setHoneypot(e.target.value)}
                tabIndex={-1} autoComplete="off"
                style={{ position: "absolute", left: "-9999px", width: 1, height: 1, opacity: 0 }}
                aria-hidden="true"
              />

              {error && <p style={{ fontSize: 12.5, color: "#C53030" }}>{error}</p>}
              {justSubmitted && !error && (
                <p style={{ fontSize: 12.5, color: "#2F6B45" }}>✓ Sent. You'll see it appear below once it's logged.</p>
              )}

              <button type="submit" disabled={submitting} className="btn btn-primary" style={{ alignSelf: "flex-start" }}>
                {submitting ? "Sending…" : "Send to support"}
              </button>
            </form>

            <h2 style={{ fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 16, color: "var(--forest)", marginBottom: 14 }}>Your requests</h2>
            {loadingTickets ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>{[1, 2].map(i => <Skeleton key={i} h={70} />)}</div>
            ) : tickets.length === 0 ? (
              <p style={{ fontSize: 13.5, color: "var(--ink-faint)" }}>Nothing sent yet.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {tickets.map(t => {
                  const s = STATUS_LABEL[t.status];
                  return (
                    <motion.div key={t.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                      style={{ background: "white", border: "1px solid var(--border)", borderRadius: 2, padding: 16 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10, marginBottom: 6 }}>
                        <p style={{ fontSize: 13.5, fontWeight: 700, color: "var(--forest)" }}>{t.subject}</p>
                        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", padding: "3px 8px", borderRadius: 2, background: s.bg, color: s.color, whiteSpace: "nowrap" }}>
                          {s.label}
                        </span>
                      </div>
                      <p style={{ fontSize: 13, color: "var(--ink-muted)", lineHeight: 1.6, whiteSpace: "pre-line", marginBottom: t.admin_response ? 12 : 6 }}>{t.description}</p>
                      {t.admin_response && (
                        <div style={{ background: "var(--cream)", borderRadius: 2, padding: "10px 12px", marginBottom: 6 }}>
                          <p style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--ink-faint)", marginBottom: 4 }}>Response</p>
                          <p style={{ fontSize: 12.5, color: "var(--forest)", lineHeight: 1.6, whiteSpace: "pre-line" }}>{t.admin_response}</p>
                        </div>
                      )}
                      <p style={{ fontSize: 11, color: "var(--ink-faint)" }}>{formatDate(t.created_at)}</p>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
