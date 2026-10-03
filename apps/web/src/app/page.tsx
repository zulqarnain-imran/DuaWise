import { SearchExperience } from "../components/SearchExperience";

export default function Home() {
  return (
    <main id="main" className="relative mx-auto max-w-6xl px-4 py-10 sm:py-14 lg:py-16">
      <div className="mesh-bg pointer-events-none absolute inset-x-0 top-0 -z-10 h-[28rem] w-full" />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 mx-auto h-96 w-full max-w-6xl rounded-full bg-gradient-to-b from-emerald-100/60 via-emerald-50/40 to-transparent blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-24 -z-10 h-72 w-72 -translate-x-1/2 rounded-full bg-gradient-to-br from-teal-100/50 to-transparent blur-3xl"
      />

      <header className="mb-12">
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200/70 bg-white/80 px-5 py-1.5 text-xs font-semibold uppercase tracking-[0.3em] text-emerald-800 shadow-sm shadow-emerald-900/5 ring-1 ring-emerald-100/80 backdrop-blur-xl sm:text-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            DuaWise • Context-Aware Intelligence
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          </div>
          <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl">
            <span className="gradient-text">Find the Right Dua</span>
            <span className="mt-2 block text-sand-900">For Your Situation</span>
          </h1>
          <p className="max-w-3xl text-lg leading-relaxed text-sand-700 sm:text-xl">
            Describe what you're going through in natural language. DuaWise maps your situation to a relevant Dua from cited sources, shows Arabic, translation, and reference with full explainability.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <span className="chip chip-active">TF-IDF + Cosine</span>
            <span className="chip">SBERT Embeddings</span>
            <span className="chip">Hybrid Fusion</span>
            <span className="chip">Context-Aware M4</span>
            <span className="chip">Explainable Ranking</span>
          </div>
        </div>
      </header>

      <SearchExperience />
    </main>
  );
}

