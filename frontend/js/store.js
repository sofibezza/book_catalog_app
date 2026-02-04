const initialState = {
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('access_token') || null,
    view: 'dashboard', // dashboard | search
    myBooks: { data: [], status: 'idle', error: null }, // status: idle | loading | success | error
    searchResults: { data: [], status: 'idle', error: null }
};

// Log inicial del estado al cargar la app
console.log("Estado Inicial:", initialState);

const observers = new Set();

export const store = new Proxy(initialState, {
    set(target, key, value) {
        console.log(`⚡ [State Change] ${key} =`, value);

        target[key] = value;
        
        observers.forEach(fn => fn(target)); 
        return true;
    }
});

export const subscribe = (fn) => {
    observers.add(fn);
    fn(store);
    return () => observers.delete(fn);
};

export const actions = {
    logout: () => {
        console.log("👋 [Store] Ejecutando Logout...");
        store.user = null;
        store.token = null;
 
        store.view = 'dashboard';
        store.myBooks = { data: [], status: 'idle', error: null };
        
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
    },
    
    setLogin: (token, user) => {
        console.log("🔑 [Store] Guardando sesión de:", user.email);
        
        // Actualiza localStorage
        localStorage.setItem('access_token', token);
        localStorage.setItem('user', JSON.stringify(user));
        
        store.token = token;
        store.user = user;
    }
};