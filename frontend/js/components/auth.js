import { api } from '../api.js';
import { actions } from '../store.js';

let isLoginMode = true;

export const Auth = {
    render: () => {
        return `
            <div class="auth-wrapper">
                <div class="card">
                    <h1 style="text-align:center; margin-bottom:1.5rem">Book Tracker</h1>
                    <h2 style="margin-bottom:1rem; color: var(--primary)">${isLoginMode ? 'Iniciar Sesión' : 'Crear Cuenta'}</h2>
                    
                    <div id="auth-error" style="
                        display: none; 
                        background-color: #fee2e2; 
                        color: #dc2626; 
                        padding: 0.75rem; 
                        border-radius: 8px; 
                        margin-bottom: 1rem; 
                        font-size: 0.9rem;
                        text-align: center;">
                    </div>

                    <form id="auth-form">
                        ${!isLoginMode ? `<div class="form-group"><label>Username</label><input type="text" name="username" required minlength="3"></div>` : ''}
                        
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" name="email" required>
                        </div>
                        
                        <div class="form-group">
                            <label>Password</label>
                            <input type="password" name="password" required>
                        </div>
                        
                        <button type="submit" id="submit-btn" class="btn btn-primary" style="width:100%; margin-top: 1rem">
                            ${isLoginMode ? 'Entrar' : 'Registrarse'}
                        </button>
                    </form>
                    
                    <div style="text-align:center; margin-top:1.5rem; border-top: 1px solid var(--border); padding-top: 1rem;">
                        <button class="btn btn-ghost" id="toggle-auth" style="color: var(--primary)">
                            ${isLoginMode ? '¿No tienes cuenta? Regístrate' : '¿Ya tienes cuenta? Ingresa'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    init: (rerenderCallback) => {
        const toggleBtn = document.getElementById('toggle-auth');
        if (toggleBtn) {
            toggleBtn.onclick = () => {
                isLoginMode = !isLoginMode;
                rerenderCallback();
            };
        }

        // Manejo del Formulario
        const form = document.getElementById('auth-form');
        const errorBox = document.getElementById('auth-error');
        const submitBtn = document.getElementById('submit-btn');

        if (form) {
            form.onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());

                errorBox.style.display = 'none';
                errorBox.textContent = '';
                
                const originalBtnText = submitBtn.textContent;
                submitBtn.disabled = true; // Bloqueamos botón
                submitBtn.textContent = 'Procesando...';

                try {
                    if (!isLoginMode) {
                        // REGISTRO
                        await api.register({ email: data.email, username: data.username, password: data.password });
                        alert('¡Registro exitoso! Por favor inicia sesión.');
                        isLoginMode = true;
                        rerenderCallback();
                    } else {
                        // LOGIN
                        const res = await api.login(data.email, data.password);
                        actions.setLogin(res.access_token, { email: data.email });
                    }

                } catch (err) {
                    console.error("Error de Autenticación:", err);

                    // Mensaje visual para el usuario
                    errorBox.textContent = err.message || "Ocurrió un error inesperado";
                    errorBox.style.display = 'block';

                } finally {
                    // RESTAURAR ESTADO
                    submitBtn.disabled = false; // Desbloqueamos botón
                    submitBtn.textContent = originalBtnText; // Texto original
                }
            };
        }
    }
};