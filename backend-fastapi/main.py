"""
============================================================
MAIN APPLICATION - FastAPI PLI 2050
============================================================
API REST para Sistema de Formulários de Entrevistas
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging
import os
from dotenv import load_dotenv
from pathlib import Path

# Import routers (modularizados por domínio)
from app.routers.health import routes as health_router
from app.routers.submit import routes as submit_router
# NOVO: Router de pesquisas
from app.routers.pesquisas import router as pesquisas_router
# NOVO: Router de entrevistadores (dados completos + instituição)
from app.routers.entrevistadores import routes as entrevistadores_router
# DEPRECATED: Agora são JSONs estáticos
# from app.routers.lists import routes as lists_router
from app.routers.analytics import routes as analytics_router
from app.routers.external import router as external_router

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# CRIAR APLICAÇÃO FASTAPI
# ============================================================

app = FastAPI(
    title="PLI 2050 - API Sistema de Formulários",
    description=(
        "API REST para coleta de dados de entrevistas com empresas "
        "embarcadoras de São Paulo"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================
# CORS MIDDLEWARE
# ============================================================

# Origens permitidas (localhost + produção GitHub Pages)
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500,"
    "http://localhost:8000,http://127.0.0.1:8000,"
    "http://localhost:8010,http://127.0.0.1:8010,"
    "https://vpcapanema.github.io"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"✅ CORS habilitado para: {allowed_origins}")

# ============================================================
# MIDDLEWARE DE CACHE PARA ARQUIVOS ESTÁTICOS
# ============================================================


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Adiciona headers de cache para arquivos estáticos
    - JSONs de listas: cache 1 ano (31536000s)
    - Outros estáticos (CSS/JS): cache 1 hora (3600s)
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Cache agressivo para JSONs de listas (raramente mudam)
        if request.url.path.startswith("/lists/"):
            response.headers["Cache-Control"] = (
                "public, max-age=31536000, immutable"
            )
            response.headers["X-Cache-Strategy"] = "1-year (static data)"

        # Cache moderado para CSS/JS (podem ter atualizações)
        elif any(
            request.url.path.startswith(prefix)
            for prefix in ["/css/", "/js/", "/vendor/"]
        ):
            response.headers["Cache-Control"] = \
                "public, max-age=3600"
            response.headers["X-Cache-Strategy"] = \
                "1-hour (dynamic assets)"

        return response


# app.add_middleware(CacheControlMiddleware)
# logger.info(
#     "✅ Cache Control middleware habilitado "
#     "(JSONs: 1 ano, assets: 1 hora)"
# )

# ============================================================
# MONTAR ARQUIVOS ESTÁTICOS DO FRONTEND (se existir)
# ============================================================

# Caminho para o frontend (relativo ao backend-fastapi)
frontend_path = Path(__file__).parent.parent / "frontend"

# Montar arquivos estáticos APENAS se diretórios existirem
# Em produção, quando o repositório incluir o frontend, isso permite servir
if frontend_path.exists():
    try:
        # CSS
        if (frontend_path / "css").exists():
            app.mount(
                "/css",
                StaticFiles(directory=str(frontend_path / "css")),
                name="css"
            )

        # JS
        if (frontend_path / "js").exists():
            app.mount(
                "/js",
                StaticFiles(directory=str(frontend_path / "js")),
                name="js"
            )

        # Assets
        if (frontend_path / "assets").exists():
            app.mount(
                "/assets",
                StaticFiles(directory=str(frontend_path / "assets")),
                name="assets"
            )

        # Vendor
        if (frontend_path / "vendor").exists():
            app.mount(
                "/vendor",
                StaticFiles(directory=str(frontend_path / "vendor")),
                name="vendor"
            )

        # HTML (páginas estáticas)
        if (frontend_path / "html").exists():
            app.mount(
                "/html",
                StaticFiles(directory=str(frontend_path / "html"), html=True),
                name="html"
            )

        # JSONs de listas (frontend/html/lists)
        lists_path = frontend_path / "html" / "lists"
        if lists_path.exists():
            app.mount(
                "/lists",
                StaticFiles(directory=str(lists_path)),
                name="lists"
            )
            logger.info("📂 JSONs de listas disponíveis em: /lists/")

        logger.info(f"📁 Frontend estático montado de: {frontend_path}")
    except Exception as e:
        logger.warning(f"⚠️  Erro ao montar frontend: {e}")
        logger.warning("⚠️  API rodando SEM arquivos estáticos (modo API-only)")
else:
    logger.info("📡 Modo API-only (frontend não encontrado - normal em produção)")
    logger.info("📡 Frontend servido separadamente via GitHub Pages")

# ============================================================
# REGISTRAR ROUTERS (MODULARIZADOS)
# ============================================================

app.include_router(health_router.router)    # GET /health, /info
app.include_router(submit_router.router)    # POST /api/submit-form, /api/submit-form-divided
app.include_router(entrevistadores_router.router)  # GET /api/entrevistadores, /api/entrevistadores/{id}
app.include_router(pesquisas_router)        # GET /api/pesquisas/* - Listagem e visualização
app.include_router(analytics_router.router)  # GET /api/analytics/* - KPIs e gráficos
# app.include_router(lists_router.router)   # DEPRECATED: JSONs estáticos

# GET /api/external/cnpj/* - Consulta CNPJ na Receita Federal via BrasilAPI
app.include_router(
    external_router,
    prefix="/api/external",
    tags=["External APIs"]
)

# ============================================================
# ROOT ENDPOINT - SERVIR INDEX.HTML
# ============================================================


@app.get("/")
async def root():
    """
    Root endpoint - redireciona para /info em produção
    Serve index.html em desenvolvimento (se frontend existir)
    """
    # Possíveis localizações do index.html (ambientes variados)
    candidate_paths = []

    # 1) Padrão do repositório: frontend/html/index.html
    candidate_paths.append(frontend_path / "html" / "index.html")

    # 2) Padrão alternativo: frontend/index.html
    candidate_paths.append(frontend_path / "index.html")

    # 3) Caminho absoluto configurável via ENV (útil em containers/prod)
    env_path = os.getenv('FRONTEND_STATIC_PATH')
    if env_path:
        candidate_paths.append(Path(env_path) / "index.html")

    # 4) Caminhos relativos à raiz do projeto (quando executado fora do package)
    candidate_paths.append(Path.cwd() / "frontend" / "html" / "index.html")
    candidate_paths.append(Path.cwd() / "frontend" / "index.html")

    # Retornar o primeiro index.html encontrado
    for p in candidate_paths:
        try:
            if p and p.exists():
                logger.info(f"📄 Servindo frontend index.html de: {p}")
                return FileResponse(str(p))
        except Exception:
            # ignorar erros de permissão e continuar buscando
            continue

    # Em produção (sem frontend disponível), redirecionar para GitHub Pages se configurado
    from fastapi.responses import RedirectResponse
    pages_url = os.getenv('FRONTEND_PAGES_URL') or 'https://vpcapanema.github.io/formulario_entrevista_embarcadores/html/index.html'
    logger.info(f"📡 Frontend não encontrado localmente - redirecionando para {pages_url}")
    return RedirectResponse(url=pages_url)


# ============================================================
# ROTAS PARA PÁGINAS HTML (fallback para navegação SPA)
# ============================================================

@app.get("/glossario.html")
@app.get("/glossario")
async def serve_glossario():
    """Serve o glossário também a partir da página inicial na raiz."""
    return FileResponse(str(frontend_path / "html" / "glossario.html"))


@app.get("/respostas.html")
@app.get("/respostas")
async def serve_respostas():
    """Serve a página de respostas"""
    html_path = frontend_path / "html" / "respostas.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"error": "Página não encontrada", "path": str(html_path)}


@app.get("/analytics.html")
@app.get("/analytics")
async def serve_analytics():
    """Serve a página de analytics"""
    html_path = frontend_path / "html" / "analytics.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"error": "Página não encontrada", "path": str(html_path)}


@app.get("/instrucoes.html")
@app.get("/instrucoes")
async def serve_instrucoes():
    """Serve a página de instruções"""
    html_path = frontend_path / "html" / "instrucoes.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"error": "Página não encontrada", "path": str(html_path)}


@app.get("/visualizador_dados.html")
@app.get("/visualizador")
async def serve_visualizador():
    """Serve a página do visualizador"""
    html_path = frontend_path / "html" / "visualizador_dados.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"error": "Página não encontrada", "path": str(html_path)}


@app.get("/index.html")
@app.get("/formulario")
async def serve_formulario():
    """Serve a página do formulário"""
    html_path = frontend_path / "html" / "index.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"error": "Página não encontrada", "path": str(html_path)}


@app.get("/debug/frontend-files")
async def debug_frontend_files():
    """Endpoint temporário de debug que lista possíveis caminhos e arquivos encontrados."""
    results = {}

    candidate_paths = {
        'repo_frontend_html': frontend_path / 'html',
        'repo_frontend_root': frontend_path,
        'cwd_frontend_html': Path.cwd() / 'frontend' / 'html',
        'cwd_frontend_root': Path.cwd() / 'frontend'
    }

    env_path = os.getenv('FRONTEND_STATIC_PATH')
    if env_path:
        candidate_paths['env_frontend'] = Path(env_path)

    for name, p in candidate_paths.items():
        try:
            exists = p.exists()
            files = []
            if exists and p.is_dir():
                # listar até 100 itens para evitar payload grande
                for i, child in enumerate(sorted(p.iterdir())):
                    if i >= 100:
                        files.append('...')
                        break
                    files.append(child.name)
            results[name] = {
                'path': str(p),
                'exists': exists,
                'is_dir': p.is_dir() if p.exists() else False,
                'sample_files': files
            }
        except Exception as e:
            results[name] = {'path': str(p), 'error': str(e)}

    # Checar especificamente por index.html e lists/estados.json nas localizações mais prováveis
    checks = []
    check_paths = [
        frontend_path / 'html' / 'index.html',
        frontend_path / 'index.html',
        frontend_path / 'html' / 'lists' / 'estados.json',
    ]
    if env_path:
        check_paths.extend([Path(env_path) / 'index.html', Path(env_path) / 'lists' / 'estados.json'])

    for cp in check_paths:
        try:
            checks.append({'path': str(cp), 'exists': cp.exists(), 'size': cp.stat().st_size if cp.exists() else None})
        except Exception:
            checks.append({'path': str(cp), 'exists': False, 'error': 'stat failed'})

    return {
        'summary': 'debug frontend files',
        'candidates': results,
        'checks': checks
    }


# ============================================================
# STARTUP EVENT
# ============================================================


# @app.on_event("startup")
# async def startup_event():
#     """
#     Executa ao iniciar a aplicação
#     """
#     logger.info("="*60)
#     logger.info("🚀 PLI 2050 - API Sistema de Formulários v2.0.0")
#     logger.info("="*60)
#     logger.info("📡 Framework: FastAPI")
#     logger.info("📊 Database: PostgreSQL (RDS AWS)")
#     logger.info(
#         f"🔒 CORS: {len(allowed_origins)} origens permitidas"
#     )
#     logger.info("")
# 
#     # Testar conexão com banco de dados
#     try:
#         logger.info("🔍 Testando conexão com banco de dados...")
#         # Temporariamente desabilitado para debug
#         logger.info("✅ Teste de conexão temporariamente desabilitado")
#     except Exception as e:
#         logger.error(f"❌ Erro na conexão com banco: {e}")
#         logger.error("🛑 Servidor será interrompido devido a erro de banco")
#         # Não levantar exceção aqui pois pode causar problemas no startup
#         # Apenas logar o erro
# 
#     logger.info("🌐 URLs Disponíveis:")
#     logger.info("   🏠 Frontend: http://localhost:8010/")
#     logger.info(
#         "   📋 Formulário: http://localhost:8010/html/index.html"
#     )
#     logger.info(
#         "   📊 Analytics: http://localhost:8010/html/analytics.html"
#     )
#     logger.info(
#         "   📄 Respostas: http://localhost:8010/html/respostas.html"
#     )
#     logger.info("   📚 API Docs: http://localhost:8010/docs")
#     logger.info("   🏥 Health Check: http://localhost:8010/health")
#     logger.info("")
#     logger.info("="*60)


# ============================================================
# SHUTDOWN EVENT
# ============================================================


# @app.on_event("shutdown")
# async def shutdown_event():
#     """
#     Executa ao desligar a aplicação
#     """
#     logger.info("⏹️  Desligando API PLI 2050...")
#     logger.info("✅ API finalizada")


# ============================================================
# EXECUTAR SERVIDOR (se rodado como script)
# ============================================================


if __name__ == "__main__":
    import uvicorn
    
    # Configurações
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("UVICORN_PORT", "8000"))
    
    # Rodar servidor
    uvicorn.run(
        "main:app",  # String path
        host=host,
        port=port,
        reload=False,  # Reload desabilitado para testes
        log_level="info"
    )
