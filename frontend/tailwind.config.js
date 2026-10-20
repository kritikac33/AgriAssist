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
          50: '#f3f6ed',
          100: '#e6efdc',
          200: '#d1e3c1',
          300: '#b4d6a8',
          400: '#76b876',
          500: '#2b8b52',
          600: '#24764a',
          700: '#1c5d3b',
          800: '#123d2b',
          900: '#0b251b',
        },
        cream: {
          50: '#fffdf7',
          100: '#f5f2e9',
          200: '#e9e5d8',
          300: '#d8ceb9',
          400: '#c3ad8d',
          500: '#a98a67',
          600: '#8e6d50',
          700: '#79533b',
          800: '#65432f',
          900: '#483121',
        },
        forest: '#123d2b',
        leaf: '#24764a',
        sage: '#dce9cf',
        paper: '#fffdf7',
        soil: '#79533b',
      },
    },
  },
  plugins: [],
}
