/**
 * NAVBAR - Navegação com SPA Router
 * Usa History API para URLs limpas sem recarregar
 */

function navegarPara(pagina) {
    // Se o router estiver disponível, usa navegação SPA
    if (window.router) {
        window.router.navigate(pagina);
    } else {
        // Fallback: abrir em nova aba (caso router não carregue)
        const urls = {
            'formulario': './',
            'respostas': './respostas',
            'analytics': './analytics',
            'instrucoes': './instrucoes',
            'visualizador': './visualizador'
        };
        
        const url = urls[pagina];
        if (url) {
            window.open(url, '_blank');
        }
    }
}

console.log('✅ Navbar carregado - navegarPara() disponível');
