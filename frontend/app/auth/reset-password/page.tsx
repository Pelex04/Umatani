"use client";
import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { api, ApiError } from "@/lib/api";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordContent />
    </Suspense>
  );
}

function ResetPasswordContent() {
  const params = useSearchParams();
  const token = params.get("token");

  const [password,        setPassword]        = useState("");
  const [confirmPassword, setConfirmPassword]  = useState("");
  const [show,     setShow]     = useState(false);
  const [state,    setState]    = useState<"idle" | "saving" | "done">("idle");
  const [error,    setError]    = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }
    if (!token) {
      setError("This page needs a reset link — use the link from your email.");
      return;
    }
    setState("saving");
    try {
      await api.auth.resetPassword(token, password);
      setState("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong resetting your password.");
      setState("idle");
    }
  };

  if (!token) {
    return (
      <div style={{ minHeight: "calc(100vh - 58px)", display: "flex", alignItems: "center", justifyContent: "center", padding: "56px 24px", background: "var(--cream)" }}>
        <div style={{ width: "100%", maxWidth: 380, textAlign: "center" }}>
          <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 28, color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 10 }}>
            Missing reset link
          </h1>
          <p style={{ fontSize: 13.5, color: "var(--ink-faint)", lineHeight: 1.6, marginBottom: 24 }}>
            This page needs a reset token. Use the link from your email, or request a new one.
          </p>
          <Link href="/auth/forgot-password" className="btn btn-primary" style={{ justifyContent: "center", padding: "13px 28px", borderRadius: 2, display: "inline-flex" }}>
            Request reset link
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "calc(100vh - 58px)", display: "flex", alignItems: "center", justifyContent: "center", padding: "56px 24px", background: "var(--cream)" }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        style={{ width: "100%", maxWidth: 380 }}>

        {state === "done" ? (
          <div style={{ textAlign: "center" }}>
            <CheckIcon />
            <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 28, color: "var(--forest)", letterSpacing: "-0.025em", marginTop: 20, marginBottom: 10 }}>
              Password reset
            </h1>
            <p style={{ fontSize: 13.5, color: "var(--ink-faint)", lineHeight: 1.6, marginBottom: 28 }}>
              Your password has been changed, and you've been signed out everywhere else for safety. Sign back in with your new password.
            </p>
            <Link href="/auth/login" className="btn btn-primary" style={{ justifyContent: "center", padding: "13px 28px", borderRadius: 2, display: "inline-flex" }}>
              Continue to login
            </Link>
          </div>
        ) : (
          <>
            <p className="eyebrow" style={{ marginBottom: 12 }}>Account</p>
            <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 34, color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 10 }}>
              Set a new password
            </h1>
            <p style={{ fontSize: 13.5, color: "var(--ink-faint)", lineHeight: 1.6, marginBottom: 32 }}>
              At least 10 characters, with an uppercase letter, a lowercase letter, and a number.
            </p>

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 7, letterSpacing: "0.01em" }}>
                  New password
                </label>
                <div style={{ position: "relative" }}>
                  <input type={show ? "text" : "password"} value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••••" required minLength={10} className="input" style={{ paddingRight: 54 }} />
                  <button type="button" onClick={() => setShow(!show)} style={{
                    position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)",
                    background: "none", border: "none", cursor: "pointer",
                    fontSize: 11, fontWeight: 600, color: "var(--ink-faint)",
                    letterSpacing: "0.04em", textTransform: "uppercase",
                  }}>
                    {show ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--forest)", marginBottom: 7, letterSpacing: "0.01em" }}>
                  Confirm new password
                </label>
                <input type={show ? "text" : "password"} value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••" required minLength={10} className="input" />
              </div>

              {error && (
                <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
                  style={{ background: "#FFF5F5", border: "1px solid #FED2D2", borderRadius: 2, padding: "11px 14px", fontSize: 13, color: "#C53030", display: "flex", alignItems: "center", gap: 8 }}>
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#C53030" strokeWidth="1.5"/><path d="M8 5v3.5M8 11h.01" stroke="#C53030" strokeWidth="1.5" strokeLinecap="round"/></svg>
                  {error}
                </motion.div>
              )}

              <button type="submit" disabled={state === "saving"} className="btn btn-primary"
                style={{ width: "100%", justifyContent: "center", padding: "13px", fontSize: 14, marginTop: 8, borderRadius: 2 }}>
                {state === "saving" ? "Saving…" : "Reset password"}
              </button>
            </form>

            {error.toLowerCase().includes("invalid") || error.toLowerCase().includes("expired") ? (
              <p style={{ fontSize: 13, color: "var(--ink-faint)", marginTop: 20, textAlign: "center" }}>
                <Link href="/auth/forgot-password" style={{ color: "var(--forest)", fontWeight: 500, textDecoration: "none" }}>
                  Request a new reset link
                </Link>
              </p>
            ) : null}
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
