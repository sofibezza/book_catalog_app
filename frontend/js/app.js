import { store, subscribe, actions } from './store.js';
import { Auth } from './components/auth.js';
import { Dashboard } from './components/dashboard.js';
import { Search } from './components/search.js';

const app = document.getElementById('app');

console.log("Aplicación iniciada.");

function render() {
    console.log("Ciclo de actualización ejecutado.");


    if (!store.token) {
        console.log("No hay sesión activa. Renderizando Login/Registro.");
        app.innerHTML = Auth.render();
        Auth.init(render);
        return;
    }

    const isSearch = store.view === 'search';

    app.innerHTML = `
        <div class="app-container">
            <header>
                <h2>${isSearch ? 'Buscar en Google' : ' Mi Biblioteca'}</h2>
                <div style="display:flex; gap:1rem">
                    <button class="btn ${!isSearch ? 'btn-primary' : 'btn-ghost'}" id="nav-home">Mis Libros</button>
                    <button class="btn ${isSearch ? 'btn-primary' : 'btn-ghost'}" id="nav-search">Buscar Nuevo</button>
                    <button class="btn btn-danger btn-sm" id="btn-logout">Salir</button>
                </div>
            </header>
            <main id="main-content">
                ${isSearch ? Search.render() : Dashboard.render()}
            </main>
        </div>
    `;

    document.getElementById('nav-home').onclick = () => {
        console.log("Cambiando a Dashboard");
        store.view = 'dashboard';
    };

    document.getElementById('nav-search').onclick = () => {
        console.log("Cambiando a Búsqueda");
        store.view = 'search';
    };

    document.getElementById('btn-logout').onclick = () => {
        console.log("Usuario cerrando sesión...");
        actions.logout();
    };

    // Inicializar el componente actual
    try {
        if (isSearch) {
            console.log("Inicializando lógica de Search");
            Search.init();
        } else {
            console.log("Inicializando lógica de Dashboard");
            Dashboard.init();
        }
    } catch (error) {
        console.error("Fallo al inicializar componente:", error);
    }
}

subscribe(render);
render();