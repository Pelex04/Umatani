"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setLoading(true);
    try { await login(email, password); router.push("/dashboard"); }
    catch (err: any) { setError(err.message ?? "Incorrect email or password."); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ minHeight: "calc(100vh - 58px)", display: "flex" }}>
      {/* Left — brand (hidden on mobile, shown on desktop — see .auth-brand-panel in globals.css) */}
      <div className="auth-brand-panel" style={{
        flex: "0 0 46%", background: "var(--forest)",
        flexDirection: "column", justifyContent: "space-between",
        padding: "56px 60px", display: "none",
      }}>
        <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(247,244,239,0.12)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontWeight: 700, color: "var(--cream)", fontSize: 15 }}>u</span>
        </div>
        <div>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(201,168,76,0.6)", marginBottom: 20 }}>
            UMATA?
          </div>
          <h2 style={{
            fontFamily: "var(--font-serif)", fontStyle: "italic", fontWeight: 300,
            fontSize: 60, color: "var(--cream)", lineHeight: 0.9,
            letterSpacing: "-0.03em", marginBottom: 24,
          }}>
            Welcome<br />back.
          </h2>
          <p style={{ color: "rgba(247,244,239,0.4)", fontSize: 14.5, lineHeight: 1.75, maxWidth: 280 }}>
            Manage your business profile, track reviews, and connect with customers across campus.
          </p>
        </div>
        <p style={{ color: "rgba(247,244,239,0.18)", fontSize: 11 }}>
          Student talent · Malawi
        </p>
      </div>

      {/* Right — form */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "56px 24px", background: "var(--cream)" }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          style={{ width: "100%", maxWidth: 360 }}>

          <p className="eyebrow" style={{ marginBottom: 12 }}>Account</p>
          <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 38, color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 6 }}>
            Sign in
          </h1>
          <p style={{ fontSize: 13.5, color: "var(--ink-faint)", marginBottom: 40 }}>
            New to Umata?{" "}
            <Link href="/auth/register" style={{ color: "var(--forest)", fontWeight: 500, textDecoration: "none" }}>
              Create an account
            </Link>
          </p>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#374151", marginBottom: 7, letterSpacing: "0.01em" }}>
                School email
              </label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                placeholder="you@mubas.ac.mw" required className="input" />
            </div>

            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#374151", marginBottom: 7, letterSpacing: "0.01em" }}>
                Password
              </label>
              <div style={{ position: "relative" }}>
                <input type={show ? "text" : "password"} value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••••" required className="input" style={{ paddingRight: 54 }} />
                <button type="button" onClick={() => setShow(!show)} style={{
                  position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)",
                  background: "none", border: "none", cursor: "pointer",
                  fontSize: 11, fontWeight: 600, color: "var(--ink-faint)",
                  letterSpacing: "0.04em", textTransform: "uppercase",
                  transition: "color 0.15s",
                }}
                onMouseEnter={e => (e.currentTarget.style.color = "var(--forest)")}
                onMouseLeave={e => (e.currentTarget.style.color = "var(--ink-faint)")}>
                  {show ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {error && (
              <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
                style={{ background: "#FFF5F5", border: "1px solid #FED2D2", borderRadius: 10, padding: "11px 14px", fontSize: 13, color: "#C53030", display: "flex", alignItems: "center", gap: 8 }}>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#C53030" strokeWidth="1.5"/><path d="M8 5v3.5M8 11h.01" stroke="#C53030" strokeWidth="1.5" strokeLinecap="round"/></svg>
                {error}
              </motion.div>
            )}

            <button type="submit" disabled={loading} className="btn btn-primary"
              style={{ width: "100%", justifyContent: "center", padding: "13px", fontSize: 14, marginTop: 8, borderRadius: 11 }}>
              {loading ? (
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <svg width="14" height="14" viewBox="0 0 14 14" style={{ animation: "spinSlow 0.8s linear infinite" }}>
                    <circle cx="7" cy="7" r="5.5" stroke="rgba(247,244,239,0.3)" strokeWidth="1.5" fill="none"/>
                    <path d="M7 1.5A5.5 5.5 0 0112.5 7" stroke="var(--cream)" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
                  </svg>
                  Signing in…
                </span>
              ) : "Sign in"}
            </button>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
