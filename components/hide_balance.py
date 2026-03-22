"""
🐺 Wolf Wallet — Hide Balance Component

Componente para ocultar/mostrar valores financeiros.
Estado gerenciado globalmente via session_state.

Usage:
    from components.hide_balance import mask_value, render_hide_toggle
"""

from __future__ import annotations

from auth.session import is_balance_hidden
from config.settings import Finance


def mask_value(value: str, force_hidden: bool | None = None) -> str:
    """
    Retorna o valor mascarado ou real baseado no estado global.

    Args:
        value: Valor formatado (ex: "R$ 1.234,56").
        force_hidden: Se fornecido, sobrescreve o estado global.

    Returns:
        Valor original ou "R$ ••••••".
    """
    hidden = force_hidden if force_hidden is not None else is_balance_hidden()
    return Finance.HIDDEN_VALUE if hidden else value
