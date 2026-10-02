import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

/**
 * eslint-config-next 16 ships native flat configs, so no FlatCompat bridge is
 * used. Passing the compat layer to these configs throws a circular-structure
 * error during config normalisation.
 */
const config = [
  ...nextCoreWebVitals,
  ...nextTypeScript,
  {
    ignores: [".next/**", "node_modules/**", "out/**", "next-env.d.ts"],
  },
  {
    rules: {
      // Arabic text and RTL content are first-class here, and this rule cannot
      // distinguish a genuine unescaped-entity bug from a bidi-context artefact.
      "react/no-unescaped-entities": "off",
      "@next/next/no-img-element": "error",
    },
  },
];

export default config;
