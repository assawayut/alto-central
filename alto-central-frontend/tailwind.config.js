/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'hsl(213, 89%, 47%)',
          dark: 'hsl(211, 93%, 34%)',
          foreground: 'hsl(0, 0%, 100%)',
        },
        success: {
          DEFAULT: 'hsl(178, 80%, 40%)',
          foreground: 'hsl(0, 0%, 100%)',
        },
        warning: {
          DEFAULT: 'hsl(42, 99%, 66%)',
          foreground: 'hsl(0, 0%, 0%)',
        },
        danger: {
          DEFAULT: 'hsl(4, 85%, 57%)',
          foreground: 'hsl(0, 0%, 100%)',
        },
        background: 'hsl(230, 100%, 99%)',
        foreground: 'hsl(220, 6%, 37%)',
        card: {
          DEFAULT: 'hsl(0, 0%, 100%)',
          foreground: 'hsl(220, 6%, 37%)',
        },
        muted: {
          DEFAULT: 'hsl(213, 13%, 53%)',
          foreground: 'hsl(213, 13%, 53%)',
        },
        border: 'hsl(228, 71%, 95%)',
      },
      borderRadius: {
        lg: '12px',
        md: '10px',
        sm: '8px',
      },
      boxShadow: {
        'card': '1px 3px 20px rgba(154, 170, 207, 0.10)',
      },
    },
  },
  plugins: [],
}
