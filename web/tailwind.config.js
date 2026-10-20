/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        bg: "rgb(var(--color-bg) / <alpha-value>)",
        surf: "rgb(var(--color-surf) / <alpha-value>)",
        elev: "rgb(var(--color-elev) / <alpha-value>)",
        line: "rgb(var(--color-line) / <alpha-value>)",
        tx: "rgb(var(--color-tx) / <alpha-value>)",
        mut: "rgb(var(--color-mut) / <alpha-value>)",
        brasa: "rgb(var(--color-brasa) / <alpha-value>)",
        info: "rgb(var(--color-info) / <alpha-value>)",
        ok: "rgb(var(--color-ok) / <alpha-value>)",
        warn: "rgb(var(--color-warn) / <alpha-value>)",
        err: "rgb(var(--color-err) / <alpha-value>)",
      },
      borderRadius: {
        card: "12px",
        btn: "8px",
      },
    },
  },
  plugins: [],
};
