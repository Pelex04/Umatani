"use client";
import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { api } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setState("sending");
    try {
      await api.auth.forgotPassword(email.trim());
    } finally {
      // Same response either way — the backend deliberately doesn't
      // reveal whether this email belongs to a registered account.
      setState("sent");
    }
  };

  return (
    <div style={{ minHeight: "calc(100vh - 58px)", display: "flex", alignItems: "center", justifyContent: "center", padding: "56px 24px", background: "var(--cream)" }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        style={{ width: "100%", maxWidth: 380 }}>

        {state === "sent" ? (
          <div style={{ textAlign: "center" }}>
            <CheckIcon />
            <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 28, color: "var(--forest)", letterSpacing: "-0.025em", marginTop: 20, marginBottom: 10 }}>
              Check your email
            </h1>
            <p style={{ fontSize: 13.5, color: "var(--ink-faint)", lineHeight: 1.6, marginBottom: 28 }}>
              If <strong style={{ color: "var(--forest)" }}>{email.trim()}</strong> is registered with Umata?, we've sent a link to reset the password. It expires in an hour.
            </p>
            <Link href="/auth/login" style={{ fontSize: 13.5, color: "var(--forest)", fontWeight: 500, textDecoration: "none" }}>
              Back to sign in
            </Link>
          </div>
        ) : (
          <>
            <p className="eyebrow" style={{ marginBottom: 12 }}>Account</p>
            <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 34, color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 10 }}>
              Forgot password?
            </h1>
            <p style={{ fontSize: 13.5, color: "var(--ink-faint)", lineHeight: 1.6, marginBottom: 32 }}>
              Enter the school email on your account and we'll send you a link to reset it.
            </p>

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 7, letterSpacing: "0.01em" }}>
                  School email
                </label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                  placeholder="you@mubas.ac.mw" required className="input" />
              </div>

              <button type="submit" disabled={state === "sending"} className="btn btn-primary"
                style={{ width: "100%", justifyContent: "center", padding: "13px", fontSize: 14, marginTop: 8, borderRadius: 2 }}>
                {state === "sending" ? "Sending…" : "Send reset link"}
              </button>
            </form>

            <p style={{ fontSize: 13.5, color: "var(--ink-faint)", marginTop: 24, textAlign: "center" }}>
              <Link href="/auth/login" style={{ color: "var(--forest)", fontWeight: 500, textDecoration: "none" }}>
                Back to sign in
              </Link>
            </p>
          </>
        )}
      </motion.div>
    </div>
  );
}

function CheckIcon() {
  return (
    <svg width="44" height="44" viewBox="0 0 44 44" style={{ margin: "0 auto", display: "block" }}>
      <circle cx="22" cy="22" r="20" fill="var(--forest-50)" stroke="var(--forest)" strokeWidth="1.5" />
      <path d="M14 22.5l5.5 5.5L30 16" stroke="var(--forest)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  );
}
