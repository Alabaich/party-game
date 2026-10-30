/** @type {import('tailwindcss').Config} */
const v = (name) => `rgb(var(--c-${name}) / <alpha-value>)`

export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Bricolage Grotesque"', 'system-ui', 'sans-serif'],
        body: ['"Space Mono"', 'monospace'],
      },
      // colours come from the active theme (see index.css: [data-theme=...])
      colors: {
        ink: v('ink'),
        cream: v('cream'),
        punch: v('punch'),
        zest: v('zest'),
        mint: v('mint'),
      },
    },
  },
  plugins: [],
}
