"use client";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [menu,   setMenu]   = useState(false);
  const [mobile, setMobile] = useState(false);

  const handleLogout = async () => {
    setMenu(false);
    await logout();
    router.push("/");
  };

  const navLink = (label: string, href: string) => (
    <Link key={href} href={href} onClick={() => setMobile(false)} style={{
      display: "block", textDecoration: "none", fontSize: 13.5, fontWeight: 500,
      color: "#4B5563", padding: "7px 12px", borderRadius: 8,
      transition: "background 0.15s, color 0.15s",
    }}
    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "var(--forest-100)"; (e.currentTarget as HTMLElement).style.color = "var(--forest)"; }}
    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = ""; (e.currentTarget as HTMLElement).style.color = "#4B5563"; }}>
      {label}
    </Link>
  );

  return (
    <>
      <header style={{
        position: "sticky", top: 0, zIndex: 50,
        background: "rgba(247,244,239,0.94)",
        backdropFilter: "blur(14px)",
        borderBottom: "1px solid rgba(26,58,42,0.07)",
      }}>
        <div style={{
          maxWidth: 1200, margin: "0 auto",
          padding: "0 24px", height: 58,
          display: "flex", alignItems: "center", justifyContent: "space-between",
          gap: 16,
        }}>
          {/* Logo */}
          <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            <div style={{
              width: 26, height: 26, borderRadius: 7,
              background: "var(--forest)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <span style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontWeight: 700, color: "var(--cream)", fontSize: 13, lineHeight: 1 }}>u</span>
            </div>
            <span style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontWeight: 700, color: "var(--forest)", fontSize: 18, letterSpacing: "-0.025em", lineHeight: 1 }}>
              umatani
            </span>
          </Link>

          {/* Desktop nav */}
          <nav style={{ display: "flex", gap: 2, flex: 1, justifyContent: "center" }}>
            {navLink("Discover", "/discover")}
          </nav>

          {/* Right actions */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            {!user ? (
              <>
                <Link href="/auth/login" style={{
                  textDecoration: "none", fontSize: 13.5, fontWeight: 500, color: "#4B5563",
                  padding: "7px 12px", borderRadius: 8, transition: "all 0.15s",
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "var(--forest-100)"; (e.currentTarget as HTMLElement).style.color = "var(--forest)"; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = ""; (e.currentTarget as HTMLElement).style.color = "#4B5563"; }}>
                  Sign in
                </Link>
                <Link href="/auth/register" className="btn btn-primary" style={{ fontSize: 13, padding: "8px 16px" }}>
                  List your business
                </Link>
              </>
            ) : (
              <div style={{ position: "relative" }}>
                <button onClick={() => setMenu(!menu)} style={{
                  display: "flex", alignItems: "center", gap: 7,
                  padding: "6px 10px", borderRadius: 10,
                  border: "none", background: "transparent", cursor: "pointer",
                  transition: "background 0.15s",
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "var(--forest-100)")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
                  <div style={{
                    width: 28, height: 28, borderRadius: "50%",
                    background: "var(--forest)", color: "var(--cream)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 11.5, fontWeight: 600, fontFamily: "var(--font-sans)",
                  }}>
                    {user.full_name[0].toUpperCase()}
                  </div>
                  <span style={{ fontSize: 13.5, fontWeight: 500, color: "#374151" }}>
                    {user.full_name.split(" ")[0]}
                  </span>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
                    style={{ transform: menu ? "rotate(180deg)" : "", transition: "transform 0.2s" }}>
                    <path d="M2 4l4 4 4-4" stroke="#9CA3AF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>

                {menu && (
                  <>
                    <div style={{ position: "fixed", inset: 0, zIndex: 10 }} onClick={() => setMenu(false)} />
                    <div style={{
                      position: "absolute", right: 0, top: "calc(100% + 8px)", zIndex: 20,
                      width: 200, background: "white", borderRadius: 12,
                      border: "1px solid rgba(26,58,42,0.09)",
                      boxShadow: "0 8px 28px rgba(0,0,0,0.1), 0 2px 8px rgba(0,0,0,0.06)",
                      overflow: "hidden", animation: "scaleIn 0.15s ease-out",
                    }}>
                      <div style={{ padding: "12px 14px", borderBottom: "1px solid var(--border)" }}>
                        <p style={{ fontSize: 12.5, fontWeight: 600, color: "var(--forest)", marginBottom: 1 }}>{user.full_name}</p>
                        <p style={{ fontSize: 11.5, color: "var(--ink-faint)" }}>{user.role.replace("_", " ")}</p>
                      </div>
                      <div style={{ padding: 6 }}>
                        <Link href={user.role === "admin" ? "/admin" : "/dashboard"} onClick={() => setMenu(false)}
                          style={{ display: "flex", alignItems: "center", gap: 9, padding: "9px 10px", borderRadius: 8, fontSize: 13, color: "#374151", textDecoration: "none", fontWeight: 500, transition: "background 0.12s" }}
                          onMouseEnter={e => (e.currentTarget.style.background = "var(--forest-50)")}
                          onMouseLeave={e => (e.currentTarget.style.background = "")}>
                          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.4"/><rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.4"/><rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.4"/><rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.4"/></svg>
                          {user.role === "admin" ? "Admin panel" : "Dashboard"}
                        </Link>
                        <button onClick={handleLogout} style={{
                          width: "100%", display: "flex", alignItems: "center", gap: 9,
                          padding: "9px 10px", borderRadius: 8, fontSize: 13, color: "#DC2626",
                          background: "none", border: "none", cursor: "pointer", fontWeight: 500,
                          textAlign: "left", fontFamily: "var(--font-sans)", transition: "background 0.12s",
                        }}
                        onMouseEnter={e => (e.currentTarget.style.background = "#FFF5F5")}
                        onMouseLeave={e => (e.currentTarget.style.background = "")}>
                          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M10 3h3a1 1 0 011 1v8a1 1 0 01-1 1h-3M7 10l3-3-3-3M10 8H2" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
                          Sign out
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Mobile menu button */}
            <button onClick={() => setMobile(!mobile)} style={{
              display: "none", background: "none", border: "none", cursor: "pointer",
              padding: 6, borderRadius: 8, color: "#4B5563",
            }} className="mobile-menu-btn">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                {mobile
                  ? <path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
                  : <><path d="M3 6h14M3 10h14M3 14h14" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/></>
                }
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        {mobile && (
          <div style={{ borderTop: "1px solid var(--border)", padding: "10px 16px 14px", background: "rgba(247,244,239,0.98)" }}>
            {navLink("Discover", "/discover")}
            {!user && navLink("Sign in", "/auth/login")}
            {user && navLink(user.role === "admin" ? "Admin panel" : "Dashboard", user.role === "admin" ? "/admin" : "/dashboard")}
          </div>
        )}
      </header>

      <style>{`
        @media (max-width: 640px) {
          .mobile-menu-btn { display: flex !important; }
          nav { display: none !important; }
        }
      `}</style>
    </>
  );
}
