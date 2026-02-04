import { store, actions } from './store.js';

const API_URL = 'http://localhost:8000/api/v1';

async function request(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (store.token) headers['Authorization'] = `Bearer ${store.token}`;

    const config = { ...options, headers: { ...headers, ...options.headers } };
    const method = options.method || 'GET';

    console.log(`[${method}] ${endpoint}`);

    try {
        const res = await fetch(`${API_URL}${endpoint}`, config);
        
        if (res.ok) {
            console.log(`[${res.status}] ${endpoint}`);
        } else {
            console.warn(`[${res.status}] ${endpoint} - Procesando error...`);
        }

        if (res.status === 401) {
            console.error(" Sesión expirada. Cerrando sesión...");
            actions.logout();
            throw new Error('Sesión expirada. Inicia sesión de nuevo.');
        }


        if (!res.ok) {
            let errData;
            try {
                errData = await res.json();
            } catch (e) {
                console.error(" El servidor no devolvió JSON:", e);
                throw new Error(`Error del servidor (${res.status}): ${res.statusText}`);
            }

            let errorMessage = 'Error desconocido';
            
            // Extraer mensajes de FastAPI / Pydantic
            if (errData.detail) {
                if (typeof errData.detail === 'string') {
                    errorMessage = errData.detail;
                } else if (Array.isArray(errData.detail)) {
                    // Mapeamos errores de validación (campo: error)
                    errorMessage = errData.detail.map(e => {
                        const field = e.loc ? e.loc[1] : 'Campo';
                        return `${field}: ${e.msg}`;
                    }).join('\n');
                } else {
                    errorMessage = JSON.stringify(errData.detail);
                }
            }
            
            console.error(`API Error en ${endpoint}:`, errorMessage);
            throw new Error(errorMessage);
        }

        if (res.status === 204) return null; 
        
        const data = await res.json(); 
        return data;

    } catch (error) {
        if (!error.message.includes('Error del servidor') && !error.message.includes('API Error')) {
            console.error(` Fallo de Red/Sistema en ${endpoint}:`, error);
        }
        throw error;
    }
}

export const api = {
    login: (username, password) => {
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        return request('/user/login', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: params 
        });
    },
    register: (data) => request('/user/register', { method: 'POST', body: JSON.stringify(data) }),
    getMyBooks: () => request('/book/'),
    
    searchBooks: (q) => {
        return request(`/book/search?q=${q}&limit=8`);
    },
    
    saveBook: (data) => request('/book/', { method: 'POST', body: JSON.stringify(data) }),
    updateStatus: (id, status) => request(`/book/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }),
    deleteBook: (id) => request(`/book/${id}`, { method: 'DELETE' })
};