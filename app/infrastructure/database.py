"""Camada de persistência de metadados via SQLAlchemy 2.0.

Na Fase 0 fornecemos apenas o engine, a fábrica de sessões e um ``health_check``
para validar a conectividade. O schema de domínio será adicionado nas fases
seguintes, conforme a necessidade de cada feature.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Classe base declarativa para os modelos ORM."""


def _build_engine() -> Engine:
    """Cria o engine SQLAlchemy a partir das configurações."""
    settings = get_settings()
    connect_args = (
        {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    )
    return create_engine(
        settings.database_url,
        echo=settings.debug and not settings.is_production,
        connect_args=connect_args,
        future=True,
    )


engine: Engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    """Fornece uma sessão transacional com commit/rollback automático."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logger.error("database_session_rollback", exc_info=True)
        raise
    finally:
        session.close()


def health_check() -> bool:
    """Verifica a conectividade com o banco de metadados.

    Returns:
        ``True`` se a consulta de verificação for bem-sucedida.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.error("database_health_check_failed", exc_info=True)
        return False
