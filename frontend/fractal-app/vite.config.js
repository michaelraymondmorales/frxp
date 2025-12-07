import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react'; // Import the React plugin
import tailwindcss from '@tailwindcss/vite'; // Import the Tailwind CSS Vite plugin

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(), // Add the React plugin
    tailwindcss(), // Add the Tailwind CSS plugin
  ],
});
