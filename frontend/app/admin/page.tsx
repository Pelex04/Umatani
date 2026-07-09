"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatDate } from "@/lib/utils";
import type { PlatformStats } from "@/types";

type Tab = "overview"|"users"|"businesses"|"schools"|"reports"|"tickets";

const TABS: { key: Tab; label: string; stat?: keyof PlatformStats }[] = [
  { key: "overview",   label: "Overview" },
  { key: "users",      label: "Users",      stat: "pending_id_review" },
  { key: "businesses", label: "Businesses", stat: "pending_businesses" },
  { key: "schools",    label: "Schools" },
  { key: "reports",    label: "Reports",    stat: "open_reports" },
  { key: "tickets",    label: "Tickets",    stat: "open_tickets" },
];

export default function AdminDashboard() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [tab,     setTab]     = useState<Tab>("overview");
  const [stats,   setStats]   = useState<PlatformStats | null>(null);
  const [rows,    setRows]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting,  setActing]  = useState<string | null>(null);
  const [viewingId, setViewingId] = useState<string | null>(null);
  const [viewError, setViewError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) { router.push("/"); return; }
    if (!user) return;
    api.admin.stats().then(setStats).finally(() => setLoading(false));
  }, [user, authLoading]);

  const loadTab = async (t: Tab) => {
    setTab(t); setRows([]); setLoading(true);
    try {
      switch (t) {
        case "users":      setRows(await api.admin.users({ limit: 50 })); break;
        case "businesses": { const r = await api.admin.businesses.list("pending") as any; setRows(r.items ?? []); break; }
        case "schools":    setRows(await api.admin.schools.list() as any[]); break;
        case "reports":    setRows(await api.admin.support.reports() as any[]); break;
        case "tickets":    setRows(await api.admin.support.tickets() as any[]); break;
      }
    } finally { setLoading(false); }
  };

  const act = async (fn: () => Promise<any>, id: string) => {
    setActing(id); try { await fn(); await loadTab(tab); } finally { setActing(null); }
  };

  const viewStudentId = async (userId: string) => {
    setViewingId(userId); setViewError(null);
    try {
      const { url } = await api.admin.getStudentIdUrl(userId);
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (err: any) {
      setViewError(err.message ?? "Could not load this ID photo.");
    } finally {
      setViewingId(null);
    }
  };

  if (authLoading) return <AdminSkeleton />;
  if (!user || user.role !== "admin") return null;

  const statCards = stats ? [
    { label: "Users", value: stats.total_users, sub: `${stats.verified_users} verified`, alert: false },
    { label: "Pending ID review", value: stats.pending_id_review, sub: "awaiting verification", alert: stats.pending_id_review > 0 },
    { label: "Businesses", value: stats.total_businesses, sub: `${stats.approved_businesses} approved`, alert: false },
    { label: "Pending approval", value: stats.pending_businesses, sub: "need review", alert: stats.pending_businesses > 0 },
    { label: "Schools", value: stats.total_schools, sub: `${stats.approved_schools} active`, alert: false },
    { label: "Reviews", value: stats.total_reviews, sub: `${stats.flagged_reviews} flagged`, alert: stats.flagged_reviews > 0 },
    { label: "Open reports", value: stats.open_reports, sub: "need resolution", alert: stats.open_reports > 0 },
    { label: "Open tickets", value: stats.open_tickets, sub: "awaiting response", alert: stats.open_tickets > 0 },
  ] : [];

  return (
    <div style={{ minHeight: "100vh", background: "#F4F6F4" }}>
      {/* Header */}
      <div style={{ background: "var(--forest)" }}>
        <div style={{ maxWidth: 1120, margin: "0 auto", padding: "28px 28px 0" }}>
          <p style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(201,168,76,0.65)", marginBottom: 6 }}>Admin</p>
          <h1 style={{ fontFamily: "var(--font-serif)", fontWeight: 300, fontSize: 30, color: "var(--cream)", marginBottom: 24, letterSpacing: "-0.02em" }}>
            Control Panel
          </h1>
          {/* Tabs in header */}
          <div style={{ display: "flex", gap: 2, overflowX: "auto" }} className="scrollbar-hide">
            {TABS.map(t => {
              const count = t.stat ? (stats?.[t.stat] as number ?? 0) : 0;
              return (
                <button key={t.key} onClick={() => loadTab(t.key)} style={{
                  padding: "10px 18px", fontSize: 13, fontWeight: 500,
                  background: "none", border: "none", cursor: "pointer",
                  color: tab === t.key ? "var(--cream)" : "rgba(247,244,239,0.45)",
                  borderBottom: `2px solid ${tab === t.key ? "var(--gold)" : "transparent"}`,
                  transition: "all 0.15s", flexShrink: 0, fontFamily: "var(--font-sans)",
                  display: "flex", alignItems: "center", gap: 7, paddingBottom: 12,
                }}>
                  {t.label}
                  {count > 0 && <span style={{ background: tab === t.key ? "var(--gold)" : "rgba(255,255,255,0.12)", color: tab === t.key ? "var(--forest-800)" : "rgba(247,244,239,0.7)", fontSize: 10, fontWeight: 700, padding: "1px 6px", borderRadius: 100 }}>{count}</span>}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1120, margin: "0 auto", padding: "28px 28px 60px" }}>

        {/* Overview */}
        {tab === "overview" && (
          <div>
            {loading || !stats
              ? <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12 }}>{[1,2,3,4,5,6,7,8].map(i => <Skeleton key={i} h={88} r={12} />)}</div>
              : <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
                  style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12 }}>
                  {statCards.map((s, i) => (
                    <motion.div key={s.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                      style={{ background: s.alert && s.value > 0 ? "#FFFBFB" : "white", border: `1px solid ${s.alert && s.value > 0 ? "rgba(220,38,38,0.15)" : "var(--border)"}`, borderRadius: 12, padding: "16px" }}>
                      <p style={{ fontSize: 11, fontWeight: 500, color: "var(--ink-faint)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 8 }}>{s.label}</p>
                      <p style={{ fontFamily: "var(--font-serif)", fontSize: 32, fontWeight: 300, color: s.alert && s.value > 0 ? "#DC2626" : "var(--forest)", lineHeight: 1 }}>{s.value}</p>
                      <p style={{ fontSize: 11, color: "var(--ink-faint)", marginTop: 4 }}>{s.sub}</p>
                    </motion.div>
                  ))}
                </motion.div>
            }
          </div>
        )}

        {/* Users */}
        {tab === "users" && (
          <div>
            <p style={{ fontSize: 12.5, color: "var(--ink-faint)", marginBottom: 16 }}>{rows.length} users</p>
            {viewError && <p style={{ fontSize: 12.5, color: "#C53030", marginBottom: 12 }}>{viewError}</p>}
            {loading ? <TableSkeleton /> : (
              <div style={{ background: "white", border: "1px solid var(--border)", borderRadius: 14, overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border)", background: "#FAFAFA" }}>
                      {["Name","Email","Status","Role","Joined",""].map(h => (
                        <th key={h} style={{ padding: "11px 16px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--ink-faint)", letterSpacing: "0.07em", textTransform: "uppercase" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((u: any) => (
                      <tr key={u.id} style={{ borderBottom: "1px solid var(--border)" }}>
                        <td style={{ padding: "12px 16px", fontWeight: 500, color: "var(--forest)" }}>{u.full_name}</td>
                        <td style={{ padding: "12px 16px", color: "var(--ink-faint)", fontSize: 12 }}>{u.email}</td>
                        <td style={{ padding: "12px 16px" }}><StatusPill status={u.status} /></td>
                        <td style={{ padding: "12px 16px", color: "var(--ink-faint)", fontSize: 12, textTransform: "capitalize" }}>{u.role.replace("_"," ")}</td>
                        <td style={{ padding: "12px 16px", color: "var(--ink-faint)", fontSize: 12 }}>{formatDate(u.created_at)}</td>
                        <td style={{ padding: "12px 16px" }}>
                          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                            {u.status === "pending_id_review" && u.student_id_submitted && (
                              <button onClick={() => viewStudentId(u.id)} disabled={viewingId === u.id}
                                style={{ fontSize: 12, fontWeight: 500, color: "var(--forest-600)", background: "none", border: "1px solid var(--border-med)", borderRadius: 6, padding: "5px 12px", cursor: "pointer" }}>
                                {viewingId === u.id ? "Loading…" : "View ID"}
                              </button>
                            )}
                            {u.status === "pending_id_review" && u.student_id_submitted && (
                              <button onClick={() => act(() => api.admin.verifyUser(u.id), u.id)} disabled={acting === u.id}
                                style={{ fontSize: 12, fontWeight: 600, color: "var(--forest-600)", background: "var(--forest-100)", border: "none", borderRadius: 6, padding: "5px 12px", cursor: "pointer" }}>
                                {acting === u.id ? "…" : "Verify"}
                              </button>
                            )}
                            {u.status === "pending_id_review" && !u.student_id_submitted && (
                              <span style={{ fontSize: 12, color: "var(--ink-faint)", fontStyle: "italic" }}>Awaiting ID submission</span>
                            )}
                            {u.status !== "suspended" && (
                              <button onClick={() => act(() => api.admin.suspendUser(u.id), `${u.id}s`)} disabled={acting === `${u.id}s`}
                                style={{ fontSize: 12, color: "#DC2626", background: "none", border: "none", cursor: "pointer", fontWeight: 500 }}>Suspend</button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {rows.length === 0 && <p style={{ textAlign: "center", padding: "32px", color: "var(--ink-faint)", fontSize: 13.5 }}>No users found</p>}
              </div>
            )}
          </div>
        )}

        {/* Businesses */}
        {tab === "businesses" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <p style={{ fontSize: 12.5, color: "var(--ink-faint)", marginBottom: 6 }}>Pending approval</p>
            {loading ? <TableSkeleton /> : rows.length === 0
              ? <AllClear text="No businesses pending approval" />
              : rows.map((b: any) => (
                  <div key={b.id} style={{ background: "white", border: "1px solid var(--border)", borderRadius: 12, padding: "14px 16px", display: "flex", alignItems: "center", gap: 14 }}>
                    <div style={{ width: 40, height: 40, borderRadius: 10, background: "var(--forest-100)", color: "var(--forest)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-serif)", fontWeight: 700, fontSize: 16, flexShrink: 0 }}>{b.name[0]}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontWeight: 500, color: "var(--forest)", fontSize: 13.5, marginBottom: 2 }}>{b.name}</p>
                      <p style={{ fontSize: 12, color: "var(--ink-faint)" }} className="lc-1">{b.description}</p>
                    </div>
                    <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                      <button onClick={() => act(() => api.admin.businesses.approve(b.id), `${b.id}a`)} disabled={!!acting}
                        style={{ fontSize: 12.5, fontWeight: 600, background: "var(--forest)", color: "var(--cream)", border: "none", borderRadius: 8, padding: "7px 16px", cursor: "pointer", display: "flex", alignItems: "center", gap: 5 }}>
                        {acting === `${b.id}a` ? "…" : "Approve"}
                      </button>
                      <button onClick={() => act(() => api.admin.businesses.suspend(b.id), `${b.id}s`)} disabled={!!acting}
                        style={{ fontSize: 12.5, fontWeight: 500, background: "#FFF0F0", color: "#DC2626", border: "1px solid #FED2D2", borderRadius: 8, padding: "7px 14px", cursor: "pointer" }}>
                        Reject
                      </button>
                    </div>
                  </div>
                ))
            }
          </div>
        )}

        {/* Schools */}
        {tab === "schools" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {loading ? <TableSkeleton /> : rows.map((s: any) => (
              <div key={s.id} style={{ background: "white", border: "1px solid var(--border)", borderRadius: 12, padding: "14px 16px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
                <div>
                  <p style={{ fontWeight: 500, color: "var(--forest)", fontSize: 13.5, marginBottom: 2 }}>{s.name}</p>
                  <p style={{ fontSize: 12, color: "var(--ink-faint)" }}>{s.city}, {s.country} · @{s.email_domain}</p>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
                  <StatusPill status={s.status} />
                  {s.status !== "approved"
                    ? <button onClick={() => act(() => api.admin.schools.approve(s.id), s.id)} disabled={acting === s.id} style={{ fontSize: 12.5, fontWeight: 600, background: "var(--forest)", color: "var(--cream)", border: "none", borderRadius: 8, padding: "7px 16px", cursor: "pointer" }}>{acting === s.id ? "…" : "Approve"}</button>
                    : <button onClick={() => act(() => api.admin.schools.suspend(s.id), s.id)} disabled={acting === s.id} style={{ fontSize: 12.5, color: "#DC2626", background: "none", border: "none", cursor: "pointer", fontWeight: 500 }}>Suspend</button>
                  }
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Reports */}
        {tab === "reports" && (
          <div>
            {loading ? <TableSkeleton /> : rows.length === 0
              ? <AllClear text="No open reports" />
              : <div style={{ background: "white", border: "1px solid var(--border)", borderRadius: 14, overflow: "hidden" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead><tr style={{ borderBottom: "1px solid var(--border)", background: "#FAFAFA" }}>
                      {["Type","Reason","Status","Date",""].map(h => <th key={h} style={{ padding: "11px 16px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--ink-faint)", letterSpacing: "0.07em", textTransform: "uppercase" }}>{h}</th>)}
                    </tr></thead>
                    <tbody>{rows.map((r: any) => (
                      <tr key={r.id} style={{ borderBottom: "1px solid var(--border)" }}>
                        <td style={{ padding: "12px 16px" }}><span style={{ fontSize: 11, fontWeight: 500, padding: "3px 8px", borderRadius: 6, background: "#F1F3F5", color: "#4B5563", textTransform: "capitalize" }}>{r.report_type}</span></td>
                        <td style={{ padding: "12px 16px", color: "var(--ink-muted)", maxWidth: 280 }} className="lc-1">{r.reason}</td>
                        <td style={{ padding: "12px 16px" }}><StatusPill status={r.status} /></td>
                        <td style={{ padding: "12px 16px", color: "var(--ink-faint)", fontSize: 12 }}>{formatDate(r.created_at)}</td>
                        <td style={{ padding: "12px 16px" }}>
                          {r.status === "open" && <div style={{ display: "flex", gap: 10 }}>
                            <button onClick={() => act(() => api.admin.support.resolveReport(r.id, { status: "resolved" }), r.id)} disabled={!!acting} style={{ fontSize: 12, color: "var(--forest-600)", fontWeight: 600, background: "none", border: "none", cursor: "pointer" }}>Resolve</button>
                            <button onClick={() => act(() => api.admin.support.resolveReport(r.id, { status: "dismissed" }), `${r.id}d`)} disabled={!!acting} style={{ fontSize: 12, color: "var(--ink-faint)", background: "none", border: "none", cursor: "pointer" }}>Dismiss</button>
                          </div>}
                        </td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
            }
          </div>
        )}

        {/* Tickets */}
        {tab === "tickets" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {loading ? <TableSkeleton /> : rows.length === 0
              ? <AllClear text="No open tickets" />
              : rows.map((t: any) => (
                  <div key={t.id} style={{ background: "white", border: "1px solid var(--border)", borderRadius: 12, padding: 16 }}>
                    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, marginBottom: 8 }}>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <StatusPill status={t.status} />
                        <span style={{ fontSize: 11, fontWeight: 500, padding: "3px 8px", borderRadius: 6, background: "#F1F3F5", color: "#4B5563", textTransform: "capitalize" }}>{t.ticket_type.replace("_"," ")}</span>
                      </div>
                      <span style={{ fontSize: 11.5, color: "var(--ink-faint)", flexShrink: 0 }}>{formatDate(t.created_at)}</span>
                    </div>
                    <p style={{ fontWeight: 500, fontSize: 13.5, color: "var(--forest)", marginBottom: 4 }}>{t.subject}</p>
                    <p style={{ fontSize: 13, color: "var(--ink-faint)", lineHeight: 1.65 }} className="lc-2">{t.description}</p>
                    {t.admin_response && (
                      <div style={{ marginTop: 10, background: "var(--forest-50)", borderLeft: "3px solid var(--forest-400)", borderRadius: "0 8px 8px 0", padding: "8px 12px", fontSize: 12.5, color: "var(--ink-muted)" }}>
                        <strong style={{ color: "var(--forest)" }}>Response: </strong>{t.admin_response}
                      </div>
                    )}
                    {t.status === "open" && (
                      <button onClick={() => act(() => api.admin.support.respondTicket(t.id, { status: "resolved", admin_response: "Thank you for reaching out. This has been noted and resolved." }), t.id)}
                        disabled={acting === t.id}
                        style={{ marginTop: 12, fontSize: 12, fontWeight: 500, color: "var(--forest-600)", background: "var(--forest-100)", border: "none", borderRadius: 7, padding: "6px 14px", cursor: "pointer" }}>
                        {acting === t.id ? "Resolving…" : "Mark resolved"}
                      </button>
                    )}
                  </div>
                ))
            }
          </div>
        )}
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, [string,string]> = {
    approved:  ["#E8F0EA","#2B6438"], verified:  ["#E8F0EA","#2B6438"], resolved: ["#E8F0EA","#2B6438"],
    pending:   ["#FBF4E0","#A8882E"], pending_id_review: ["#FBF4E0","#A8882E"], open: ["#FBF4E0","#A8882E"],
    suspended: ["#FFF0F0","#DC2626"], dismissed: ["#F1F3F5","#6B7280"],
    pending_email_verification: ["#F1F3F5","#6B7280"], in_progress: ["#EEF2FF","#4338CA"],
  };
  const [bg, color] = map[status] ?? ["#F1F3F5","#6B7280"];
  return <span style={{ background: bg, color, fontSize: 11, fontWeight: 600, padding: "3px 9px", borderRadius: 100, textTransform: "capitalize", whiteSpace: "nowrap" }}>{status.replace(/_/g," ")}</span>;
}
function TableSkeleton() { return <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>{[1,2,3,4,5].map(i => <Skeleton key={i} h={52} r={10} />)}</div>; }
function AllClear({ text }: { text: string }) { return <div style={{ textAlign: "center", padding: "56px 0" }}><p style={{ fontFamily: "var(--font-serif)", fontSize: 22, color: "var(--forest)", fontWeight: 300, marginBottom: 6 }}>All clear</p><p style={{ fontSize: 13.5, color: "var(--ink-faint)" }}>{text}</p></div>; }
function AdminSkeleton() { return <div style={{ minHeight: "100vh", background: "#F4F6F4" }}><div style={{ background: "var(--forest)", height: 120 }} /><div style={{ maxWidth: 1120, margin: "0 auto", padding: 28 }}><div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12 }}>{[1,2,3,4,5,6,7,8].map(i => <Skeleton key={i} h={88} r={12} />)}</div></div></div>; }
