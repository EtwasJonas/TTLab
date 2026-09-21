/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    // Tailwind v3 pipeline (matches tailwind.config.ts + the @tailwind
    // directives in app/globals.css). Do NOT use '@tailwindcss/postcss'
    // here - that is the Tailwind v4 plugin, which silently drops the
    // v3 theme (spacing/colors/radius utilities) when fed @tailwind
    // directives and leaves the whole UI without most of its styling.
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;
