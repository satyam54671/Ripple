import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#050A14",
          900: "#0A1222",
          800: "#101B33",
          700: "#192847",
        },
      },
    },
  },
  plugins: [],
};

export default config;
