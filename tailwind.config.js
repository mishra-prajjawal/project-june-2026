/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/templates/**/*.html",
    "./src/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          green: {
            light: '#EAF6EC',
            DEFAULT: '#10B981', // Emerald green
            dark: '#047857',
            accent: '#059669',
          },
          orange: {
            light: '#FEF3C7',
            DEFAULT: '#F59E0B', // Amber orange
            dark: '#D97706',
            accent: '#B45309',
          },
          white: '#FFFFFF',
          slate: '#F8FAFC',
          dark: '#0F172A',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Roboto', 'Open Sans', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
