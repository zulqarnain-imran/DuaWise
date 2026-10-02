import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sand: {
          50: "#fbf8f3",
          100: "#f5efe3",
          200: "#e9dcc7",
          300: "#d8c2a0",
          400: "#c2a074",
          500: "#b08651",
          600: "#9c7043",
          700: "#80593a",
          800: "#694a34",
          900: "#583e2e",
        },
        emerald: {
          50: "#ecfdf5",
          100: "#d1fae5",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        arabic: ["var(--font-arabic)", "Amiri", "Scheherazade New", "serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;
