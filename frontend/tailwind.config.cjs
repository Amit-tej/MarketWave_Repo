module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#2563eb', // blue
        accent: '#10b981', // green
        highlight: '#f59e0b', // amber
        slatebg: '#0f172a'
      },
      fontFamily: {
        inter: ['Inter', 'ui-sans-serif', 'system-ui']
      }
    }
  },
  plugins: []
}
