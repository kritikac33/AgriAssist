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
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        cream: {
          50: '#fdfbf7',
          100: '#faf5ef',
          200: '#f5ebdf',
          300: '#efdccf',
          400: '#e6c9b3',
          500: '#dbb094',
          600: '#c99772',
          700: '#b07d59',
          800: '#96644a',
          900: '#7d523e',
        },
      },
    },
  },
  plugins: [],
}
