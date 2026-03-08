/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                bgMain: '#F8F9FA',
                bgPanel: '#FFFFFF',
                textMain: '#1A1A1A',
                textMuted: '#6B7280',
                borderSubtle: '#E5E7EB',
                accentPrimary: '#2563EB',
            }
        },
    },
    plugins: [],
}
