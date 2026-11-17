/**
 * AUTENTICAÇÃO SIMPLES - Proteção de Páginas Internas
 * Usado para esconder Respostas, Analytics e Visualizador do público
 */

class SimpleAuth {
    constructor() {
        // Senha hardcoded (você pode trocar depois)
        this.PASSWORD = 'pli2050@admin'; // ⚠️ TROCAR ESSA SENHA!
        this.STORAGE_KEY = 'pli2050_auth';
        
        // Páginas que requerem autenticação
        this.protectedPages = ['respostas', 'analytics', 'visualizador'];
    }
    
    /**
     * Verifica se usuário está autenticado
     */
    isAuthenticated() {
        try {
            const stored = localStorage.getItem(this.STORAGE_KEY);
            if (!stored) return false;
            
            const data = JSON.parse(stored);
            // Verifica se token ainda é válido (expira em 7 dias)
            const expires = new Date(data.expires);
            if (expires < new Date()) {
                this.logout();
                return false;
            }
            return data.authenticated === true;
        } catch (e) {
            // localStorage bloqueado por Tracking Prevention
            console.warn('⚠️ localStorage bloqueado - autenticação desabilitada');
            return false;
        }
    }
    
    /**
     * Tenta fazer login com senha
     */
    login(password) {
        if (password === this.PASSWORD) {
            try {
                // Salva autenticação por 7 dias
                const expires = new Date();
                expires.setDate(expires.getDate() + 7);
                
                localStorage.setItem(this.STORAGE_KEY, JSON.stringify({
                    authenticated: true,
                    expires: expires.toISOString(),
                    timestamp: new Date().toISOString()
                }));
                
                return true;
            } catch (e) {
                // localStorage bloqueado
                console.error('❌ Não foi possível salvar autenticação:', e.message);
                alert('⚠️ Seu navegador está bloqueando o armazenamento local.\nDesabilite "Tracking Prevention" ou use outro navegador.');
                return false;
            }
        }
        return false;
    }
    
    /**
     * Faz logout
     */
    logout() {
        try {
            localStorage.removeItem(this.STORAGE_KEY);
        } catch (e) {
            console.warn('⚠️ Erro ao remover autenticação:', e.message);
        }
    }
    
    /**
     * Mostra modal de login
     */
    showLoginModal() {
        // Criar modal se não existir
        let modal = document.getElementById('auth-modal');
        if (!modal) {
            modal = this.createLoginModal();
            document.body.appendChild(modal);
        }
        
        modal.style.display = 'flex';
        document.getElementById('auth-password-input').focus();
    }
    
