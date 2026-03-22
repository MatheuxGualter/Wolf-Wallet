"""
🐺 Wolf Wallet — Email Service (Gmail SMTP)

Envio de emails via Gmail SMTP com App Password.
Funções:
    - send_welcome_email: boas-vindas com senha temporária
    - send_password_reset_email: nova senha temporária

Configuração necessária em .streamlit/secrets.toml:
    GMAIL_USER = "wolfwallet.projeto@gmail.com"
    GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"

Usage:
    from services.email_service import send_welcome_email, send_password_reset_email
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st

from config.settings import App

logger = logging.getLogger(__name__)

# =============================================
# Configuração SMTP
# =============================================
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _get_credentials() -> tuple[str, str] | None:
    """
    Lê credenciais Gmail do st.secrets.

    Returns:
        Tupla (user, app_password), ou None se não configurado.
    """
    try:
        user = st.secrets.get("GMAIL_USER", "")
        password = st.secrets.get("GMAIL_APP_PASSWORD", "")
        if user and password:
            return user, password
    except Exception:
        pass

    logger.warning("Credenciais Gmail não configuradas em st.secrets.")
    return None


def _send_email(to: str, subject: str, html_body: str) -> bool:
    """
    Envia um email HTML via Gmail SMTP.

    Args:
        to: Email do destinatário.
        subject: Assunto.
        html_body: Corpo em HTML.

    Returns:
        True se enviou com sucesso, False caso contrário.
    """
    credentials = _get_credentials()
    if not credentials:
        logger.warning(f"Email não enviado para {to} — credenciais não configuradas.")
        return False

    gmail_user, gmail_password = credentials

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{App.TITLE} <{gmail_user}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to, msg.as_string())

        logger.info(f"Email enviado para {to}: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Falha de autenticação Gmail. Verifique GMAIL_USER e GMAIL_APP_PASSWORD.")
        return False
    except Exception as e:
        logger.error(f"Erro ao enviar email para {to}: {e}")
        return False


# =============================================
# Templates de email
# =============================================

def _base_template(content: str) -> str:
    """Wrapper HTML com estilo base."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 2rem;">
        <div style="max-width: 500px; margin: 0 auto; background: #16213e; border-radius: 12px; padding: 2rem; border: 1px solid #0f3460;">
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <h1 style="color: #e94560; margin: 0;">🐺 {App.TITLE}</h1>
                <p style="color: #888; font-size: 0.9rem;">{App.DESCRIPTION}</p>
            </div>
            {content}
            <hr style="border-color: #0f3460; margin: 1.5rem 0;">
            <p style="color: #666; font-size: 0.75rem; text-align: center;">
                Este é um email automático do {App.TITLE}. Não responda.
            </p>
        </div>
    </body>
    </html>
    """


def send_welcome_email(name: str, email: str, temp_password: str) -> bool:
    """
    Envia email de boas-vindas com senha temporária.

    Args:
        name: Nome do usuário.
        email: Email do destinatário.
        temp_password: Senha temporária gerada.

    Returns:
        True se enviou com sucesso.
    """
    content = f"""
    <h2 style="color: #e0e0e0;">Bem-vindo(a), {name}! 👋</h2>
    <p>Sua conta no <strong>{App.TITLE}</strong> foi criada por um administrador.</p>
    <p>Use as credenciais abaixo para acessar:</p>
    <div style="background: #1a1a2e; border-radius: 8px; padding: 1rem; margin: 1rem 0; border-left: 4px solid #e94560;">
        <p style="margin: 0.3rem 0;"><strong>Email:</strong> {email}</p>
        <p style="margin: 0.3rem 0;"><strong>Senha temporária:</strong>
            <code style="background: #0f3460; padding: 2px 8px; border-radius: 4px; color: #4ecca3; font-size: 1.1rem;">{temp_password}</code>
        </p>
    </div>
    <p>⚠️ <strong>Troque sua senha no primeiro acesso</strong> para garantir a segurança da sua conta.</p>
    """

    return _send_email(
        to=email,
        subject=f"🐺 {App.TITLE} — Bem-vindo(a)!",
        html_body=_base_template(content),
    )


def send_password_reset_email(name: str, email: str, temp_password: str) -> bool:
    """
    Envia email com nova senha temporária (reset por admin).

    Args:
        name: Nome do usuário.
        email: Email do destinatário.
        temp_password: Nova senha temporária.

    Returns:
        True se enviou com sucesso.
    """
    content = f"""
    <h2 style="color: #e0e0e0;">Redefinição de Senha 🔑</h2>
    <p>Olá, <strong>{name}</strong>!</p>
    <p>Um administrador redefiniu sua senha no <strong>{App.TITLE}</strong>.</p>
    <div style="background: #1a1a2e; border-radius: 8px; padding: 1rem; margin: 1rem 0; border-left: 4px solid #4ecca3;">
        <p style="margin: 0.3rem 0;"><strong>Nova senha temporária:</strong>
            <code style="background: #0f3460; padding: 2px 8px; border-radius: 4px; color: #4ecca3; font-size: 1.1rem;">{temp_password}</code>
        </p>
    </div>
    <p>⚠️ <strong>Troque sua senha no próximo acesso.</strong></p>
    <p style="color: #888;">Se você não solicitou essa alteração, entre em contato com um administrador.</p>
    """

    return _send_email(
        to=email,
        subject=f"🐺 {App.TITLE} — Sua senha foi redefinida",
        html_body=_base_template(content),
    )


def is_email_configured() -> bool:
    """Verifica se as credenciais Gmail estão configuradas."""
    return _get_credentials() is not None
