import { api } from '../api.js';
import { debounce } from '../utils.js';
import { renderModal } from './modal.js';
import { store } from '../store.js';

export const Search = {
    render: () => {
        return `
            <div style="max-width: 600px; margin: 0 auto 2rem auto;">
                <div class="form-group">
                    <input type="text" id="search-input" 
                           placeholder="Escribe título, autor o ISBN..." 
                           autocomplete="off"
                           style="padding: 1rem; font-size: 1.1rem; box-shadow: var(--shadow-lg);">
                </div>
                <p style="text-align: center; font-size: 0.85rem; color: var(--text-muted);">
                    Busca en Google Books y guarda en tu colección
                </p>
            </div>
            <div id="search-results-area"></div>
        `;
    },

    init: () => {
        const input = document.getElementById('search-input');
        const resultsArea = document.getElementById('search-results-area');

        // Evitar scroll con espacio
        input.addEventListener('keydown', (e) => {
            if (e.key === ' ') e.stopPropagation(); 
        });

        const drawResults = (books) => {
            // Sin resultados
            if (!books || books.length === 0) {
                console.log(" Búsqueda sin resultados. Mostrando opción manual.");
                
                resultsArea.innerHTML = `
                    <div style="text-align: center; margin-top: 2rem;">
                        <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 1.1rem;">
                            No se encontró nada con ese nombre.
                        </p>
                        <button class="btn btn-primary" id="btn-manual-add">
                            Agregar manualmente
                        </button>
                    </div>
                `;

                // Botón Manual
                document.getElementById('btn-manual-add').onclick = () => {
                    const currentSearchTerm = input.value;
                    console.log("Usuario inicia creación manual para:", currentSearchTerm); 
                    
                    renderModal(
                        { title: currentSearchTerm }, 
                        () => console.log(" Creación manual cancelada"), 
                        () => {   // OnSuccess
                            console.log(" Libro manual creado exitosamente");
                            store.myBooks = { ...store.myBooks, status: 'idle' };
                            
                            input.value = '';
                            resultsArea.innerHTML = `
                                <div style="text-align: center; margin-top: 2rem; color: var(--primary);">
                                    <h3>✅ ¡Libro creado!</h3>
                                    <p>Ya puedes verlo en "Mis Libros".</p>
                                </div>
                            `;
                        }
                    );
                };
                return;
            }

            // Lista de Resultados
            console.log(`Renderizando ${books.length} tarjetas de libros.`);
            
            resultsArea.innerHTML = `
                <div class="book-grid">
                    ${books.map(book => `
                        <div class="book-card">
                            <div class="book-cover">
                                ${book.cover_url 
                                    ? `<img src="${book.cover_url}" alt="${book.title}">` 
                                    : '<div style="height:100%; display:flex; align-items:center; justify-content:center; background:#eee; color:#666">Sin Portada</div>'}
                            </div>
                            <div class="book-info">
                                <h3 class="book-title">${book.title}</h3>
                                <p class="book-author">${book.author || 'Autor desconocido'}</p>
                                
                                <div style="margin-top:auto">
                                    <button class="btn btn-primary btn-sm save-btn" 
                                            style="width:100%" 
                                            data-book='${JSON.stringify(book).replace(/'/g, "&apos;")}'>
                                         Guardar
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        };

        // EVENTO INPUT
        input.addEventListener('input', debounce(async (e) => {
            const q = e.target.value.trim();
            if (q.length < 2) { 
                resultsArea.innerHTML = ''; 
                return; 
            }

            console.log(` Buscando: "${q}"`);
            resultsArea.innerHTML = '<div class="spinner"></div>';
            
            try {
                const results = await api.searchBooks(q);
                console.log(" Datos recibidos de API:", results);
                drawResults(results);
            } catch (err) {
                console.error(" Error crítico buscando libros:", err);
                resultsArea.innerHTML = `<p style="color:var(--danger); text-align:center">Error de conexión: ${err.message}</p>`;
            }
        }, 500));

        // EVENTO GUARDAR
        resultsArea.addEventListener('click', (e) => {
            if (e.target.closest('.save-btn')) {
                const btn = e.target.closest('.save-btn');
                const bookData = JSON.parse(btn.dataset.book);
                
                console.log("💾 Click en Guardar para:", bookData.title);
                handleSaveDirect(bookData, btn);
            }
        });
    }
};

// Función de Guardado Directo
async function handleSaveDirect(book, btnElement) {
    if (book.title && book.author) {
        try {
            const originalText = btnElement.textContent;
            btnElement.textContent = 'Guardando...';
            btnElement.disabled = true;

            await api.saveBook({
                title: book.title,
                author: book.author,
                isbn: book.isbn,
                publication_year: book.publication_year,
                description: book.description,
                cover_url: book.cover_url
            });

            console.log("✅ Guardado directo exitoso:", book.title); // LOG

            btnElement.textContent = '¡Guardado!';
            btnElement.classList.replace('btn-primary', 'btn-ghost');
            
            // Sincronizar Store
            store.myBooks = { ...store.myBooks, status: 'idle' };

        } catch (err) {
            console.error("❌ Falló el guardado directo:", err); // LOG ERROR
            
            btnElement.textContent = 'Error';
            btnElement.title = err.message; 
            btnElement.classList.replace('btn-primary', 'btn-danger'); 
            
            setTimeout(() => {
                btnElement.textContent = '💾 Reintentar';
                btnElement.disabled = false;
                btnElement.classList.replace('btn-danger', 'btn-primary');
            }, 2000);
        }
    } else {
        console.warn("⚠️ Datos incompletos (Falta autor/título). Abriendo modal."); // LOG WARN
        
        renderModal(
            book, 
            () => { 
                console.log("✖️ Edición en modal cancelada"); 
                btnElement.disabled = false; 
            }, 
            () => { 
                console.log(" Guardado vía modal exitoso"); 
                btnElement.textContent = '¡Guardado Manual!';
                btnElement.disabled = true;
                btnElement.classList.replace('btn-primary', 'btn-ghost');
                
                store.myBooks = { ...store.myBooks, status: 'idle' };
            }
        );
    }
}