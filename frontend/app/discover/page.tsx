"use client";
import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useReferenceData } from "@/lib/referenceData";
import { BusinessCard } from "@/components/business/BusinessCard";
import { BusinessCardSkeleton } from "@/components/ui/Skeleton";
import type { BusinessListItem } from "@/types";

function DiscoverInner() {
  const sp     = useSearchParams();
  const router = useRouter();

  const [keyword,    setKeyword]    = useState(sp.get("keyword") ?? "");
  const [categoryId, setCategoryId] = useState(sp.get("category_id") ?? "");
  const [schoolId,   setSchoolId]   = useState(sp.get("school_id") ?? "");
  const [minRating,  setMinRating]  = useState(sp.get("min_rating") ?? "");
  const [showFilter, setShowFilter] = useState(false);

  const { categories, schools } = useReferenceData();
  const [results,    setResults]    = useState<BusinessListItem[]>([]);
  const [total,      setTotal]      = useState(0);
  const [loading,    setLoading]    = useState(true);
  const [offset,     setOffset]     = useState(0);
  const LIMIT = 18;

  const schoolMap = Object.fromEntries(schools.map(s => [s.id, s]));
  const catMap    = Object.fromEntries(categories.map(c => [c.id, c]));

  // Debounced separately from `keyword` itself: without this, doSearch's
  // dependency on keyword meant its identity changed on every keystroke,
  // which re-triggered the effect below on every keystroke too — a full
  // network request per character typed, not just on Enter/search-click
  // as the visible handlers suggested. requestId guards against an older,
  // slower response resolving after a newer one and overwriting it.
  const [debouncedKeyword, setDebouncedKeyword] = useState(keyword);
  useEffect(() => {
    const handle = setTimeout(() => setDebouncedKeyword(keyword), 400);
    return () => clearTimeout(handle);
  }, [keyword]);

  const requestIdRef = useRef(0);

  const doSearch = useCallback(async (off = 0, keywordOverride?: string) => {
    const thisRequestId = ++requestIdRef.current;
    setLoading(true);
    try {
      const res = await api.businesses.search({
        keyword: (keywordOverride ?? debouncedKeyword) || undefined,
        category_id: categoryId || undefined,
        school_id: schoolId || undefined,
        min_rating: minRating ? Number(minRating) : undefined,
        offset: off, limit: LIMIT,
      });
      if (thisRequestId !== requestIdRef.current) return; // a newer search superseded this one
      if (off === 0) setResults(res.items);
      else setResults(prev => [...prev, ...res.items]);
      setTotal(res.total);
      setOffset(off);
    } finally {
      if (thisRequestId === requestIdRef.current) setLoading(false);
    }
  }, [debouncedKeyword, categoryId, schoolId, minRating]);

  useEffect(() => { doSearch(0); }, [doSearch]);

  // Bypasses the debounce timer entirely — used when the person explicitly
  // hits Enter or clicks Search, so acting on their input is never slower
  // than just waiting, even mid-debounce.
  const searchNow = () => { setDebouncedKeyword(keyword); doSearch(0, keyword); };

  const activeFilters = [
    categoryId && catMap[categoryId]?.name,
    schoolId   && schoolMap[schoolId]?.name,
    minRating  && `${minRating}+ stars`,
  ].filter(Boolean) as string[];

  const S = { /* label */ L: { fontSize: 11, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase" as const, color: "#A8882E", display: "block", marginBottom: 6 } };

  return (
    <div style={{ minHeight: "100vh", background: "#F7F4EF" }}>
      {/* Sticky search bar */}
      <div style={{
        background: "white", borderBottom: "1px solid rgba(26,58,42,0.07)",
        position: "sticky", top: 58, zIndex: 30,
      }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "14px 24px" }}>
          <div className="discover-search-row" style={{ display: "flex", gap: 10 }}>
            <div style={{ position: "relative", flex: 1 }}>
              <svg width="15" height="15" viewBox="0 0 20 20" fill="none"
                style={{ position: "absolute", left: 13, top: "50%", transform: "translateY(-50%)", opacity: 0.4 }}>
                <circle cx="9" cy="9" r="6" stroke="#333" strokeWidth="1.8"/>
                <path d="M14 14l4 4" stroke="#333" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
              <input
                type="text" value={keyword}
                onChange={e => setKeyword(e.target.value)}
                onKeyDown={e => e.key === "Enter" && searchNow()}
                placeholder="Search businesses or services…"
                className="input"
                style={{ paddingLeft: 36 }}
              />
            </div>
            <button onClick={() => setShowFilter(!showFilter)}
              className="btn btn-outline"
              style={{ gap: 6, background: showFilter ? "#E8F0EA" : "", flexShrink: 0 }}>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M2 4h12M4 8h8M6 12h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              Filters
              {activeFilters.length > 0 && (
                <span style={{ background: "#1A3A2A", color: "#F7F4EF", fontSize: 10, fontWeight: 600, borderRadius: 100, padding: "1px 6px" }}>
                  {activeFilters.length}
                </span>
              )}
            </button>
            <button onClick={searchNow} className="btn btn-primary" style={{ flexShrink: 0 }}>
              Search
            </button>
          </div>

          {showFilter && (
            <div className="anim-in discover-filter-grid" style={{
              marginTop: 14, paddingTop: 14,
              borderTop: "1px solid rgba(26,58,42,0.07)",
              display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16,
            }}>
              <div>
                <span style={S.L}>Category</span>
                <select value={categoryId} onChange={e => setCategoryId(e.target.value)} className="input" style={{ fontSize: 13.5 }}>
                  <option value="">All categories</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <span style={S.L}>University</span>
                <select value={schoolId} onChange={e => setSchoolId(e.target.value)} className="input" style={{ fontSize: 13.5 }}>
                  <option value="">All universities</option>
                  {schools.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <span style={S.L}>Min rating</span>
                <select value={minRating} onChange={e => setMinRating(e.target.value)} className="input" style={{ fontSize: 13.5 }}>
                  <option value="">Any rating</option>
                  <option value="4">4+ stars</option>
                  <option value="3">3+ stars</option>
                </select>
              </div>
            </div>
          )}

          {activeFilters.length > 0 && (
            <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
              {categoryId && catMap[categoryId] && (
                <span className="badge badge-green" style={{ gap: 6 }}>
                  {catMap[categoryId].name}
                  <button onClick={() => setCategoryId("")} style={{ background: "none", border: "none", cursor: "pointer", padding: 0, lineHeight: 1, color: "#2B6438", fontSize: 14 }}>×</button>
                </span>
              )}
              {minRating && (
                <span className="badge badge-gold" style={{ gap: 6 }}>
                  {minRating}+ stars
                  <button onClick={() => setMinRating("")} style={{ background: "none", border: "none", cursor: "pointer", padding: 0, lineHeight: 1, color: "#A8882E", fontSize: 14 }}>×</button>
                </span>
              )}
              <button onClick={() => { setCategoryId(""); setSchoolId(""); setMinRating(""); setKeyword(""); }}
                style={{ fontSize: 12, color: "#E53935", background: "none", border: "none", cursor: "pointer", fontWeight: 500 }}>
                Clear all
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "32px 24px" }}>
        <p style={{ fontSize: 13, color: "#9CA3AF", marginBottom: 20 }}>
          {loading ? "Searching…" : total === 0 ? "No businesses found" : `${total} business${total === 1 ? "" : "es"} found`}
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
          {loading && results.length === 0
            ? Array.from({ length: 9 }).map((_, i) => <BusinessCardSkeleton key={i} />)
            : results.map(biz => (
                <BusinessCard key={biz.id} business={biz} school={schoolMap[biz.school_id]} category={catMap[biz.category_id]} />
              ))
          }
        </div>

        {!loading && total === 0 && (
          <div style={{ textAlign: "center", padding: "80px 0" }}>
            <p style={{ fontFamily: "var(--font-serif)", fontSize: 22, color: "#1A3A2A", marginBottom: 8 }}>Nothing found</p>
            <p style={{ fontSize: 14, color: "#9CA3AF" }}>Try different keywords or clear some filters.</p>
          </div>
        )}

        {!loading && results.length < total && (
          <div style={{ textAlign: "center", marginTop: 36 }}>
            <button onClick={() => doSearch(offset + LIMIT)} className="btn btn-outline" style={{ padding: "10px 32px" }}>
              Load more
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DiscoverPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: "100vh", background: "#F7F4EF", display: "flex", alignItems: "center", justifyContent: "center", color: "#9CA3AF" }}>Loading…</div>}>
      <DiscoverInner />
    </Suspense>
  );
}
