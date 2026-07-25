"use client";
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { api, ApiError } from "@/lib/api";

type State = "verifying" | "success" | "error" | "missing";

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailContent />
    </Suspense>
  );
}

function VerifyEmailContent() {
  const params = useSearchParams();
  const token = params.get("token");

  const [state, setState] = useState<State>("verifying");
  const [error, setError] = useState("");
  const [resendEmail, setResendEmail] = useState("");
  const [resendState, setResendState] = useState<"idle" | "sending" | "sent">("idle");

  useEffect(() => {
    if (!token) {
      setState("missing");
      return;
    }
    api.auth.verifyEmail(token)
      .then(() => setState("success"))
      .catch(err => {
        setError(err instanceof ApiError ? err.message : "Something went wrong verifying your email.");
        setState("error");
      });
  }, [token]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    setResendState("sending");
    try {
      await api.auth.resendVerification(resendEmail.trim());
    } finally {
      // Always shows the same confirmation regardless of outcome — the
      // backend deliberately doesn't reveal whether an email is registered.
      setResendState("sent");
    }
  };

  return (
    <div style={{ minHeight: "calc(100vh - 58px)", display: "flex", alignItems: "center", justifyContent: "center", padding: "56px 24px", background: "var(--cream)" }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        style={{ width: "100%", maxWidth: 400, textAlign: "center" }}>

        {state === "verifying" && (
          <>
            <Spinner />
            <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 28, color: "var(--forest)", letterSpacing: "-0.025em", marginTop: 20, marginBottom: 8 }}>
              Verifying your email…
            </h1>
            <p style={{ fontSize: 13.5, color: "var(--ink-faint)" }}>One moment.</p>
          </>
        )}

        {state === "success" && (
          <>
            <CheckIcon />
            <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 30, color: "var(--forest)", letterSpacing: "-0.025em", marginTop: 20, marginBottom: 10 }}>
              Email verified
            </h1>
            <p style={{ fontSize: 14, color: "var(--ink-faint)", lineHeight: 1.6, marginBottom: 28 }}>
              Your school email is confirmed. Log in to continue setting up your account and submit your student ID.
            </p>
            <Link href="/auth/login" className="btn btn-primary" style={{ justifyContent: "center", padding: "13px 28px", borderRadius: 2, display: "inline-flex" }}>
              Continue to login
            </Link>
          </>
        )}

        {state === "missing" && (
          <>
            <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 28, color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 10 }}>
              Missing verification link
            </h1>
            <p style={{ fontSize: 13.5, color: "var(--ink-faint)" }}>
              This page needs a verification token. Use the link from your email, not this page directly.
            </p>
          </>
        )}

        {state === "error" && (
          <>
            <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 28, color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 10 }}>
              Link expired or invalid
            </h1>
            <p style={{ fontSize: 13.5, color: "#C53030", marginBottom: 28 }}>{error}</p>

            {resendState === "sent" ? (
              <p style={{ fontSize: 13.5, color: "var(--forest-600)", fontWeight: 500 }}>
                If that email has an account awaiting verification, a fresh link is on its way.
              </p>
            ) : (
              <form onSubmit={handleResend} style={{ display: "flex", flexDirection: "column", gap: 12, textAlign: "left" }}>
                <div>
                  <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 7 }}>
                    Get a new verification link
                  </label>
                  <input type="email" value={resendEmail} onChange={e => setResendEmail(e.target.value)}
                    placeholder="you@mubas.ac.mw" required className="input" />
                </div>
                <button type="submit" disabled={resendState === "sending"} className="btn btn-primary"
                  style={{ width: "100%", justifyContent: "center", padding: "13px", borderRadius: 2 }}>
                  {resendState === "sending" ? "Sending…" : "Resend verification email"}
                </button>
              </form>
            )}
          </>
        )}
      </motion.div>
    </div>
  );
}

function Spinner() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" style={{ animation: "spinSlow 0.8s linear infinite", margin: "0 auto", display: "block" }}>
      <circle cx="16" cy="16" r="13" stroke="var(--border-med)" strokeWidth="2.5" fill="none" />
      <path d="M16 3a13 13 0 0112 8" stroke="var(--forest)" strokeWidth="2.5" strokeLinecap="round" fill="none" />
    </svg>
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
