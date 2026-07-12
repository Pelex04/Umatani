"use client";
/**
 * Schools and categories are near-static reference data — 6 universities,
 * 12 categories, changed by an admin maybe a few times ever. Before this,
 * every page (home, discover, business detail, dashboard) independently
 * re-fetched both lists from scratch on every navigation. Combined with
 * CORS preflight (this is a cross-origin setup, so every GET is really two
 * round trips: an OPTIONS then the request) and cross-region backend/DB
 * latency, that meant paying multiple redundant full network round trips
 * on every single page load for data that's essentially always the same —
 * a real, compounding, universally-felt source of slowness independent of
 * any specific page's content.
 *
 * Fetched once here, at the root layout, and reused everywhere via
 * useReferenceData() instead of each page calling the API directly.
 */
import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api } from "./api";
import type { School, Category } from "@/types";

interface ReferenceDataCtx {
  schools: School[];
  categories: Category[];
  loading: boolean;
  schoolById: (id: string) => School | undefined;
  categoryById: (id: string) => Category | undefined;
}

const Ctx = createContext<ReferenceDataCtx | null>(null);

export function ReferenceDataProvider({ children }: { children: ReactNode }) {
  const [schools, setSchools] = useState<School[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.schools.list(), api.categories.list()])
      .then(([schs, cats]) => { setSchools(schs); setCategories(cats); })
      .finally(() => setLoading(false));
  }, []);

  const schoolById = (id: string) => schools.find(s => s.id === id);
  const categoryById = (id: string) => categories.find(c => c.id === id);

  return (
    <Ctx.Provider value={{ schools, categories, loading, schoolById, categoryById }}>
      {children}
    </Ctx.Provider>
  );
}

export function useReferenceData() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useReferenceData must be used within ReferenceDataProvider");
  return ctx;
}
