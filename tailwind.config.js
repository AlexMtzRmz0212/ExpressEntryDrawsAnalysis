/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#070B14",
          900: "#0C111D",
          800: "#141B2D",
          700: "#1A2236",
          600: "#243050",
        },
        accent: {
          red:       "#C0392B",
          "red-lt":  "#E74C3C",
          gold:      "#D4A843",
          "gold-lt": "#F0C96A",
        },
      },
      fontFamily: {
        display: ['"Playfair Display"', "Georgia", "serif"],
        mono:    ['"IBM Plex Mono"', '"Courier New"', "monospace"],
        body:    ['"DM Sans"', "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease forwards",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
