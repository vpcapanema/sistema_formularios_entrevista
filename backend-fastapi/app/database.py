"""
============================================================
DATABASE CONNECTION - FastAPI PLI 2050
============================================================
Gerenciamento de conexões PostgreSQL com pool otimizado
"""

from typing import Generator
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# ============================================================
# CARREGA .env DO DIRETÓRIO CORRETO (backend-fastapi/)
# ============================================================
# Detecta diretório do arquivo atual e carrega .env do pai (backend-fastapi/)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

print(f"📁 Carregando .env de: {env_path}")
print(f"🔗 DATABASE_URL configurada: {os.getenv('DATABASE_URL', 'NÃO DEFINIDA')[:50]}...")

# Database URL - Render PostgreSQL (PRODUÇÃO)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/formulario_pli"
)

# Schema name
SCHEMA_NAME = os.getenv("SCHEMA_NAME", "formulario_embarcadores")

# Engine com pool otimizado para Render PostgreSQL
engine = create_engine(
    DATABASE_URL,
    # ============================================================
    # CONNECTION POOL - Otimizado para Produção
    # ============================================================
    pool_size=10,              # Conexões persistentes no pool
    max_overflow=20,           # Conexões extras sob demanda (picos de tráfego)
    pool_timeout=30,           # Timeout para obter conexão (segundos)
    pool_recycle=3600,         # ✅ OTIMIZADO: Recicla após 1h (era 30min)
    pool_pre_ping=True,        # Testa conexão antes de usar (evita "server has gone away")

    # ============================================================
    # PERFORMANCE
    # ============================================================
    echo=False,                # Logs SQL (True apenas em debug)
    echo_pool=False,           # Logs de pool (False em produção)

    # ============================================================
    # POSTGRESQL ESPECÍFICO - Render
    # ============================================================
    connect_args={
        "options": f"-csearch_path={SCHEMA_NAME},public -c timezone=America/Sao_Paulo",
        "sslmode": os.getenv("POSTGRES_SSLMODE", "require"),
        "connect_timeout": 10,         # Timeout de conexão
        "application_name": "PLI2050_FastAPI"  # Identificação no pg_stat_activity
    }
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class para models
Base = declarative_base()


# Dependency para FastAPI
def get_db() -> Generator:
    """
    Dependency que fornece session do database.
    Usa yield para garantir fechamento mesmo em caso de erro.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
