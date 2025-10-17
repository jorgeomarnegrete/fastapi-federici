import React, { useState, createContext, useContext, useCallback, useEffect } from 'react';

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
    const [authToken, setAuthToken] = useState(null);
    const [user, setUser] = useState(null);

    const login = (token, userData) => {
        setAuthToken(token);
        setUser(userData);
        console.log('Usuario logueado:', userData.nombre, 'Es Admin:', userData.is_admin);
    };

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
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error('Fallo al cargar el perfil de usuario (ruta /users/me).');
        }

        const userData = await response.json();
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
            const userData = await fetchUserDetails(token);
            
            login(token, userData);

            setIsError(false);
            setMessage(`¡Bienvenido, ${userData.nombre}! Redireccionando...`);
            
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
// COMPONENTE: MainContent (Contenido Inicial/Login)
// ====================================================================
const MainContent = ({ openLoginModal, navigateToProduction }) => {
    const { isAuthenticated, user, authToken, logout } = useAuth(); 
    
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
                    text: '¡Acceso Denegado! El token es inválido o expiró. Cierre sesión y vuelva a iniciar.', 
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
        // Vista de Usuario Autenticado (Muestra el botón para ir a la gestión de producción)
        const isAdmin = user.is_admin;
        return (
            <div className="text-center p-8 bg-white rounded-xl shadow-2xl max-w-xl w-full">
                <h1 className="text-4xl font-extrabold text-green-600">
                    Panel de Control
                </h1>
                
                <p className="text-xl text-gray-600 mt-4 mb-2">
                    Bienvenido, <span className="font-semibold text-indigo-700">{user.nombre}</span>.
                </p>
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

                {/* Zona de Botones */}
                <div className="space-y-4 pt-4 border-t border-gray-100">
                    
                    {/* Botón para navegar a la nueva pantalla */}
                    <button
                        onClick={navigateToProduction}
                        className="w-full py-3 px-8 text-lg font-semibold text-white bg-indigo-600 rounded-lg shadow-md hover:bg-indigo-700 transition duration-300 transform hover:scale-[1.01]"
                    >
                        Acceder a Gestión de Producción
                    </button>
                    
                    {/* Botón de ejemplo para llamar a un endpoint protegido */}
                    <button
                        onClick={fetchProtectedData}
                        className="w-full py-3 px-8 text-lg font-semibold text-indigo-700 border-2 border-indigo-700 rounded-lg shadow-md hover:bg-indigo-50 transition duration-300 transform hover:scale-[1.01]"
                    >
                        Probar Conexión (Endpoint API)
                    </button>

                    {/* Botón de Cerrar Sesión */}
                    <button
                        onClick={logout}
                        className="w-full py-3 px-8 text-sm font-medium text-gray-500 hover:text-red-500 transition duration-300"
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
// COMPONENTE: UserManagement (CRUD de Usuarios)
// RUTA: Archivos -> Usuarios. REQUIERE: is_admin: true
// ====================================================================
const UserManagement = () => {
    const { authToken, user } = useAuth();
    const [users, setUsers] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingUser, setEditingUser] = useState(null);

    // Form state
    const initialUserState = {
        email: '',
        password: '',
        nombre: '',
        is_admin: false,
        is_active: true,
    };
    const [formData, setFormData] = useState(initialUserState);

    // --- Admin Check ---
    if (!user || !user.is_admin) {
        return (
            <div className="text-center p-10 bg-red-50 border border-red-300 rounded-xl shadow-lg">
                <h2 className="text-3xl font-bold text-red-700">❌ Acceso Denegado</h2>
                <p className="mt-4 text-gray-600">Solo los usuarios con rol de **Administrador** pueden gestionar otros usuarios. (is_admin: true)</p>
            </div>
        );
    }
    
    // --- API Functions ---
    // 1. Fetch Users
    const fetchUsers = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/users/`, {
                headers: { 'Authorization': `Bearer ${authToken}` },
            });

            if (response.status === 403) {
                // Aunque ya verificamos el admin, el backend puede denegar.
                throw new Error("No tienes permisos de API para ver esta lista.");
            }
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Fallo al cargar usuarios.');
            }

            const data = await response.json();
            // Filtra al usuario actual para evitar auto-eliminación/degradación.
            setUsers(data.filter(u => u.id !== user.id)); 
        } catch (err) {
            console.error("Fetch Users Error:", err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    }, [authToken, user.id]);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    // 2. Handle Form Submission (Create/Update)
    const handleFormSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        const isUpdating = !!editingUser;
        const method = isUpdating ? 'PUT' : 'POST';
        const url = isUpdating 
            ? `${API_BASE_URL}/users/${editingUser.id}` 
            : `${API_BASE_URL}/users/`;

        // Construir el payload con los campos opcionales
        const payload = {
            email: formData.email,
            nombre: formData.nombre,
            is_admin: formData.is_admin,
            is_active: formData.is_active
        };

        // Lógica de Contraseña CORREGIDA:
        if (formData.password) {
            // Si la contraseña se proporciona (Create o Update), la incluimos en el payload.
            payload.password = formData.password;
        } else if (!isUpdating) {
            // Si es un nuevo usuario (POST) y la contraseña está vacía, es un error.
            setError("La contraseña es obligatoria para un nuevo usuario.");
            setIsLoading(false);
            return;
        }
        // Si es una actualización (PUT) y la contraseña está vacía, simplemente no se incluye en el payload, 
        // y el backend NO debe cambiarla.

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}` 
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Fallo al ${isUpdating ? 'actualizar' : 'crear'} el usuario.`);
            }

            // Éxito: cerrar formulario, resetear estado y refrescar datos
            setIsFormOpen(false);
            setEditingUser(null);
            setFormData(initialUserState);
            await fetchUsers();

        } catch (err) {
            console.error("CRUD Error:", err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    // 3. Handle Delete
    const handleDelete = async (userId, userName) => {
        // Reemplazo de window.confirm() por un mensaje de alerta personalizado
        const confirmed = prompt(`ADVERTENCIA: Vas a eliminar a "${userName}".\n\nEscribe "CONFIRMAR" para proceder:`);
        
        if (confirmed !== "CONFIRMAR") {
            return;
        }

        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${authToken}` },
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Fallo al eliminar el usuario.');
            }

            // Éxito: refrescar datos
            await fetchUsers();
        } catch (err) {
            console.error("Delete Error:", err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    // --- UI Handlers ---
    const startCreate = () => {
        setEditingUser(null);
        setFormData(initialUserState);
        setIsFormOpen(true);
        setError(null);
    };

    const startEdit = (userToEdit) => {
        setEditingUser(userToEdit);
        setFormData({
            email: userToEdit.email,
            password: '', // NUNCA rellenar la contraseña por seguridad.
            nombre: userToEdit.nombre,
            is_admin: userToEdit.is_admin,
            is_active: userToEdit.is_active,
        });
        setIsFormOpen(true);
        setError(null);
    };

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value,
        }));
    };

    // --- Componentes Auxiliares Locales (para mantener todo en un archivo) ---
    const InputField = ({ label, name, type = 'text', value, onChange, required, disabled, placeholder }) => (
        <div>
            <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
                {label} {required && <span className="text-red-500">*</span>}
            </label>
            <input
                type={type}
                id={name}
                name={name}
                value={value}
                onChange={onChange}
                required={required}
                disabled={disabled || isLoading}
                placeholder={placeholder}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
            />
        </div>
    );
    
    const CheckboxField = ({ label, name, checked, onChange }) => (
        <div className="flex items-center">
            <input
                type="checkbox"
                id={name}
                name={name}
                checked={checked}
                onChange={onChange}
                disabled={isLoading}
                className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            />
            <label htmlFor={name} className="ml-2 block text-sm font-medium text-gray-700">
                {label}
            </label>
        </div>
    );

    const UserForm = () => (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => { 
            // Cierra el modal solo si no está cargando
            if (!isLoading) { setIsFormOpen(false); setEditingUser(null); setError(null); }
        }}>
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-6 animate-scaleIn" onClick={e => e.stopPropagation()}>
                <h3 className="text-2xl font-bold text-indigo-700 mb-4 border-b pb-2">
                    {editingUser ? 'Editar Usuario' : 'Crear Nuevo Usuario'}
                </h3>
                
                {error && <div className="p-3 mb-4 text-red-700 bg-red-100 rounded-lg text-sm">{error}</div>}

                <form onSubmit={handleFormSubmit} className="space-y-4">
                    
                    <InputField 
                        label="Nombre Completo" 
                        name="nombre" 
                        value={formData.nombre} 
                        onChange={handleInputChange} 
                        required 
                        placeholder="Ej: Juan Pérez"
                    />
                    <InputField 
                        label="Email (Usuario)" 
                        name="email" 
                        type="email" 
                        value={formData.email} 
                        onChange={handleInputChange} 
                        required 
                        placeholder="correo@empresa.com"
                    />
                    
                    {/* Campo de Contraseña con placeholder descriptivo */}
                    <InputField 
                        label="Contraseña" 
                        name="password" 
                        type="password" 
                        value={formData.password} 
                        onChange={handleInputChange} 
                        required={!editingUser} 
                        placeholder={editingUser ? 'Dejar vacío para NO cambiar la contraseña' : 'Contraseña obligatoria'}
                    />

                    <div className="flex space-x-6 pt-2">
                        <CheckboxField 
                            label="Es Administrador" 
                            name="is_admin" 
                            checked={formData.is_admin} 
                            onChange={handleInputChange} 
                        />
                        <CheckboxField 
                            label="Está Activo" 
                            name="is_active" 
                            checked={formData.is_active} 
                            onChange={handleInputChange} 
                        />
                    </div>
                    
                    <div className="flex justify-end space-x-3 pt-4">
                        <button
                            type="button"
                            onClick={() => { setIsFormOpen(false); setEditingUser(null); setError(null); }}
                            className="py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition duration-150"
                            disabled={isLoading}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            className="py-2 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition duration-150 disabled:opacity-50"
                            disabled={isLoading}
                        >
                            {isLoading ? 'Guardando...' : (editingUser ? 'Guardar Cambios' : 'Crear Usuario')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );


    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-semibold text-gray-700">Lista de Usuarios</h2>
                <button
                    onClick={startCreate}
                    className="flex items-center px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg shadow-md hover:bg-indigo-700 transition duration-150 disabled:opacity-50"
                    disabled={isLoading}
                >
                    <span className="text-xl mr-2">+</span>
                    Nuevo Usuario
                </button>
            </div>
            
            {error && (
                <div className="p-4 bg-red-100 text-red-700 rounded-lg border border-red-300">
                    Error: {error}
                </div>
            )}
            
            {isLoading && (
                <div className="text-center p-10 text-gray-500">Cargando usuarios...</div>
            )}

            {!isLoading && users.length === 0 && !error && (
                <div className="text-center p-10 text-gray-500 bg-white border border-dashed rounded-lg">
                    No hay otros usuarios registrados.
                </div>
            )}

            {!isLoading && users.length > 0 && (
                <div className="overflow-x-auto bg-white rounded-xl shadow-md">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Admin</th>
                                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Activo</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {users.map((u) => (
                                <tr key={u.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{u.nombre}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.email}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${u.is_admin ? 'bg-indigo-100 text-indigo-800' : 'bg-gray-100 text-gray-800'}`}>
                                            {u.is_admin ? 'Sí' : 'No'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                            {u.is_active ? 'Activo' : 'Inactivo'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                                        <button
                                            onClick={() => startEdit(u)}
                                            className="text-indigo-600 hover:text-indigo-900 transition duration-150"
                                            title="Editar"
                                            disabled={isLoading}
                                        >
                                            ✏️
                                        </button>
                                        <button
                                            onClick={() => handleDelete(u.id, u.nombre)}
                                            className="text-red-600 hover:text-red-900 transition duration-150"
                                            title="Eliminar"
                                            disabled={isLoading}
                                        >
                                            🗑️
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {isFormOpen && <UserForm />}
        </div>
    );
};


// ====================================================================
// COMPONENTE: ProductionManagement (Dashboard con menú y manejo de vistas)
// ====================================================================
const NavItem = ({ label, icon, onClick, isSubItem = false, isActive = false }) => (
    <div
        onClick={onClick}
        className={`flex items-center p-3 rounded-lg cursor-pointer transition duration-200 
            ${isSubItem ? 'ml-6 text-sm hover:bg-gray-700' : 'font-medium text-base hover:bg-indigo-700'}
            ${isActive ? 'bg-indigo-700 text-white shadow-inner' : 'text-gray-300'}
        `}
    >
        <span className="w-5 h-5 mr-3 text-center">{icon}</span>
        {label}
    </div>
);

const ProductionManagement = ({ navigateToHome }) => {
    const { logout, user } = useAuth();
    // Usamos el nombre de la vista (o subvista) actual como estado
    const [activeView, setActiveView] = useState('Dashboard');
    
    const handleLogout = () => {
        logout();
        navigateToHome(); 
    };

    const handleItemClick = (label, subItem = null) => {
        // Lógica para manejar la apertura/cierre de sub-menús
        const parent = menuData.find(item => item.label === label);
        if (parent && parent.subItems && !subItem) {
             // Si el padre está activo, al hacer click de nuevo lo llevamos a la primera sub-vista
             if (activeView === parent.label || isParentActive(parent.label)) {
                 setActiveView(parent.subItems[0].view);
             } else {
                 // Si no está activo, lo abrimos
                 setActiveView(parent.label);
             }
        } else {
            setActiveView(subItem || label);
        }
    };
    
    // Contenido dinámico principal (usando switch para claridad)
    const renderContent = () => {
        switch (activeView) {
            case 'Usuarios':
                return <UserManagement />; // Componente CRUD de Usuarios
            case 'Dashboard':
                return (
                    <div className="text-center p-10">
                        <h2 className="text-2xl font-semibold text-gray-700">Resumen del Sistema</h2>
                        <p className="mt-4 text-gray-500">
                            Aquí se mostrarán los indicadores clave de rendimiento (KPIs) y gráficos de producción y órdenes.
                        </p>
                    </div>
                );
            case 'Clientes':
            case 'Proveedores':
            case 'Productos':
            case 'Puestos de trabajos':
            case 'Rutas':
            case 'General':
            case 'Cambio de estados':
            case 'Gestión de OC':
            case 'Expedición':
            case 'Reportes':
            case 'Configuración':
            default:
                return (
                    <div className="text-center p-10">
                        <h2 className="text-2xl font-semibold text-gray-700">Módulo en Desarrollo</h2>
                        <p className="mt-4 text-gray-500">
                            El módulo **{activeView}** está en construcción.
                        </p>
                    </div>
                );
        }
    };


    const menuData = [
        { label: 'Dashboard', icon: '🏠', view: 'Dashboard' },
        { 
            label: 'Archivos', icon: '🗄️', view: 'Archivos', 
            subItems: [
                { label: 'Clientes', view: 'Clientes' },
                { label: 'Proveedores', view: 'Proveedores' },
                { label: 'Productos', view: 'Productos' },
                { label: 'Puestos de trabajos', view: 'Puestos de trabajos' },
                { label: 'Rutas', view: 'Rutas' },
                { label: 'Usuarios', view: 'Usuarios' }, // Punto de entrada para el CRUD
            ] 
        },
        { 
            label: 'Gestión de OP', icon: '📝', view: 'Gestión de OP', 
            subItems: [
                { label: 'General', view: 'General' },
                { label: 'Cambio de estados', view: 'Cambio de estados' },
            ] 
        },
        { label: 'Gestión de OC', icon: '🧾', view: 'Gestión de OC' }, 
        { label: 'Expedición', icon: '📦', view: 'Expedición' },
        { label: 'Reportes', icon: '📊', view: 'Reportes' },
        { label: 'Configuración', icon: '🛠️', view: 'Configuración' },
    ];


    // Función auxiliar para determinar si un sub-menú está abierto para despliegue
    const isParentActive = (parentLabel) => {
        const parent = menuData.find(item => item.label === parentLabel);
        return parent && parent.subItems && parent.subItems.some(sub => sub.view === activeView);
    };

    return (
        // Contenedor principal del dashboard: ocupa toda la ventana y usa flex para el layout side-by-side
        <div className="flex w-full min-h-screen bg-gray-100">
            {/* Sidebar (Menú de Navegación) */}
            <aside className="w-64 bg-gray-800 text-white flex flex-col shadow-2xl transition-all duration-300 flex-shrink-0">
                <div className="p-6 text-2xl font-extrabold text-indigo-400 border-b border-gray-700">
                    FastControl
                </div>

                <div className="flex-grow p-4 space-y-1 overflow-y-auto">
                    {menuData.map((item) => (
                        <React.Fragment key={item.view}>
                            {/* Item Principal */}
                            <NavItem
                                label={item.label}
                                icon={item.icon}
                                onClick={() => handleItemClick(item.label)}
                                // El item principal está activo si su label coincide O si alguno de sus sub-items está activo
                                isActive={activeView === item.label || (item.subItems && isParentActive(item.label))}
                            />
                            
                            {/* Sub-Items (solo se muestran si el item principal o un sub-item está activo) */}
                            {item.subItems && (activeView === item.label || isParentActive(item.label)) && (
                                <div className="ml-2 border-l border-gray-600 pl-2 space-y-1">
                                    {item.subItems.map(sub => (
                                        <NavItem
                                            key={sub.view}
                                            label={sub.label}
                                            icon="•"
                                            onClick={() => handleItemClick(item.label, sub.view)}
                                            isSubItem={true}
                                            isActive={activeView === sub.view}
                                        />
                                    ))}
                                </div>
                            )}
                        </React.Fragment>
                    ))}
                </div>

                {/* Sección de Usuario y Cerrar Sesión */}
                <div className="p-4 border-t border-gray-700">
                    <div className="text-xs text-gray-400 mb-2 truncate">
                        Usuario: {user.nombre} ({user.is_admin ? 'Admin' : 'Estándar'})
                    </div>
                    <button
                        onClick={handleLogout}
                        className="flex items-center p-3 w-full rounded-lg text-sm text-red-400 bg-gray-700 hover:bg-red-800 transition duration-200"
                    >
                        <span className="w-5 h-5 mr-3">🚪</span>
                        Cerrar Sesión
                    </button>
                </div>
            </aside>

            {/* Contenido Principal del Panel */}
            <main className="flex-1 p-6 overflow-y-auto">
                <h1 className="text-3xl font-bold text-gray-800 mb-6 border-b pb-3">
                    {activeView}
                </h1>

                <div className="bg-white p-8 rounded-xl shadow-lg min-h-[calc(100vh-120px)]">
                    {renderContent()}
                </div>
            </main>
        </div>
    );
};

// ====================================================================
// COMPONENTE CONTENIDO PRINCIPAL: RootAppContent
// Contiene toda la lógica de estado y navegación.
// ====================================================================
const RootAppContent = () => {
    // Estado para controlar la visibilidad del modal de inicio de sesión
    const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
    
    // Estado para controlar qué vista se muestra: 'HOME' o 'PRODUCTION'
    const [currentView, setCurrentView] = useState('HOME');

    // Ahora SAFE: useAuth() se llama dentro del AuthProvider
    const { isAuthenticated } = useAuth();
    
    // REDIRECCIÓN DE SEGURIDAD: Si no está autenticado, siempre debe estar en HOME.
    if (!isAuthenticated && currentView !== 'HOME') {
        setCurrentView('HOME'); 
    }

    const openModal = () => setIsLoginModalOpen(true);
    const closeModal = () => setIsLoginModalOpen(false);
    
    // Funciones de navegación
    const navigateToProduction = () => setCurrentView('PRODUCTION');
    const navigateToHome = () => setCurrentView('HOME');


    // Renderizado condicional basado en la vista actual
    let renderedComponent;
    
    switch (currentView) {
        case 'PRODUCTION':
            renderedComponent = <ProductionManagement navigateToHome={navigateToHome} />;
            break;
        case 'HOME':
        default:
            renderedComponent = <MainContent openLoginModal={openModal} navigateToProduction={navigateToProduction} />;
            break;
    }


    return (
        <div className={`w-full min-h-screen font-sans bg-gray-100 ${currentView === 'HOME' ? 'flex flex-col items-center justify-center p-4' : ''}`}>
            
            {renderedComponent}

            <LoginModal 
                isOpen={isLoginModalOpen} 
                onClose={closeModal} 
            />
        </div>
    );
}

// ====================================================================
// COMPONENTE PRINCIPAL: APP
// Única responsabilidad: Envolver la aplicación en el proveedor de contexto.
// ====================================================================
const App = () => {
    return (
        <AuthProvider>
            <RootAppContent />
        </AuthProvider>
    );
};

export default App;
