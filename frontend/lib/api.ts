const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = false
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "An error occurred" }));
    throw new ApiError(err.detail ?? "An error occurred", res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

// Auth
export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<{ access_token: string; refresh_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    register: (data: {
      email: string;
      password: string;
      full_name: string;
      school_id: string;
    }) => request("/auth/register", { method: "POST", body: JSON.stringify(data) }),
    me: () => request<import("@/types").User>("/auth/me", {}, true),
    logout: (refresh_token: string) =>
      request("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token }),
      }, true),
  },

  schools: {
    list: (search?: string) =>
      request<import("@/types").School[]>(
        `/schools${search ? `?search=${encodeURIComponent(search)}` : ""}`
      ),
    get: (id: string) => request<import("@/types").School>(`/schools/${id}`),
    // Resolves an email to its university by domain. A 404 here means
    // "no university matches this email" — an expected outcome while the
    // person is still typing, not a real error — so it resolves to null
    // instead of throwing.
    matchByEmail: async (email: string): Promise<import("@/types").School | null> => {
      try {
        return await request<import("@/types").School>(
          `/schools/match?email=${encodeURIComponent(email)}`
        );
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
      }
    },
  },

  categories: {
    list: () => request<import("@/types").Category[]>("/categories"),
  },

  businesses: {
    search: (params: {
      keyword?: string;
      category_id?: string;
      school_id?: string;
      min_rating?: number;
      offset?: number;
      limit?: number;
    }) => {
      const q = new URLSearchParams();
      if (params.keyword)     q.set("keyword", params.keyword);
      if (params.category_id) q.set("category_id", params.category_id);
      if (params.school_id)   q.set("school_id", params.school_id);
      if (params.min_rating)  q.set("min_rating", String(params.min_rating));
      if (params.offset)      q.set("offset", String(params.offset));
      if (params.limit)       q.set("limit", String(params.limit));
      return request<import("@/types").SearchResult>(
        `/businesses?${q.toString()}`
      );
    },
    get: (id: string) =>
      request<import("@/types").Business>(`/businesses/${id}`),
    getBySlug: (slug: string) =>
      request<import("@/types").Business>(`/businesses/slug/${slug}`),
    getMine: () =>
      request<import("@/types").Business>("/businesses/me", {}, true),
    create: (data: object) =>
      request("/businesses", { method: "POST", body: JSON.stringify(data) }, true),
    update: (data: object) =>
      request("/businesses/me", { method: "PATCH", body: JSON.stringify(data) }, true),
  },

  reviews: {
    list: (businessId: string, offset = 0, limit = 20) =>
      request<import("@/types").PaginatedReviews>(
        `/reviews?business_id=${businessId}&offset=${offset}&limit=${limit}`
      ),
    create: (data: object) =>
      request("/reviews", { method: "POST", body: JSON.stringify(data) }, true),
    reply: (reviewId: string, content: string) =>
      request(
        `/reviews/${reviewId}/reply`,
        { method: "POST", body: JSON.stringify({ content }) },
        true
      ),
  },

  support: {
    createReport: (data: object) =>
      request("/support/reports", { method: "POST", body: JSON.stringify(data) }),
    createTicket: (data: object) =>
      request("/support/tickets", { method: "POST", body: JSON.stringify(data) }, true),
  },

  admin: {
    stats: () =>
      request<import("@/types").PlatformStats>("/admin/stats", {}, true),
    users: (params?: { status?: string; offset?: number; limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.status) q.set("status", params.status);
      if (params?.offset) q.set("offset", String(params.offset));
      if (params?.limit)  q.set("limit", String(params.limit));
      return request<import("@/types").User[]>(`/admin/users?${q}`, {}, true);
    },
    verifyUser: (id: string) =>
      request(`/admin/users/${id}/verify`, { method: "PATCH" }, true),
    suspendUser: (id: string) =>
      request(`/admin/users/${id}/suspend`, { method: "PATCH" }, true),
    schools: {
      list: () => request("/admin/schools", {}, true),
      approve: (id: string) =>
        request(`/admin/schools/${id}/approve`, { method: "PATCH" }, true),
      suspend: (id: string) =>
        request(`/admin/schools/${id}/suspend`, { method: "PATCH" }, true),
    },
    businesses: {
      list: (status?: string) =>
        request(`/admin/businesses${status ? `?status=${status}` : ""}`, {}, true),
      approve: (id: string) =>
        request(`/admin/businesses/${id}/approve`, { method: "PATCH" }, true),
      suspend: (id: string) =>
        request(`/admin/businesses/${id}/suspend`, { method: "PATCH" }, true),
    },
    reviews: {
      flag: (id: string) =>
        request(`/admin/reviews/${id}/flag`, { method: "PATCH" }, true),
    },
    support: {
      reports: (status?: string) =>
        request(`/admin/support/reports${status ? `?status=${status}` : ""}`, {}, true),
      resolveReport: (id: string, data: object) =>
        request(`/admin/support/reports/${id}`, { method: "PATCH", body: JSON.stringify(data) }, true),
      tickets: () => request("/admin/support/tickets", {}, true),
      respondTicket: (id: string, data: object) =>
        request(`/admin/support/tickets/${id}`, { method: "PATCH", body: JSON.stringify(data) }, true),
    },
    auditLogs: () => request("/admin/audit-logs", {}, true),
  },
};
