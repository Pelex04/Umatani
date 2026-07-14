import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Business logos/covers/portfolio/review photos are served from
    // Supabase Storage's public bucket. Wildcarding the subdomain covers
    // any project ref without needing to hardcode this specific project's
    // hostname (and needing a config change if that ever changes).
    remotePatterns: [
      { protocol: "https", hostname: "**.supabase.co", pathname: "/storage/v1/object/public/**" },
      { protocol: "https", hostname: "images.unsplash.com" },
    ],
  },
};

export default nextConfig;
