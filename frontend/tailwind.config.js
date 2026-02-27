/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                dark: {
                    900: '#111827',
                    800: '#1f2937',
                    700: '#374151'
                },
                brand: {
                    green: '#10b981',
                    red: '#ef4444',
                    blue: '#3b82f6',
                }
            }
        },
    },
    plugins: [],
}
