const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

// FastAPI's error body isn't a single shape: most of our own handlers raise
// HTTPException with a plain string detail, but pydantic validation
// failures (422s) return detail as an array of {loc, msg, type} objects
// instead. Passing that array straight into ApiError's message meant a
// validation error like a password missing a lowercase letter rendered as
// "[object Object]" or crashed a component trying to display it — this
// normalizes both shapes into one readable string.
function extractErrorMessage(body: any): string {
  if (typeof body?.detail === "string") return body.detail;
  if (Array.isArray(body?.detail)) {
    return body.detail
      .map((e: any) => e?.msg ?? JSON.stringify(e))
      .join(" ");
  }
  return "An error occurred";
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
    throw new ApiError(extractErrorMessage(err), res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// Separate from request() because FormData needs the browser to set its
// own multipart Content-Type (with the boundary) — setting it manually,
// or forcing application/json like request() does, breaks the upload.
async function uploadRequest<T>(path: string, formData: FormData): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { method: "POST", headers, body: formData });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "An error occurred" }));
    throw new ApiError(extractErrorMessage(err), res.status);
  }
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
    verifyEmail: (token: string) =>
      request<import("@/types").User>("/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ token }),
      }),
    resendVerification: (email: string) =>
      request("/auth/resend-verification", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),
    forgotPassword: (email: string) =>
      request("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),
    resetPassword: (token: string, new_password: string) =>
      request<import("@/types").User>("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, new_password }),
      }),
    submitStudentId: (storageKey: string) =>
      request(`/auth/student-id?storage_key=${encodeURIComponent(storageKey)}`, {
        method: "POST",
      }, true),
  },

  media: {
    // purpose must match one of the backend's UploadPurpose values —
    // "student_id" is the only one currently used from the frontend.
    upload: (file: File, purpose: string) => {
      const formData = new FormData();
      formData.append("purpose", purpose);
      formData.append("file", file);
      return uploadRequest<{ storage_key: string; purpose: string }>("/media/upload", formData);
    },
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
    updateLogo: (storageKey: string) =>
      request<import("@/types").Business>(
        `/businesses/me/logo?storage_key=${encodeURIComponent(storageKey)}`, { method: "PATCH" }, true
      ),
    updateCover: (storageKey: string) =>
      request<import("@/types").Business>(
        `/businesses/me/cover?storage_key=${encodeURIComponent(storageKey)}`, { method: "PATCH" }, true
      ),
    addPortfolioItem: (data: { item_type: string; storage_key_or_url: string; caption?: string; display_order?: number }) =>
      request<import("@/types").PortfolioItem>(
        "/businesses/me/portfolio", { method: "POST", body: JSON.stringify(data) }, true
      ),
    removePortfolioItem: (itemId: string) =>
      request(`/businesses/me/portfolio/${itemId}`, { method: "DELETE" }, true),
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
    // auth=true here doesn't make sign-in required — the request()
    // helper only attaches an Authorization header when a token actually
    // exists, it never blocks the request for lacking one. Passing true
    // means: if the person happens to be signed in, the backend's
    // optional_bearer picks up their token and links the report to their
    // account (useful for admin follow-up); if not, it's omitted and the
    // report still goes through anonymously, exactly as the backend
    // (deliberately public, no-auth-required) supports.
    createReport: (data: { report_type: string; target_id: string; reason: string; details?: string }) =>
      request("/support/reports", { method: "POST", body: JSON.stringify(data) }, true),
    createTicket: (data: { ticket_type: string; subject: string; description: string }) =>
      request("/support/tickets", { method: "POST", body: JSON.stringify(data) }, true),
    myTickets: () =>
      request<import("@/types").SupportTicket[]>("/support/tickets/mine", {}, true),
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
    getStudentIdUrl: (userId: string) =>
      request<{ url: string; expires_in_seconds: number }>(
        `/admin/media/student-id-url?user_id=${encodeURIComponent(userId)}`, {}, true
      ),
    schools: {
      list: () => request("/admin/schools", {}, true),
      create: (data: { name: string; country: string; city: string; email_domain: string; logo_url?: string | null }) =>
        request("/admin/schools", { method: "POST", body: JSON.stringify(data) }, true),
      approve: (id: string) =>
        request(`/admin/schools/${id}/approve`, { method: "PATCH" }, true),
      suspend: (id: string) =>
        request(`/admin/schools/${id}/suspend`, { method: "PATCH" }, true),
    },
    businesses: {
      list: (status?: string) =>
        request(`/admin/businesses${status ? `?status=${status}` : ""}`, {}, true),
      get: (id: string) =>
        request(`/admin/businesses/${id}`, {}, true),
      approve: (id: string) =>
        request(`/admin/businesses/${id}/approve`, { method: "PATCH" }, true),
      suspend: (id: string) =>
        request(`/admin/businesses/${id}/suspend`, { method: "PATCH" }, true),
    },
    broadcast: (data: { subject: string; message: string; audience: string }) =>
      request<{ recipient_count: number; status: string }>(
        "/admin/broadcast", { method: "POST", body: JSON.stringify(data) }, true
      ),
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
    categories: {
      list: () => request<import("@/types").CategoryAdmin[]>("/admin/categories", {}, true),
      create: (data: { name: string; description?: string | null; icon_url?: string | null; display_order?: number }) =>
        request<import("@/types").CategoryAdmin>(
          "/admin/categories", { method: "POST", body: JSON.stringify(data) }, true
        ),
      update: (id: string, data: {
        name?: string; description?: string | null; icon_url?: string | null;
        display_order?: number; is_active?: boolean;
      }) =>
        request<import("@/types").CategoryAdmin>(
          `/admin/categories/${id}`, { method: "PATCH", body: JSON.stringify(data) }, true
        ),
      // There's no hard-delete endpoint by design: categories.id is
      // referenced by businesses.category_id with ON DELETE RESTRICT,
      // so the DB would reject deleting a category still in use.
      // "Removing" a category means deactivating it (is_active: false) —
      // it disappears from the public list and can't be selected for new
      // businesses, without breaking existing businesses that reference it.
      deactivate: (id: string) =>
        request<import("@/types").CategoryAdmin>(
          `/admin/categories/${id}`, { method: "PATCH", body: JSON.stringify({ is_active: false }) }, true
        ),
      activate: (id: string) =>
        request<import("@/types").CategoryAdmin>(
          `/admin/categories/${id}`, { method: "PATCH", body: JSON.stringify({ is_active: true }) }, true
        ),
    },
  },
};
