import { api } from '../api.js';

export function renderModal(initialData = {}, onClose = () => {}, onSuccess = () => {}) {
    const modalRoot = document.getElementById('modal-root');
    
    // Normalización de datos
    const title = initialData.title || '';
    const author = Array.isArray(initialData.authors) ? initialData.authors[0] : (initialData.author || '');
    const isbn = initialData.isbn || '';
    const year = initialData.publication_year || (initialData.published_date ? initialData.published_date.substring(0, 4) : '');
    const description = initialData.description || '';
    const cover = initialData.cover_url || initialData.thumbnail || '';

    // Renderizamos el HTML
    modalRoot.innerHTML = `
        <div class="modal-overlay" id="modal-overlay">
            <div class="modal-content">
                <h2 style="margin-bottom: 1rem;">
                    ${title ? 'Editar Libro' : 'Nuevo Libro'}
                </h2>

                <div id="modal-error" style="
                    display: none; 
                    background-color: #fee2e2; 
                    color: #dc2626; 
                    padding: 0.75rem; 
                    border-radius: 8px; 
                    margin-bottom: 1rem; 
                    font-size: 0.9rem;
                    text-align: center;">
                </div>

                <form id="book-form">
                    <div class="form-group">
                        <label>Título *</label>
                        <input type="text" id="m-title" value="${title}" required>
                    </div>

                    <div class="form-group">
                        <label>Autor *</label>
                        <input type="text" id="m-author" value="${author}" required placeholder="Ej. J.K. Rowling">
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div class="form-group">
                            <label>Año</label>
                            <input type="number" id="m-year" value="${year}" placeholder="2024">
                        </div>
                        <div class="form-group">
                            <label>ISBN</label>
                            <input type="text" id="m-isbn" value="${isbn}">
                        </div>
                    </div>

                    <div class="form-group">
                        <label>URL de Portada (Imagen)</label>
                        <input type="text" id="m-cover" value="${cover}" placeholder="https://...">
                    </div>

                    <div class="form-group">
                        <label>Descripción</label>
                        <textarea id="m-desc" rows="3" style="width:100%; padding:0.5rem; border:1px solid var(--border); border-radius:8px;">${description}</textarea>
                    </div>

                    <div style="display: flex; justify-content: flex-end; gap: 1rem; margin-top: 2rem;">
                        <button type="button" class="btn btn-ghost" id="modal-cancel">Cancelar</button>
                        <button type="submit" class="btn btn-primary" id="modal-save">Guardar Libro</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    modalRoot.classList.remove('hidden');

    const closeModal = () => {
        modalRoot.classList.add('hidden');
        modalRoot.innerHTML = ''; 
        onClose();
    };

    document.getElementById('modal-cancel').onclick = closeModal;
    document.getElementById('modal-overlay').onclick = (e) => {
        if (e.target.id === 'modal-overlay') closeModal();
    };

    // --- LÓGICA DE GUARDADO ---
    const form = document.getElementById('book-form');
    const errorBox = document.getElementById('modal-error');
    
    form.onsubmit = async (e) => {
        e.preventDefault();

        const btn = document.getElementById('modal-save');
        const originalText = btn.textContent;
        
        // Limpiar errores previos
        errorBox.style.display = 'none';
        errorBox.textContent = '';

        const rawIsbn = document.getElementById('m-isbn').value.trim();
        const titleVal = document.getElementById('m-title').value.trim();
        
        console.log(`📝 [Modal] Iniciando guardado de: "${titleVal}"`);

        const newBookData = {
            title: titleVal,
            author: document.getElementById('m-author').value.trim(),
            publication_year: parseInt(document.getElementById('m-year').value) || null,
            isbn: rawIsbn === "" ? null : rawIsbn,
            cover_url: document.getElementById('m-cover').value.trim(),
            description: document.getElementById('m-desc').value.trim()
        };

        console.log("Payload a enviar:", newBookData);

        try {
            btn.textContent = 'Guardando...';
            btn.disabled = true;

            await api.saveBook(newBookData);

            console.log("Guardado exitoso.");
            closeModal();
            onSuccess();
            
        } catch (err) {
            console.error("Falló el guardado:", err);

            errorBox.style.display = 'block';

            errorBox.textContent = `No se pudo guardar: ${err.message}`;

            // Restauramos el botón para permitir reintentar
            btn.textContent = originalText;
            btn.disabled = false;
        }
    };
}