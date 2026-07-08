import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          50:  "#F0F5F1",
          100: "#E8F0EA",
          200: "#C8DCC C",
          300: "#9DC4A4",
          400: "#6BA578",
          500: "#3D8050",
          600: "#2B6438",
          700: "#1A3A2A",
          800: "#122619",
          900: "#0A160F",
        },
        gold: {
          100: "#FBF4E0",
          300: "#E8CC7A",
          400: "#C9A84C",
          500: "#A8882E",
          600: "#856A1A",
        },
        slate: {
          50:  "#F8F9FA",
          100: "#F1F3F5",
          200: "#E9ECEF",
          300: "#DEE2E6",
          400: "#CED4DA",
          500: "#ADB5BD",
          600: "#6C757D",
          700: "#495057",
          800: "#3D4852",
          900: "#212529",
        },
        cream: "#F7F4EF",
        sage:  "#E8F0EA",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        body:    ["Inter", "system-ui", "sans-serif"],
        mono:    ["JetBrains Mono", "Menlo", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }],
      },
      borderRadius: {
        "4xl": "2rem",
      },
      boxShadow: {
        card:    "0 1px 3px 0 rgba(26,58,42,0.06), 0 1px 2px -1px rgba(26,58,42,0.06)",
        "card-hover": "0 4px 16px 0 rgba(26,58,42,0.12), 0 2px 4px -1px rgba(26,58,42,0.08)",
        gold:    "0 0 0 3px rgba(201,168,76,0.25)",
      },
      animation: {
        "fade-up":    "fadeUp 0.4s ease-out both",
        "fade-in":    "fadeIn 0.3s ease-out both",
        "scale-in":   "scaleIn 0.2s ease-out both",
        "shimmer":    "shimmer 1.8s infinite",
      },
      keyframes: {
        fadeUp: {
          from: { opacity: "0", transform: "translateY(12px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
        scaleIn: {
          from: { opacity: "0", transform: "scale(0.95)" },
          to:   { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
