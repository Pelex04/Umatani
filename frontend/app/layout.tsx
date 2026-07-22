import type { Metadata } from "next";
import { Fraunces, Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { ReferenceDataProvider } from "@/lib/referenceData";
import { Header } from "@/components/layout/Header";

// Previously loaded via `@import url('https://fonts.googleapis.com/...')`
// inside globals.css — CSS @import is render-blocking and sequential: the
// browser has to fetch and parse the main stylesheet, discover the
// @import, open a fresh connection to a third-party origin (DNS + TLS),
// fetch Google's CSS, parse *that*, discover the actual font file URLs,
// then fetch those — all before text renders correctly. That waterfall
// hit every single page load for every visitor, making it very likely
// the single biggest hit to how fast the site *feels*, independent of
// anything already fixed. next/font downloads the font files at build
// time and self-hosts them from the app's own origin instead — no
// third-party request at all, automatic font-display: swap, and it
// exposes the same --font-serif/--font-sans variable names the rest of
// the CSS already uses, so nothing else needs to change.
const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["300", "400", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-serif",
  display: "swap",
});
const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "UMATANI · Student Business Discovery", template: "%s · UMATANI" },
  description: "Discover trusted student entrepreneurs at Malawian universities. Find graphic designers, photographers, bakers, programmers and more.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${inter.variable}`}>
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
