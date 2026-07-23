"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import type { School } from "@/types";

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [show, setShow] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [schoolId, setSchoolId] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  // Email → university matching. The backend resolves the domain to a
  // school without ever handing the frontend a list of valid domains —
  // this is the single source of truth, so there's nothing to keep in
  // sync here if a new university's extension gets added later.
  const [matchedSchool, setMatchedSchool] = useState<School | null>(null);
  const [matchStatus, setMatchStatus] = useState<"idle" | "checking" | "matched" | "unmatched">("idle");

  const emailFormatValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());

  useEffect(() => {
    if (!emailFormatValid) {
      setMatchedSchool(null);
      setMatchStatus("idle");
      return;
    }
    setMatchStatus("checking");
    const handle = setTimeout(() => {
      api.schools.matchByEmail(email.trim())
        .then(school => {
          setMatchedSchool(school);
          setMatchStatus(school ? "matched" : "unmatched");
          setSchoolId(school ? school.id : "");
        })
        .catch(() => {
          setMatchedSchool(null);
          setMatchStatus("unmatched");
        });
    }, 400); // debounce while the person is still typing
    return () => clearTimeout(handle);
  }, [email, emailFormatValid]);

  const checks = {
    len: password.length >= 10,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    num: /[0-9]/.test(password),
  };

  const next = (e: React.FormEvent) => {
    e.preventDefault(); setError("");
    if (step === 0) {
      if (!fullName.trim()) return setError("Full name is required.");
      if (!emailFormatValid) return setError("Enter a valid email address.");
      if (matchStatus === "checking") return setError("Still checking your email. One moment.");
      if (matchStatus !== "matched" || !matchedSchool) {
        return setError("This isn't a recognised university email address. Use your official student email.");
      }
    }
    if (step === 1 && !schoolId) return setError("Please select your university.");
    setStep(s => s + 1);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError("");
    if (!checks.len)         return setError("Password must be at least 10 characters.");
    if (!checks.upper)       return setError("Password needs an uppercase letter.");
    if (!checks.lower)       return setError("Password needs a lowercase letter.");
    if (!checks.num)         return setError("Password needs a number.");
    if (password !== confirm) return setError("Passwords do not match.");
    setLoading(true);
    try { await api.auth.register({ email, password, full_name: fullName, school_id: schoolId }); setDone(true); }
    catch (err: any) { setError(err.message ?? "Registration failed."); }
    finally { setLoading(false); }
  };

  if (done) return (
    <div style={{ minHeight: "calc(100vh - 58px)", display: "flex", alignItems: "center", justifyContent: "center", padding: 32, background: "var(--cream)" }}>
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, ease: [0.16,1,0.3,1] }}
        style={{ maxWidth: 420, width: "100%", textAlign: "center" }}>
        <div style={{ width: 64, height: 64, borderRadius: "50%", background: "var(--forest-100)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 28px" }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none"><path d="M5 12l5 5L19 7" stroke="var(--forest-600)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </div>
        <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 34, color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 10 }}>Check your email</h1>
        <p style={{ color: "var(--ink-muted)", fontSize: 14.5, lineHeight: 1.75, marginBottom: 12 }}>
          We sent a verification link to <strong style={{ color: "var(--forest)" }}>{email}</strong>. Click it to activate your account.
        </p>
        <div style={{ background: "var(--gold-pale)", border: "1px solid rgba(201,168,76,0.25)", borderRadius: 10, padding: "12px 16px", fontSize: 13, color: "var(--gold-dark)", marginBottom: 32, textAlign: "left" }}>
          Check your spam folder if you don't see it within a few minutes.
        </div>
        <Link href="/auth/login" className="btn btn-primary" style={{ fontSize: 14 }}>Go to sign in</Link>
      </motion.div>
    </div>
  );

  return (
    <div style={{ minHeight: "calc(100vh - 58px)", display: "flex" }}>
      {/* Left brand panel (hidden on mobile, shown on desktop — see .auth-brand-panel in globals.css) */}
      <div className="auth-brand-panel" style={{ flex: "0 0 46%", background: "var(--forest)", flexDirection: "column", justifyContent: "space-between", padding: "56px 60px", display: "none" }}>
        <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(247,244,239,0.12)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontWeight: 700, color: "var(--cream)", fontSize: 15 }}>u</span>
        </div>
        <div>
          <p className="eyebrow" style={{ color: "rgba(201,168,76,0.6)", marginBottom: 20 }}>Join Umata?</p>
          <h2 style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontWeight: 300, fontSize: 60, color: "var(--cream)", lineHeight: 0.9, letterSpacing: "-0.03em", marginBottom: 24 }}>
            Show Malawi<br />what you do.
          </h2>
          <p style={{ color: "rgba(247,244,239,0.4)", fontSize: 14.5, lineHeight: 1.75, maxWidth: 280 }}>
            Free for student entrepreneurs. Reach customers across your campus and beyond.
          </p>
        </div>
        <p style={{ color: "rgba(247,244,239,0.18)", fontSize: 11 }}>Always free · Malawi</p>
      </div>

      {/* Right form */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "56px 24px", background: "var(--cream)" }}>
        <div style={{ width: "100%", maxWidth: 380 }}>
          {/* Progress */}
          <div style={{ display: "flex", gap: 6, marginBottom: 40 }}>
            {["Details", "University", "Password"].map((s, i) => (
              <div key={s} style={{ flex: 1 }}>
                <div style={{ height: 3, borderRadius: 2, background: i <= step ? "var(--forest)" : "var(--border-med)", transition: "background 0.3s", marginBottom: 6 }} />
                <p style={{ fontSize: 10, fontWeight: i === step ? 600 : 400, color: i === step ? "var(--forest)" : "var(--ink-faint)", letterSpacing: "0.04em", textTransform: "uppercase" }}>{s}</p>
              </div>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {/* Step 0 */}
            {step === 0 && (
              <motion.div key="s0" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}>
                <p className="eyebrow" style={{ marginBottom: 10 }}>Step 1 of 3</p>
                <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 36, color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 6 }}>Your details</h1>
                <p style={{ fontSize: 13.5, color: "var(--ink-faint)", marginBottom: 36 }}>
                  Already registered?{" "}
                  <Link href="/auth/login" style={{ color: "var(--forest)", fontWeight: 500, textDecoration: "none" }}>Sign in</Link>
                </p>
                <form onSubmit={next} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  <div>
                    <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#374151", marginBottom: 7 }}>Full name</label>
                    <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Rasta Kadema" required className="input" />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#374151", marginBottom: 7 }}>School email</label>
                    <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@mubas.ac.mw" required className="input" />
                    {matchStatus === "idle" && (
                      <p style={{ fontSize: 11.5, color: "var(--ink-faint)", marginTop: 6 }}>Must be your official university email address</p>
                    )}
                    {matchStatus === "checking" && (
                      <p style={{ fontSize: 11.5, color: "var(--ink-faint)", marginTop: 6 }}>Checking university…</p>
                    )}
                    {matchStatus === "matched" && matchedSchool && (
                      <p style={{ fontSize: 11.5, color: "var(--forest-600)", marginTop: 6, fontWeight: 500 }}>
                        ✓ Recognised: {matchedSchool.name}
                      </p>
                    )}
                    {matchStatus === "unmatched" && (
                      <p style={{ fontSize: 11.5, color: "#C53030", marginTop: 6 }}>
                        This email domain isn't linked to a registered university yet.
                      </p>
                    )}
                  </div>
                  {error && <ErrorMsg msg={error} />}
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!fullName.trim() || matchStatus !== "matched"}
                    style={{ width: "100%", justifyContent: "center", padding: "13px", marginTop: 4, borderRadius: 11, opacity: (!fullName.trim() || matchStatus !== "matched") ? 0.55 : 1, cursor: (!fullName.trim() || matchStatus !== "matched") ? "not-allowed" : "pointer" }}
                  >
                    Continue
                  </button>
                </form>
              </motion.div>
            )}

            {/* Step 1 */}
            {step === 1 && (
              <motion.div key="s1" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}>
                <p className="eyebrow" style={{ marginBottom: 10 }}>Step 2 of 3</p>
                <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 36, color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 12 }}>Your university</h1>
                <p style={{ fontSize: 13.5, color: "var(--ink-faint)", marginBottom: 24 }}>
                  Detected from your email address, no need to pick it manually.
                </p>
                <form onSubmit={next} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  {matchedSchool ? (
                    <div style={{
                      padding: "16px 18px", borderRadius: 11, border: "1.5px solid var(--forest)",
                      background: "var(--forest-50)",
                    }}>
                      <div style={{ fontSize: 14.5, fontWeight: 500, color: "var(--forest)", marginBottom: 2 }}>{matchedSchool.name}</div>
                      <div style={{ fontSize: 12, color: "var(--ink-faint)" }}>{matchedSchool.city}, {matchedSchool.country}</div>
                    </div>
                  ) : (
                    <p style={{ fontSize: 13, color: "#C53030", padding: "20px 0", textAlign: "center" }}>
                      No university detected. Go back and check your email address.
                    </p>
                  )}
                  {error && <ErrorMsg msg={error} />}
                  <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
                    <button type="button" onClick={() => setStep(0)} className="btn btn-outline" style={{ flex: 1, justifyContent: "center" }}>Back</button>
                    <button type="submit" className="btn btn-primary" style={{ flex: 1, justifyContent: "center", padding: "13px", borderRadius: 11 }}>Continue</button>
                  </div>
                </form>
              </motion.div>
            )}

            {/* Step 2 */}
            {step === 2 && (
              <motion.div key="s2" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}>
                <p className="eyebrow" style={{ marginBottom: 10 }}>Step 3 of 3</p>
                <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 36, color: "var(--forest)", letterSpacing: "-0.025em", marginBottom: 36 }}>Set a password</h1>
                <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  <div>
                    <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#374151", marginBottom: 7 }}>Password</label>
                    <div style={{ position: "relative" }}>
                      <input type={show ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} placeholder="At least 10 characters" required className="input" style={{ paddingRight: 54 }} />
                      <button type="button" onClick={() => setShow(!show)} style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 10, fontWeight: 600, color: "var(--ink-faint)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                        {show ? "Hide" : "Show"}
                      </button>
                    </div>
                    <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                      {[["10+ chars", checks.len], ["Uppercase", checks.upper], ["Lowercase", checks.lower], ["Number", checks.num]].map(([l, ok]) => (
                        <span key={l as string} style={{ fontSize: 11, padding: "3px 9px", borderRadius: 100, fontWeight: 500, background: ok ? "var(--forest-100)" : "#F1F3F5", color: ok ? "var(--forest-600)" : "var(--ink-faint)", transition: "all 0.2s" }}>
                          {ok ? "✓" : "·"} {l}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#374151", marginBottom: 7 }}>Confirm password</label>
                    <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="Repeat your password" required className="input" />
                  </div>
                  {error && <ErrorMsg msg={error} />}
                  <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
                    <button type="button" onClick={() => setStep(1)} className="btn btn-outline" style={{ flex: 1, justifyContent: "center" }}>Back</button>
                    <button type="submit" disabled={loading} className="btn btn-primary" style={{ flex: 1, justifyContent: "center", padding: "13px", borderRadius: 11 }}>
                      {loading ? "Creating…" : "Create account"}
                    </button>
                  </div>
                </form>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

function ErrorMsg({ msg }: { msg: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
      style={{ background: "#FFF5F5", border: "1px solid #FED2D2", borderRadius: 10, padding: "10px 14px", fontSize: 13, color: "#C53030", display: "flex", alignItems: "center", gap: 8 }}>
      <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#C53030" strokeWidth="1.5"/><path d="M8 5v3.5M8 11h.01" stroke="#C53030" strokeWidth="1.5" strokeLinecap="round"/></svg>
      {msg}
    </motion.div>
  );
}
