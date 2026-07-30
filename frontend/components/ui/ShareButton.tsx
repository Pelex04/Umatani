"use client";
import { useState } from "react";

interface Props {
  title: string;
  text?: string;
  url: string;
  dark?: boolean;
  style?: React.CSSProperties;
  className?: string;
}

/**
 * Tries the native Web Share API first — this is what makes it "work
 * anywhere" on mobile: it hands off to the OS's own share sheet, which
 * already lists WhatsApp, Messages, Email, and whatever else is
 * installed, without this component needing to know about any of them
 * individually. Desktop browsers mostly don't support navigator.share,
 * so those fall back to copying the link to the clipboard instead —
 * still one tap, still works everywhere, just a different mechanism.
 */
export function ShareButton({ title, text, url, dark, style, className }: Props) {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    if (typeof navigator !== "undefined" && "share" in navigator) {
      try {
        await navigator.share({ title, text, url });
        return;
      } catch (err) {
        // AbortError just means the person closed the share sheet without
        // picking anything — not an error worth falling back or reporting.
        if (err instanceof Error && err.name === "AbortError") return;
      }
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API can fail in rare cases (e.g. permissions in an
      // embedded webview) — last-resort fallback so the button never
      // just silently does nothing.
      window.prompt("Copy this link:", url);
    }
  };

  const base = dark
    ? { color: "rgba(250,243,231,0.85)", background: "rgba(250,243,231,0.1)", borderColor: "rgba(250,243,231,0.2)" }
    : { color: "var(--forest)", background: "white", borderColor: "var(--border-med)" };
  const hover = dark
    ? { background: "rgba(250,243,231,0.18)", borderColor: "rgba(250,243,231,0.4)" }
    : { background: "rgba(67,8,31,0.03)", borderColor: "var(--forest)" };

  return (
    <button
      type="button"
      onClick={handleShare}
      className={className}
      style={{
        display: "inline-flex", alignItems: "center", gap: 7,
        fontFamily: "var(--font-sans)", fontSize: 13, fontWeight: 600,
        borderRadius: 2, border: "1px solid",
        padding: "10px 16px", cursor: "pointer", transition: "all 0.15s",
        color: base.color, background: base.background, borderColor: base.borderColor,
        ...style,
      }}
      onMouseEnter={e => { e.currentTarget.style.background = hover.background; e.currentTarget.style.borderColor = hover.borderColor; }}
      onMouseLeave={e => { e.currentTarget.style.background = base.background; e.currentTarget.style.borderColor = base.borderColor; }}
    >
      {copied ? (
        <>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 8.5l3.5 3.5L13 4.5" stroke={dark ? "#8FBF9B" : "#2F6B45"} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Link copied
        </>
      ) : (
        <>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M11.5 5a1.75 1.75 0 100-3.5 1.75 1.75 0 000 3.5zM4.5 9.75A1.75 1.75 0 104.5 6.25a1.75 1.75 0 000 3.5zM11.5 14.5a1.75 1.75 0 100-3.5 1.75 1.75 0 000 3.5z" stroke="currentColor" strokeWidth="1.4"/>
            <path d="M6 8.7l4-2.15M6 7.3l4 2.15" stroke="currentColor" strokeWidth="1.4"/>
          </svg>
          Share
        </>
      )}
    </button>
  );
}
