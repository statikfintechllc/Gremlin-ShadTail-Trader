/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{astro,js,ts,jsx,tsx}",
    "./node_modules/shadcn-ui/dist/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      height: {
        'screen-safe': 'calc(100vh - 2rem)',
        'viewport': '100vh',
        'full-scrollable': '100%',
      },
      maxHeight: {
        'screen-safe': 'calc(100vh - 2rem)',
        'viewport': '100vh',
        'full': '100%',
      },
      minHeight: {
        'screen': '100vh',
        'full': '100%',
      },
      colors: {
        // Professional Trading Theme: Black/Gray/Red-Gold-Bronze
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))", // Pure black
        foreground: "hsl(var(--foreground))", // Red-gold text
        primary: {
          DEFAULT: "hsl(var(--primary))", // Red-gold primary
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))", // Dark gray
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))", // Medium gray
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))", // Bronze accent
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))", // Dark gray cards
          foreground: "hsl(var(--card-foreground))",
        },
        // Custom trading theme colors
        trading: {
          black: "#000000",
          gray: {
            100: "#1a1a1a",
            200: "#2a2a2a", 
            300: "#3a3a3a",
            400: "#4a4a4a",
            500: "#5a5a5a",
          },
          red: "#ff3b30",
          gold: "#ff6b35",
          bronze: "#c9a96e",
          green: "#30d158",
          blue: "#007aff",
        }
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

