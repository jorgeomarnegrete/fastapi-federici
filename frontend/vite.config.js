import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // CLAVE: Forzar a Vite a escuchar en todas las interfaces de red (0.0.0.0)
    // Esto es esencial para que sea accesible desde el host de Docker.
    host: '0.0.0.0',
    port: 5173,
    // Permite que el servidor escuche cambios de archivos fuera del contenedor
    watch: {
        usePolling: true,
    }
  },
});
