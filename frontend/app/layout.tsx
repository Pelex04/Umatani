import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { Header } from "@/components/layout/Header";

export const metadata: Metadata = {
  title: { default: "UMATANI — Student Business Discovery", template: "%s · UMATANI" },
  description: "Discover trusted student entrepreneurs at Malawian universities. Find graphic designers, photographers, bakers, programmers and more.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <Header />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
