// frontend/src/main.jsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx'; // Importamos nuestro componente principal
import './index.css'; // Importamos los estilos globales (incluido Tailwind)

// --- LÓGICA DE MONTAJE DE REACT ---

// 1. Obtenemos el punto de anclaje del DOM (el <div id="root"> en index.html)
const rootElement = document.getElementById('root');

if (rootElement) {
    // 2. Creamos y montamos la aplicación React
    ReactDOM.createRoot(rootElement).render(
        // React.StrictMode es útil para desarrollo
        <React.StrictMode>
            <App /> {/* Renderizamos el componente App */}
        </React.StrictMode>
    );
} else {
    // Esto es un fallback en caso de que el index.html esté mal.
    console.error("Error crítico: No se encontró el elemento con id='root'. La aplicación React no puede montarse.");
}

