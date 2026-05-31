/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Bricolage Grotesque"', 'system-ui', 'sans-serif'],
        body: ['"Space Mono"', 'monospace'],
      },
      colors: {
        ink: '#1a1410',
        cream: '#f4ead5',
        punch: '#ff3d5a',
        zest: '#ffc93c',
        mint: '#2ec4b6',
      },
    },
  },
  plugins: [],
}
