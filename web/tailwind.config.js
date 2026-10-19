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
        bg: "#0B0B0E",
        surf: "#141418",
        elev: "#1C1C22",
        line: "#2A2A33",
        tx: "#EDEDEF",
        mut: "#A1A1AA",
        brasa: "#FF6A2B",
        info: "#38BDF8",
        ok: "#22C55E",
        warn: "#F59E0B",
        err: "#EF4444",
      },
      borderRadius: {
        card: "12px",
        btn: "8px",
      },
    },
  },
  plugins: [],
};
