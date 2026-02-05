import { api } from '../api.js';
import { store } from '../store.js';

export const Dashboard = {
    render: () => {
        const { status, data, error } = store.myBooks;

        // Estados de Carga y Error
        if (status === 'idle') return '<div class="spinner"></div>';
        
        if (status === 'loading') return `
            <div style="text-align: center; margin-top: 3rem;">
                <div class="spinner"></div>
                <p style="color: var(--text-muted); margin-top: 1rem">Sincronizando biblioteca...</p>
            </div>`;
        
        if (error) return `
            <div style="text-align: center; color: var(--danger); margin-top: 2rem;">
                <h3>Error de Sincronización</h3>
                <p>${error}</p>
                <button class="btn btn-ghost" id="retry-btn">Reintentar</button>
            </div>`;
        
        if (data.length === 0) return `
            <div style="text-align: center; margin-top: 4rem; color: var(--text-muted);">
                <div style="font-size: 3rem; margin-bottom: 1rem;"></div>
                <h3>Tu biblioteca está vacía</h3>
                <p>Ve a "Buscar Nuevo" para agregar tu primer libro.</p>
            </div>`;

        // Renderizado de la Lista
        return `
            <div class="book-grid" id="dashboard-grid">
                ${data.map(book => `
                    <div class="book-card" style="opacity: ${book.status === 'read' ? 0.7 : 1}">
                        <div class="book-cover">
                             ${book.cover_url 
                                ? `<img src="${book.cover_url}" alt="${book.title}">` 
                                : '<div style="height:100%; display:flex; align-items:center; justify-content:center; background:#eee; color:#666">Sin Portada</div>'}
                        </div>
                        
                        <div class="book-info">
                            <span class="badge ${book.status === 'read' ? 'badge-read' : 'badge-pending'}">
                                ${book.status === 'read' ? 'LEÍDO' : 'PENDIENTE'}
                            </span>
                            
                            <h3 class="book-title">${book.title}</h3>
                            <p class="book-author">${book.author}</p>
                            
                            <div style="margin-top: auto; padding-top: 1rem; display: flex; gap: 0.5rem;">
                                ${book.status !== 'read' ? `
                                    <button class="btn btn-primary btn-sm mark-read-btn" data-id="${book.id}">
                                        ✓ Leído
                                    </button>
                                ` : ''}
                                <button class="btn btn-danger btn-sm delete-btn" data-id="${book.id}">
                                    🗑️
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    },

    init: () => {
        const { status } = store.myBooks;
        if (status === 'idle') loadBooks();

        const grid = document.getElementById('dashboard-grid');
        const retryBtn = document.getElementById('retry-btn');

        if (retryBtn) retryBtn.onclick = loadBooks;

        if (grid) {
            grid.addEventListener('click', async (e) => {
                const id = e.target.dataset.id;
                if (!id) return;

                // Manejo marcar como leido
                if (e.target.closest('.mark-read-btn')) {
                    const btn = e.target.closest('.mark-read-btn');
                    try {
                        btn.disabled = true;
                        btn.textContent = '...';
                        
                        await api.updateStatus(id, 'read');
                        loadBooks(); // Recarga exitosa

                    } catch (err) {
                        console.error(`Error actualizando libro ${id}:`, err);
                        alert(`No se pudo actualizar: ${err.message}`);
                        btn.disabled = false;
                        btn.textContent = ' Leído';
                    }
                } 
                
                // Manejo borrar libro
                else if (e.target.closest('.delete-btn')) {
                    const btn = e.target.closest('.delete-btn');
                    
                    if (confirm('¿Estás seguro de eliminar este libro de tu colección?')) {
                        try {
                            btn.disabled = true; // Evitar doble click
                            await api.deleteBook(id);
                            loadBooks(); // Recarga exitosa

                        } catch (err) {
                            console.error(`Error eliminando libro ${id}:`, err);
                            alert(`Error al eliminar: ${err.message}`);
                            btn.disabled = false;
                        }
                    }
                }
            });
        }
    }
};

async function loadBooks() {
    console.log("🔄 Sincronizando libros...");
    store.myBooks = { ...store.myBooks, status: 'loading' };
    
    try {
        const books = await api.getMyBooks();
        store.myBooks = { data: books, status: 'success', error: null };
        console.log(` ${books.length} libros cargados.`);
    } catch (err) {
        console.error("Fallo crítico al cargar Dashboard:", err);
        store.myBooks = { data: [], status: 'error', error: err.message };
    }
}