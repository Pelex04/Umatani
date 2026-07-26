export interface School {
  id: string;
  name: string;
  country: string;
  city: string;
  logo_url: string | null;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  icon_url: string | null;
  display_order: number;
}

export interface Service {
  id: string;
  name: string;
  description: string | null;
  price_range: string | null;
  display_order: number;
}

export interface PortfolioItem {
  id: string;
  item_type: "image" | "video_link" | "document" | "external_link";
  display_url: string;
  caption: string | null;
  display_order: number;
  created_at: string;
}

export interface ReviewReply {
  id: string;
  content: string;
  created_at: string;
}

export interface Review {
  id: string;
  business_id: string;
  reviewer_id: string;
  rating: number;
  comment: string;
  service_received: string | null;
  created_at: string;
  photos: { id: string; storage_key: string }[];
  reply: ReviewReply | null;
}

export interface Business {
  id: string;
  name: string;
  slug: string;
  description: string;
  school_id: string;
  category_id: string;
  logo_url: string | null;
  cover_url: string | null;
  whatsapp: string | null;
  phone: string | null;
  contact_email: string | null;
  website: string | null;
  instagram: string | null;
  twitter: string | null;
  facebook: string | null;
  tiktok: string | null;
  is_available: boolean;
  average_rating: number;
  review_count: number;
  created_at: string;
  services: Service[];
  portfolio_items: PortfolioItem[];
  status?: string;
  owner_id?: string;
}

export interface BusinessListItem {
  id: string;
  name: string;
  slug: string;
  description: string;
  school_id: string;
  category_id: string;
  logo_url: string | null;
  is_available: boolean;
  average_rating: number;
  review_count: number;
  created_at: string;
}

export interface SearchResult {
  total: number;
  offset: number;
  limit: number;
  items: BusinessListItem[];
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "business_owner" | "admin";
  status: "pending_email_verification" | "pending_id_review" | "verified" | "suspended";
  school_id: string | null;
  student_id_submitted: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PaginatedReviews {
  total: number;
  offset: number;
  limit: number;
  items: Review[];
}

export interface PlatformStats {
  total_users: number;
  verified_users: number;
  pending_id_review: number;
  total_businesses: number;
  pending_businesses: number;
  approved_businesses: number;
  total_schools: number;
  approved_schools: number;
  total_reviews: number;
  flagged_reviews: number;
  open_reports: number;
  open_tickets: number;
}

export interface SupportTicket {
  id: string;
  ticket_type: "support" | "feature_request";
  subject: string;
  description: string;
  status: "open" | "in_progress" | "resolved" | "closed";
  admin_response: string | null;
  created_at: string;
  updated_at: string;
}
