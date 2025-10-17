import React, { useState, createContext, useContext } from 'react';

// URL base de la API de FastAPI.
const API_BASE_URL = 'http://localhost:8000';

// ====================================================================
// 1. CONTEXTO DE AUTENTICACIÓN
// ====================================================================
const AuthContext = createContext(null);

// Hook personalizado para usar el contexto de autenticación
const useAuth = () => useContext(AuthContext);

// ====================================================================
// 2. PROVEEDOR DE AUTENTICACIÓN (AuthProvider)
// ====================================================================
const AuthProvider = ({ children }) => {
    // Estado para el token JWT (null si no está autenticado)
    const [authToken, setAuthToken] = useState(null);
    // Estado para el objeto de usuario (incluye 'name' e 'is_admin')
    const [user, setUser] = useState(null);

    // Función de LOGIN: Guarda token y el objeto completo del usuario
    const login = (token, userData) => {
        setAuthToken(token);
        setUser(userData);
        // CAMBIO 1: Usar userData.nombre en el log de la consola
        console.log('Usuario logueado:', userData.nombre, 'Es Admin:', userData.is_admin);
    };

    // Función de LOGOUT: Limpia token y usuario
    const logout = () => {
        setAuthToken(null);
        setUser(null);
        console.log('Sesión cerrada.');
    };

    const isAuthenticated = !!authToken;

    const contextValue = {
        isAuthenticated,
        user,
        authToken,
        login,
        logout,
    };

    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
};

