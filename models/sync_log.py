"""
🐺 Wolf Wallet — Sync Log Model (CRUD)

Operações de banco de dados para a tabela `sync_log`.
Registra cada execução do job de sincronização com o Mercado Pago.

Usage:
    from models.sync_log import create_log, get_last_log, get_all_logs
"""

from __future__ import annotations

import logging
from datetime import datetime

from config.database import execute_insert, execute_query

logger = logging.getLogger(__name__)


def create_log(
    records_added: int,
    status: str,
    error_message: str | None = None,
    begin_date: datetime | None = None,
    end_date: datetime | None = None,
) -> int | None:
    """
    Registra uma execução de sincronização no log.

    Args:
        records_added: Quantidade de transações novas inseridas.
        status: 'success' ou 'error'.
        error_message: Mensagem de erro (se status='error').
        begin_date: Início do período sincronizado.
        end_date: Fim do período sincronizado.

    Returns:
        ID do registro criado.
    """
    if status not in ("success", "error"):
        raise ValueError(f"Status inválido: {status}. Use 'success' ou 'error'.")

    log_id = execute_insert(
        "INSERT INTO sync_log (records_added, status, error_message, begin_date, end_date) "
        "VALUES (:records_added, :status, :error_message, :begin_date, :end_date) "
        "RETURNING id",
        {
            "records_added": records_added,
            "status": status,
            "error_message": error_message,
            "begin_date": begin_date,
            "end_date": end_date,
        },
    )

    logger.info(
        f"Sync log criado: id={log_id}, status={status}, "
        f"records={records_added}, period={begin_date} → {end_date}"
    )
    return log_id


def get_last_log() -> dict | None:
    """
    Retorna o log da última sincronização.

    Returns:
        Dict com dados do log, ou None se nunca sincronizou.
    """
    rows = execute_query(
        "SELECT id, sync_date, records_added, status, error_message, begin_date, end_date "
        "FROM sync_log "
        "ORDER BY sync_date DESC "
        "LIMIT 1"
    )
    return rows[0] if rows else None


def get_last_successful_log() -> dict | None:
    """
    Retorna o log da última sincronização bem-sucedida.

    Returns:
        Dict com dados do log, ou None se nunca sincronizou com sucesso.
    """
    rows = execute_query(
        "SELECT id, sync_date, records_added, status, error_message, begin_date, end_date "
        "FROM sync_log "
        "WHERE status = 'success' "
        "ORDER BY sync_date DESC "
        "LIMIT 1"
    )
    return rows[0] if rows else None


def get_all_logs(limit: int = 50) -> list[dict]:
    """
    Retorna o histórico de sincronizações.

    Args:
        limit: Quantidade máxima de registros.

    Returns:
        Lista de logs ordenados do mais recente ao mais antigo.
    """
    return execute_query(
        "SELECT id, sync_date, records_added, status, error_message, begin_date, end_date "
        "FROM sync_log "
        "ORDER BY sync_date DESC "
        "LIMIT :limit",
        {"limit": limit},
    )


def get_sync_stats() -> dict:
    """
    Retorna estatísticas gerais de sincronização.

    Returns:
        Dict com: total_syncs, successful, failed, total_records, last_sync_date.
    """
    rows = execute_query(
        "SELECT "
        "  COUNT(*) as total_syncs, "
        "  SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful, "
        "  SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed, "
        "  COALESCE(SUM(records_added), 0) as total_records, "
        "  MAX(sync_date) as last_sync_date "
        "FROM sync_log"
    )

    if rows and rows[0]:
        return rows[0]

    return {
        "total_syncs": 0,
        "successful": 0,
        "failed": 0,
        "total_records": 0,
        "last_sync_date": None,
    }
