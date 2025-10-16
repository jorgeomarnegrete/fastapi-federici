import React, { useState } from 'react';

// ====================================================================
// COMPONENTE PRINCIPAL: APP (Muestra "HOLA" de forma Garantizada)
// Usado para confirmar la funcionalidad básica de React y el compilador.
// ====================================================================
const App = () => {
    return (
        // Contenedor para ocupar toda la pantalla, con un fondo visible.
        <div className="min-h-screen w-full flex items-center justify-center bg-blue-500 font-sans p-8">
            <div className="text-center p-10 bg-white rounded-xl shadow-2xl">
                {/* Mensaje grande y llamativo */}
                <h1 className="text-8xl font-black text-blue-700 animate-bounce">
                    FastControl 1.0
                </h1>
                <p className="text-2xl text-gray-600 mt-4">
                    Sistema de gestión de producción
                </p>
            </div>
        </div>
    );
};

export default App;
