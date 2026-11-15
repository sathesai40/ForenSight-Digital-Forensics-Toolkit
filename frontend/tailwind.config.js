/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // High-assurance forensic dark palette
        forensic: {
          bg: "#090d16",       // Deep void navy/charcoal
          card: "#0f1624",     // Subtle elevated card
          cardHover: "#152033",
          border: "#1e293b",   // Slate border
          borderLight: "#334155",
          accent: "#0284c7",   // Sky/Cyan forensic indicator
          accentMuted: "rgba(2, 132, 199, 0.15)",
          textPrimary: "#f1f5f9",
          textSecondary: "#94a3b8",
          textMuted: "#64748b",
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'Consolas', 'monospace'],
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
