import type { Metadata, Viewport } from "next";
import { ServiceWorkerRegistration } from "../components/ServiceWorkerRegistration";
import "./globals.css";

export const metadata: Metadata = {
  title: "DuaWise — Advanced Context-Aware Dua Recommendation",
  description:
    "An advanced context-aware Dua recommendation system that maps free-text life situations to cited Duas using TF-IDF, semantic embeddings (SBERT), hybrid fusion, and context-aware ranking. Features multi-language support (Arabic, English, Urdu), explainable AI, and grounded citations.",
  applicationName: "DuaWise",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "DuaWise", statusBarStyle: "default" },
  keywords: [
    "Dua",
    "Islamic prayer",
    "context-aware recommendation",
    "information retrieval",
    "semantic search",
    "sentence embeddings",
    "explainable AI",
    "data science",
    "intelligent systems",
    "Arabic",
    "Urdu",
    "English",
  ],
  authors: [{ name: "DuaWise" }],
};

export const viewport: Viewport = {
  themeColor: "#ecfdf5",
  width: "device-width",
  initialScale: 1,
};

const DISCLAIMER =
  "DuaWise surfaces Duas from cited sources for personal reflection. It does not generate religious text, guarantee an outcome, or issue religious rulings. Always verify wording and attribution against the original source.";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-emerald-700 focus:px-4 focus:py-2 focus:text-white"
        >
          Skip to content
        </a>
        <div className="relative flex min-h-screen flex-col">
          <main className="flex-grow">{children}</main>
          <ServiceWorkerRegistration />
          <footer className="mt-16 border-t border-sand-200/60 bg-gradient-to-b from-white/95 to-sand-50/95 backdrop-blur-xl">
            <div className="mx-auto max-w-6xl px-4 py-10 text-sm text-sand-700">
              <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
                <div className="space-y-3">
                  <p className="gradient-text text-base font-bold">DuaWise</p>
                  <p className="leading-relaxed">{DISCLAIMER}</p>
                </div>
                <div className="space-y-3">
                  <p className="font-semibold text-sand-900">
                    Data Science &amp; Intelligent Systems
                  </p>
                  <p className="leading-relaxed">
                    Advanced IR with TF-IDF + cosine, SBERT semantic embeddings, hybrid fusion, and structured context-aware ranking (M4). Evaluated with nDCG@5, ablations, and paired statistical testing.
                  </p>
                </div>
                <div className="space-y-3 sm:col-span-2 lg:col-span-1">
                  <p className="font-semibold text-sand-900">Languages & Features</p>
                  <p className="leading-relaxed">
                    Multi-language support: English, Arabic (العربية), and Urdu (اردو). Explainable ranking, grounded citations, local-first privacy, and fully offline-capable.
                  </p>
                </div>
              </div>
              <p className="mt-10 border-t border-sand-200/60 pt-6 text-xs text-sand-600">
                Context annotations are draft and have not yet been reviewed by a qualified scholar, so treat every suggestion as a starting point for your own reading rather than an answer.
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}

