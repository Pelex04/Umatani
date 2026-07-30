import type { Metadata } from "next";
import BusinessProfileClient from "./BusinessProfileClient";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function fetchBusinessForMetadata(slug: string) {
  try {
    const res = await fetch(`${API_BASE}/businesses/slug/${slug}`, {
      // Metadata is fetched on every request rather than cached at build
      // time — business info (rating, availability, description) changes
      // often enough that a stale share preview would be worse than the
      // extra request.
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata(
  { params }: { params: Promise<{ slug: string }> }
): Promise<Metadata> {
  const { slug } = await params;
  const biz = await fetchBusinessForMetadata(slug);

  if (!biz) {
    return { title: "Business not found" };
  }

  const description = biz.description?.length > 160
    ? `${biz.description.slice(0, 157)}...`
    : biz.description || `${biz.name} on Umata? — a verified student business.`;

  const image = biz.cover_url || biz.logo_url;

  return {
    title: biz.name,
    description,
    openGraph: {
      title: biz.name,
      description,
      url: `/businesses/${slug}`,
      type: "profile",
      ...(image ? { images: [{ url: image, width: 1200, height: 630, alt: biz.name }] } : {}),
    },
    twitter: {
      card: image ? "summary_large_image" : "summary",
      title: biz.name,
      description,
      ...(image ? { images: [image] } : {}),
    },
  };
}

export default function Page() {
  return <BusinessProfileClient />;
}
