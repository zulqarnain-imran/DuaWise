import { SearchExperience } from "../components/SearchExperience";

export default function Home() {
  return (
    <main id="main" className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-8">
        <p className="text-sm font-medium uppercase tracking-wide text-emerald-700">
          Research project
        </p>
        <h1 className="mt-2 text-3xl font-bold text-sand-900 sm:text-4xl">DuaWise</h1>
        <p className="mt-3 text-lg text-sand-700">
          Describe what you are going through and find a Dua from a cited source, with
          its reference and the reason it was suggested.
        </p>
      </header>

      <SearchExperience />
    </main>
  );
}

