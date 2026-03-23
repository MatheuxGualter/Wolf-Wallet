"""
🐺 Wolf Wallet — Cookie-Based Session Persistence

Persiste a sessão do usuário via cookies do navegador usando
extra-streamlit-components.CookieManager.

Quando o usuário faz login, grava um cookie com o user_id + token.
No F5 ou troca de aba, o cookie é lido e a sessão restaurada automaticamente.

Usage:
    from auth.cookie_session import save_session_cookie, restore_session_from_cookie, clear_session_cookie
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

import streamlit as st

logger = logging.getLogger(__name__)

# Nome do cookie e duração
_COOKIE_NAME: str = "wolf_session"
_COOKIE_EXPIRY_DAYS: int = 7

# Chave secreta para assinatura do cookie
# Em produção usa SECRET_KEY do env; fallback para derivação do DATABASE_URL
_SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    hashlib.sha256(os.getenv("DATABASE_URL", "wolf-wallet-dev").encode()).hexdigest(),
)


def _get_cookie_manager():
    """Retorna uma instância do CookieManager (singleton por sessão)."""
    try:
        import extra_streamlit_components as stx
        return stx.CookieManager(key="wolf_cookie_mgr")
    except ImportError:
        logger.warning("extra-streamlit-components não instalado — cookies desativados.")
        return None
    except Exception as e:
        logger.warning("Erro ao inicializar CookieManager: %s", e)
        return None


def _sign(payload: str) -> str:
    """Gera HMAC-SHA256 do payload."""
    return hmac.new(_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _make_token(user_id: int) -> str:
    """Cria token assinado: user_id.signature."""
    payload = str(user_id)
    sig = _sign(payload)
    return f"{payload}.{sig}"


def _verify_token(token: str) -> int | None:
    """Verifica token e retorna user_id se válido, None caso contrário."""
    if not token or "." not in token:
        return None
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return None
    payload, sig = parts
    expected = _sign(payload)
    if not hmac.compare_digest(sig, expected):
        logger.warning("Cookie com assinatura inválida detectado.")
        return None
    try:
        return int(payload)
    except ValueError:
        return None


def save_session_cookie(user_id: int) -> None:
    """Grava cookie de sessão no navegador após login bem-sucedido."""
    cm = _get_cookie_manager()
    if cm is None:
        return
    try:
        token = _make_token(user_id)
        expires = datetime.now() + timedelta(days=_COOKIE_EXPIRY_DAYS)
        cm.set(
            _COOKIE_NAME,
            token,
            expires_at=expires,
            key="wolf_set_cookie",
        )
        logger.info("Cookie de sessão gravado para user_id=%s", user_id)
    except Exception as e:
        logger.warning("Não foi possível gravar cookie: %s", e)


def restore_session_from_cookie() -> bool:
    """
    Tenta restaurar sessão a partir do cookie do navegador.

    Returns:
        True se sessão restaurada com sucesso.
    """
    cm = _get_cookie_manager()
    if cm is None:
        return False

    try:
        token = cm.get(_COOKIE_NAME)
    except Exception:
        return False

    if not token:
        return False

    user_id = _verify_token(token)
    if user_id is None:
        return False

    # Busca usuário no banco
    try:
        from models.user import get_user_by_id

        user = get_user_by_id(user_id)
        if not user or not user.get("is_active"):
            clear_session_cookie()
            return False

        # Restaura sessão
        from auth.session import login_user
        login_user(user)
        logger.info("Sessão restaurada via cookie para user_id=%s", user_id)
        return True

    except Exception as e:
        logger.warning("Erro ao restaurar sessão via cookie: %s", e)
        return False


def clear_session_cookie() -> None:
    """Remove o cookie de sessão do navegador (logout)."""
    cm = _get_cookie_manager()
    if cm is None:
        return
    try:
        cm.delete(_COOKIE_NAME, key="wolf_del_cookie")
        logger.info("Cookie de sessão removido.")
    except Exception as e:
        logger.warning("Não foi possível remover cookie: %s", e)
