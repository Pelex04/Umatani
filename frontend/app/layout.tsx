import type { Metadata } from "next";
import { Plus_Jakarta_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { ReferenceDataProvider } from "@/lib/referenceData";
import { Header } from "@/components/layout/Header";

// Direction 3: one typeface across the whole system instead of a
// serif+sans pairing (Fraunces+Inter was the previous setup — that
// pairing has become extremely common as an "AI-tool default", which
// was a big part of the original complaint). Plus Jakarta Sans is
// mapped to BOTH --font-serif and --font-sans so every existing
// var(--font-serif) reference throughout the app repoints to it
// automatically, rather than needing every call site individually
// changed for the same visual outcome. IBM Plex Mono is new: used
// sparingly for actual data (ratings, prices, stats) only, never
// decoratively, adding texture without becoming a second pairing.
const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  variable: "--font-sans",
  display: "swap",
});
const jakartaAsSerif = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  variable: "--font-serif",
  display: "swap",
});
const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://www.umata.site"),
  title: { default: "Umata? · Student Business Discovery", template: "%s · Umata?" },
  description: "Discover trusted student entrepreneurs at Malawian universities. Find graphic designers, photographers, bakers, programmers and more.",
  openGraph: {
    siteName: "Umata?",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${jakarta.variable} ${jakartaAsSerif.variable} ${plexMono.variable}`}>
      <body>
        <AuthProvider>
          <ReferenceDataProvider>
            <Header />
            {children}
          </ReferenceDataProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