// ====================================================================
// COMPONENTE: LoginModal
// ====================================================================
const LoginModal = ({ isOpen, onClose }) => {
    const { login } = useAuth();

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [isError, setIsError] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    if (!isOpen) return null;

    // Función para obtener los detalles del usuario usando el token
    const fetchUserDetails = async (token) => {
        const response = await fetch(`${API_BASE_URL}/users/me`, {
            method: 'GET',
            headers: {
                // CLAVE: Enviar el token en el header Authorization
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error('Fallo al cargar el perfil de usuario (ruta /users/me).');
        }

        const userData = await response.json();
        // Asumiendo que la respuesta incluye { username, nombre, is_admin }
        if (typeof userData.is_admin === 'undefined') {
             console.warn("ADVERTENCIA: El perfil del usuario no contiene el campo 'is_admin'. Asumiendo 'false'.");
             userData.is_admin = false;
        }
        return userData; 
    };

    // Función que se ejecuta al enviar el formulario
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        setMessage('');
        setIsError(false);
        setIsLoading(true);

        const loginData = { username, password };

        try {
            // 1. Llamada de Login y obtención del Token
            const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(loginData),
            });

            const loginDataResult = await loginResponse.json();
            
            if (!loginResponse.ok) {
                setIsError(true);
                setMessage(loginDataResult.detail || 'Error de inicio de sesión. Credenciales inválidas.');
                return;
            } 

            const token = loginDataResult.access_token;
            
            // 2. Llamada para obtener los detalles del usuario con el token
            const userData = await fetchUserDetails(token);
            
            // 3. Login Exitoso: Guardar token y datos completos del usuario en el Contexto
            login(token, userData);

            setIsError(false);
            // CAMBIO 2: Usar userData.nombre en el mensaje de éxito
            setMessage(`¡Bienvenido, ${userData.nombre}! Redireccionando...`);
            
            // Cerrar modal después de un breve retraso
            setTimeout(() => {
                setUsername('');
                setPassword('');
                setMessage(''); 
                onClose(); 
            }, 1000);
            
        } catch (error) {
            console.error('Error durante el proceso de autenticación:', error);
            setIsError(true);
            setMessage(`Error: ${error.message}.`);
        } finally {
            setIsLoading(false);
        }
    };


    return (
        // Fondo oscuro semitransparente (Backdrop)
        <div className="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center z-50 p-4" onClick={onClose}>
            
            {/* Contenedor del Modal */}
            <div 
                className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 transform transition-all duration-300 scale-100"
                onClick={(e) => e.stopPropagation()} 
            >
                <div className="flex justify-between items-center mb-6 border-b pb-3">
                    <h2 className="text-3xl font-bold text-indigo-700">Iniciar Sesión</h2>
                    <button 
                        onClick={onClose}
                        className="text-gray-500 hover:text-gray-900 text-2xl font-semibold transition duration-150"
                        aria-label="Cerrar modal"
                        disabled={isLoading}
                    >
                        &times;
                    </button>
                </div>

                <form className="space-y-4" onSubmit={handleSubmit}>
                    
                    <div>
                        <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                            Usuario (Email)
                        </label>
                        <input
                            type="email"
                            id="username"
                            required
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 transition duration-150"
                            placeholder="tu.correo@ejemplo.com"
                            disabled={isLoading}
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                            Contraseña
                        </label>
                        <input
                            type="password"
                            id="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 transition duration-150"
                            placeholder="Ingresa tu contraseña"
                            disabled={isLoading}
                        />
                    </div>
                    
                    {/* Mensaje de Feedback */}
                    {message && (
                        <div className={`p-3 rounded-lg text-sm font-medium ${isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                            {message}
                        </div>
                    )}

                    {/* Botón de Login */}
                    <div className="pt-2">
                        <button
                            type="submit"
                            className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-md text-base font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-300 transform hover:scale-[1.01] disabled:opacity-50"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Accediendo...
                                </>
                            ) : (
                                'Acceder'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// ====================================================================
// COMPONENTE: MainContent (Contenido Principal)
// ====================================================================
const MainContent = ({ openLoginModal }) => {
    const { isAuthenticated, user, authToken, logout } = useAuth(); 
    
    // Estado para mostrar el resultado de la llamada protegida
    const [protectedMessage, setProtectedMessage] = useState(null);

    // Función para llamar a una ruta API protegida (e.g., /api/items)
    const fetchProtectedData = async () => {
        setProtectedMessage('Cargando...');
        try {
            const response = await fetch(`${API_BASE_URL}/api/items`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });

            if (response.status === 401) {
                setProtectedMessage({ 
                    text: '¡Acceso Denegado! El token es inválido o expiró.', 
                    isError: true 
                });
                return;
            }

            if (!response.ok) {
                const data = await response.json();
                setProtectedMessage({ 
                    text: `Error ${response.status}: ${data.detail || 'Fallo en la petición protegida'}`, 
                    isError: true 
                });
                return;
            }

            const data = await response.json();
            setProtectedMessage({ 
                text: `¡Datos protegidos recibidos con éxito! Primer ítem: ${data[0]?.name || 'sin nombre'}`, 
                isError: false 
            });

        } catch (error) {
            console.error("Error fetching protected data:", error);
            setProtectedMessage({ 
                text: 'Error de conexión con la API para datos protegidos.', 
                isError: true 
            });
        }
    };


    if (isAuthenticated && user) {
        // Vista de Usuario Autenticado
        const isAdmin = user.is_admin;
        return (
            <div className="text-center p-8 bg-white rounded-xl shadow-2xl max-w-xl w-full">
                <h1 className="text-4xl font-extrabold text-green-600">
                    Panel de Control
                </h1>
                
                {/* Mensaje de Bienvenida con el rol */}
                <p className="text-xl text-gray-600 mt-4 mb-2">
                    Bienvenido, <span className="font-semibold text-indigo-700">{user.nombre}</span>.
                </p>
                {/* Mantenemos la etiqueta de Admin visible para verificación de rol */}
                {isAdmin && (
                     <p className="text-sm font-bold text-yellow-600 mb-8 bg-yellow-100 inline-block px-3 py-1 rounded-full">
                         ROL: ADMINISTRADOR
                     </p>
                )}
                {!isAdmin && (
                     <p className="text-sm font-bold text-gray-600 mb-8 bg-gray-100 inline-block px-3 py-1 rounded-full">
                         ROL: USUARIO ESTÁNDAR
                     </p>
                )}

                {/* Zona de Botones - Solo los dos solicitados */}
                <div className="space-y-4 pt-4 border-t border-gray-100">
                    
                    {/* Botón 1: Acceder a Gestión de Producción (llama a la API protegida) */}
                    <button
                        onClick={fetchProtectedData}
                        className="w-full py-3 px-8 text-lg font-semibold text-white bg-indigo-600 rounded-lg shadow-md hover:bg-indigo-700 transition duration-300 transform hover:scale-[1.01]"
                    >
                        Acceder a Gestión de Producción
                    </button>
                    
                    {/* Botón 2: Cerrar Sesión */}
                    <button
                        onClick={logout}
                        className="w-full py-3 px-8 text-lg font-semibold text-indigo-700 border-2 border-indigo-700 rounded-lg shadow-md hover:bg-indigo-50 transition duration-300 transform hover:scale-[1.01]"
                    >
                        Cerrar Sesión
                    </button>
                </div>

                {/* Resultado de la Petición Protegida */}
                {protectedMessage && (
                    <div className={`mt-6 p-4 rounded-xl text-sm font-medium ${protectedMessage.isError ? 'bg-red-100 text-red-700 border border-red-300' : 'bg-green-100 text-green-700 border border-green-300'}`}>
                        {protectedMessage.text}
                    </div>
                )}
            </div>
        );
    }

    // Vista de Usuario NO Autenticado
    return (
        <div className="text-center p-10 bg-white rounded-xl shadow-2xl max-w-xl w-full">
            <h1 className="text-5xl md:text-6xl font-extrabold text-indigo-700 animate-fadeIn">
                FastControl
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 mt-4 mb-8">
                Sistema de gestión de producción
            </p>

            <button
                onClick={openLoginModal}
                className="py-3 px-8 text-lg font-semibold text-white bg-green-500 rounded-full shadow-lg hover:bg-green-600 transition duration-300 transform hover:scale-105 active:scale-95"
            >
                Iniciar Sesión
            </button>
        </div>
    );
};


// ====================================================================
// COMPONENTE PRINCIPAL: APP
// ====================================================================
const App = () => {
    // Estado para controlar la visibilidad del modal de inicio de sesión
    const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

    // Funciones para abrir y cerrar el modal
    const openModal = () => setIsLoginModalOpen(true);
    const closeModal = () => setIsLoginModalOpen(false);

    return (
        // Envolver toda la aplicación dentro del AuthProvider
        <AuthProvider>
            <div className="min-h-screen w-full flex flex-col items-center justify-center bg-gray-100 font-sans p-4">
                
                {/* Contenido Principal */}
                <MainContent openLoginModal={openModal} />

                {/* Renderizado Condicional del Modal */}
                <LoginModal 
                    isOpen={isLoginModalOpen} 
                    onClose={closeModal} 
                />
            </div>
        </AuthProvider>
    );
};

export default App;
