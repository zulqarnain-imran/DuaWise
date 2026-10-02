import type { Metadata, Viewport } from "next";
import { ServiceWorkerRegistration } from "../components/ServiceWorkerRegistration";
import "./globals.css";

export const metadata: Metadata = {
  title: "DuaWise â€” find a Dua for your situation",
  description:
    "A research project that surfaces Duas from cited sources based on the situation you describe. Every result shows its source and reference.",
  applicationName: "DuaWise",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "DuaWise", statusBarStyle: "default" },
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
        {children}
        <ServiceWorkerRegistration />
        <footer className="mt-16 border-t border-sand-200 bg-white">
          <div className="mx-auto max-w-3xl px-4 py-8 text-sm text-sand-700">
            <p className="font-medium text-sand-900">About this project</p>
            <p className="mt-2">{DISCLAIMER}</p>
            <p className="mt-3">
              DuaWise is a final-year research project. Its context annotations are
              drafts and have not yet been reviewed by a qualified scholar, so treat
              every suggestion as a starting point for your own reading rather than an
              answer.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

