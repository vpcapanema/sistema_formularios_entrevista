"""Inicializa o banco persistente usado pelo deploy Docker na AWS."""

from pathlib import Path

from sqlalchemy import text

from app.database import Base, engine
import app.models  # noqa: F401  # registra os modelos no metadata


with engine.begin() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS formulario_embarcadores"))
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS dados_brasil"))

Base.metadata.create_all(bind=engine)

view_sql = (
    Path(__file__).resolve().parent.parent
    / "migrations"
    / "temp_create_view_completa.sql"
).read_text(encoding="utf-8")

raw_connection = engine.raw_connection()
try:
    with raw_connection.cursor() as cursor:
        cursor.execute(view_sql)
    raw_connection.commit()
finally:
    raw_connection.close()