    /**
     * Cria modal de login
     */
    createLoginModal() {
        const modal = document.createElement('div');
        modal.id = 'auth-modal';
        modal.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 10000;
            align-items: center;
            justify-content: center;
        `;
        
        modal.innerHTML = `
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 8px;
                max-width: 400px;
                width: 90%;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            ">
                <h2 style="margin-top: 0; color: #333;">🔒 Área Interna</h2>
                <p style="color: #666; margin-bottom: 1.5rem;">
                    Digite a senha para acessar Respostas, Analytics e Visualizador
                </p>
                
                <input 
                    type="password" 
                    id="auth-password-input"
                    placeholder="Senha de acesso"
                    style="
                        width: 100%;
                        padding: 0.75rem;
                        border: 2px solid #ddd;
                        border-radius: 4px;
                        font-size: 1rem;
                        margin-bottom: 1rem;
                        box-sizing: border-box;
                    "
                />
                
                <div id="auth-error" style="
                    color: #e74c3c;
                    margin-bottom: 1rem;
                    display: none;
                    font-size: 0.9rem;
                ">
                    ❌ Senha incorreta
                </div>
                
                <div style="display: flex; gap: 0.5rem;">
                    <button 
                        id="auth-submit-btn"
                        style="
                            flex: 1;
                            padding: 0.75rem;
                            background: #667eea;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 1rem;
                            font-weight: 600;
                        "
                    >
                        Entrar
                    </button>
                    <button 
                        id="auth-cancel-btn"
                        style="
                            flex: 1;
                            padding: 0.75rem;
                            background: #95a5a6;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 1rem;
                        "
                    >
                        Cancelar
                    </button>
                </div>
            </div>
        `;
        
        // Event listeners
        const passwordInput = modal.querySelector('#auth-password-input');
        const submitBtn = modal.querySelector('#auth-submit-btn');
        const cancelBtn = modal.querySelector('#auth-cancel-btn');
        const errorDiv = modal.querySelector('#auth-error');
        
        const attemptLogin = () => {
            const password = passwordInput.value;
            if (this.login(password)) {
                modal.style.display = 'none';
                passwordInput.value = '';
                errorDiv.style.display = 'none';
                this.updateUI();
                
                // Mostrar mensagem de sucesso
                alert('✅ Autenticado com sucesso! Agora você tem acesso completo.');
            } else {
                errorDiv.style.display = 'block';
                passwordInput.value = '';
                passwordInput.focus();
            }
        };
        
        submitBtn.onclick = attemptLogin;
        passwordInput.onkeypress = (e) => {
            if (e.key === 'Enter') attemptLogin();
        };
        
        cancelBtn.onclick = () => {
            modal.style.display = 'none';
            passwordInput.value = '';
            errorDiv.style.display = 'none';
        };
        
        // Fechar ao clicar fora
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
                passwordInput.value = '';
                errorDiv.style.display = 'none';
            }
        };
        
        return modal;
    }
    
    /**
     * Atualiza UI baseado no status de autenticação
     */
    updateUI() {
        const isAuth = this.isAuthenticated();
        
        // Esconder/mostrar botões de páginas protegidas
        this.protectedPages.forEach(page => {
            const btn = document.querySelector(`[onclick*="${page}"]`);
            if (btn) {
                btn.style.display = isAuth ? 'flex' : 'none';
            }
        });
        
        // Adicionar/remover botão de login
        this.updateLoginButton(isAuth);
        
        // Se não autenticado e está em página protegida, voltar pro formulário
        if (!isAuth) {
            const currentPage = this.getCurrentPage();
            if (this.protectedPages.includes(currentPage)) {
                if (window.router) {
                    window.router.navigate('formulario');
                }
            }
        }
    }
    
    /**
     * Atualiza botão de login/logout na navbar
     */
    updateLoginButton(isAuth) {
        let loginBtn = document.getElementById('auth-login-btn');
        
        if (!loginBtn) {
            // Criar botão se não existir
            const navMenu = document.querySelector('.nav-menu');
            if (!navMenu) return;
            
            loginBtn = document.createElement('button');
            loginBtn.id = 'auth-login-btn';
            loginBtn.className = 'nav-btn';
            loginBtn.style.marginLeft = 'auto';
            navMenu.appendChild(loginBtn);
        }
        
        if (isAuth) {
            loginBtn.innerHTML = '<span>🔓</span> Sair';
            loginBtn.onclick = () => {
                if (confirm('Tem certeza que deseja sair da área interna?')) {
                    this.logout();
                    this.updateUI();
                    alert('✅ Logout realizado com sucesso!');
                    if (window.router) {
                        window.router.navigate('formulario');
                    }
                }
            };
        } else {
            loginBtn.innerHTML = '<span>🔒</span> Área Interna';
            loginBtn.onclick = () => this.showLoginModal();
        }
    }
    
    /**
     * Pega página atual baseada no arquivo HTML
     */
    getCurrentPage() {
        const fileName = window.location.pathname.split('/').pop();
        if (fileName === 'respostas.html') return 'respostas';
        if (fileName === 'analytics.html') return 'analytics';
        if (fileName === 'visualizador_dados.html') return 'visualizador';
        if (fileName === 'instrucoes.html') return 'instrucoes';
        return 'formulario';
    }
    
    /**
     * Intercepta navegação para páginas protegidas
     */
    interceptNavigation() {
        const originalNavigate = window.navegarPara;
        if (!originalNavigate) return;
        
        window.navegarPara = (pagina) => {
            if (this.protectedPages.includes(pagina) && !this.isAuthenticated()) {
                this.showLoginModal();
                return;
            }
            originalNavigate(pagina);
        };
    }
    
    /**
     * Verifica se está em página protegida sem autenticação
     */
    checkPageAccess() {
        const currentPage = this.getCurrentPage();
        if (this.protectedPages.includes(currentPage) && !this.isAuthenticated()) {
            alert('⚠️ Acesso negado! Esta página requer autenticação.');
            window.location.href = './';
        }
    }
    
    /**
     * Inicializa autenticação
     */
    init() {
        // Verificar acesso à página atual
        this.checkPageAccess();
        
        // Atualizar UI inicial
        this.updateUI();
        
        // Interceptar navegação
        setTimeout(() => this.interceptNavigation(), 100);
        
        console.log('🔒 Autenticação simples carregada');
    }
}

// Instanciar e inicializar
const auth = new SimpleAuth();

// Inicializar após DOM carregar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => auth.init());
} else {
    auth.init();
}

// Exportar para uso global
window.auth = auth;
