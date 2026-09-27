/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#10202B",
          50: "#F2F5F6",
          100: "#DCE4E7",
          200: "#B7C7CE",
          300: "#8CA5B0",
          400: "#5C7B87",
          500: "#3A5964",
          600: "#25404B",
          700: "#1A2E38",
          800: "#10202B",
          900: "#0A161E",
        },
        paper: {
          DEFAULT: "#EAEDE7",
          50: "#FBFCFA",
          100: "#F4F5F1",
          200: "#EAEDE7",
          300: "#D8DDD3",
        },
        monsoon: {
          DEFAULT: "#1F6F63",
          50: "#EAF4F2",
          100: "#CFE6E1",
          400: "#2C8D7C",
          500: "#1F6F63",
          600: "#175650",
          700: "#113F3A",
        },
        risk: {
          low: "#4C9A6B",
          moderate: "#D9A441",
          high: "#D97D34",
          critical: "#C1443A",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      backgroundImage: {
        contour: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'%3E%3Cg fill='none' stroke='%23FFFFFF' stroke-opacity='0.06' stroke-width='1'%3E%3Cpath d='M0,120 Q100,80 200,120 T400,120'/%3E%3Cpath d='M0,170 Q100,130 200,170 T400,170'/%3E%3Cpath d='M0,220 Q100,180 200,220 T400,220'/%3E%3Cpath d='M0,270 Q100,230 200,270 T400,270'/%3E%3C/g%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
};
