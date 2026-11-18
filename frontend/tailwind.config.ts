import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        clinic: {
          canvas: "#FFFFFF",
          surface: "#FFF8F8",
          border: "#FCE8E8",
          "accent-subtle": "#FFF0F0",
          "accent-muted": "#FFE4E6",
          primary: "#E11D48",
          "primary-hover": "#BE123C",
          "text-primary": "#1E1B1E",
          "text-secondary": "#645D62",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      boxShadow: {
        clinical: "0 1px 3px rgba(225, 29, 72, 0.04), 0 1px 2px rgba(30, 27, 30, 0.02)",
        "clinical-md": "0 4px 6px -1px rgba(225, 29, 72, 0.05), 0 2px 4px -1px rgba(30, 27, 30, 0.03)",
      },
    },
  },
  plugins: [],
};

export default config;
