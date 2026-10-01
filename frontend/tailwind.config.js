/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0a0a0c",
        surface: {
          DEFAULT: "#121316",
          elevated: "#18191e",
          hover: "#202228",
        },
        border: {
          DEFAULT: "#26282e",
          subtle: "#1c1d22",
          active: "#3e424d",
        },
        primary: {
          DEFAULT: "#00d2ff",
          hover: "#38bdf8",
          blue: "#3b82f6",
        },
        accent: {
          violet: "#a855f7",
          green: "#10b981",
          amber: "#f59e0b",
          red: "#ef4444",
        },
        text: {
          primary: "#f4f4f6",
          secondary: "#8c8f9a",
          muted: "#5a5d68",
        }
      },
      fontFamily: {
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "Cascadia Code",
          "Consolas",
          "monospace"
        ],
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif"
        ]
      }
    },
  },
  plugins: [],
}
