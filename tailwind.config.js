/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy:   '#16223d',
        crimson: '#c8362b',
        'warm-bg':     '#f1efe9',
        'warm-border': '#e2ded3',
        'warm-mid':    '#e6e2d8',
        muted:  '#5b6172',
        slate:  '#42485a',
        'navy-light': '#9fb0d4',
        emerald: '#2f8f6b',
        cobalt:  '#3a6ea8',
        violet:  '#6d4c91',
      },
      fontFamily: {
        sans: ['"Libre Franklin"', 'system-ui', 'sans-serif'],
        mono: ['"Spline Sans Mono"', 'monospace'],
      },
      maxWidth: {
        site: '1180px',
      },
    },
  },
  plugins: [],
};
