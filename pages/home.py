"""
🐺 Wolf Wallet — Dashboard Page

Página principal com:
    - 4 cards de métricas (saldo, entradas, saídas, rendimentos)
    - Gráfico de barras (entradas vs saídas por mês)
    - Feed de atividades recentes
    - Alertas de contas próximas do vencimento

Usage:
    from pages.home import render_home
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from auth.session import is_balance_hidden, is_visitor, render_visitor_banner, require_auth
from components.cards import render_dashboard_cards
from components.charts import bar_chart_inflows_outflows
from config.settings import App, Colors, UI
from services.report_service import build_activity_feed, build_bill_alerts, format_currency


def render_home() -> None:
    """Renderiza o dashboard completo."""
    if not require_auth():
        return

    render_visitor_banner()

    st.title(f"{App.EMOJI} Dashboard")

    # Obtém dados (mock ou reais)
    data = _load_data()
    hidden = is_balance_hidden()

    # --- Cards ---
    render_dashboard_cards(data, hidden=hidden)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Gráfico + Feed ---
    col_chart, col_feed = st.columns([3, 2])

    with col_chart:
        _render_chart(data)

    with col_feed:
        _render_activity_feed(data, hidden)
        _render_bill_alerts(data, hidden)


def _load_data() -> dict:
    """
    Carrega dados do dashboard.

    Se visitante: usa mock_data.
    Se logado: tenta carregar do banco, fallback para vazio.
    """
    if is_visitor():
        from mock.mock_data import get_mock_dashboard_data
        return get_mock_dashboard_data()

    # Tenta carregar do banco
    try:
        from models.transaction import (
            get_balance,
            get_monthly_inflows,
            get_monthly_outflows,
            get_monthly_yields,
            get_monthly_chart_data,
            get_recent_transactions,
        )
        from models.bill import get_upcoming_bills

        today = date.today()

        balance = get_balance()
        inflows = get_monthly_inflows(today.year, today.month)
        outflows = get_monthly_outflows(today.year, today.month)
        yields = get_monthly_yields(today.year, today.month)
        chart_data = get_monthly_chart_data(months=6)
        transactions = get_recent_transactions(limit=UI.RECENT_ACTIVITIES_LIMIT)
        upcoming_bills = get_upcoming_bills()

        return {
            "balance": float(balance),
            "inflows": float(inflows),
            "outflows": float(outflows),
            "yields": float(yields),
            "chart_data": chart_data,
            "transactions": transactions,
            "upcoming_bills": upcoming_bills,
        }

    except Exception as e:
        st.warning(
            f"⚠️ Não foi possível carregar dados do banco. "
            f"Mostrando dashboard vazio. ({e})"
        )
        import pandas as pd
        return {
            "balance": 0,
            "inflows": 0,
            "outflows": 0,
            "yields": 0,
            "chart_data": pd.DataFrame(columns=["month", "inflows", "outflows"]),
            "transactions": [],
            "upcoming_bills": [],
        }


def _render_chart(data: dict) -> None:
    """Renderiza o gráfico de entradas vs saídas."""
    st.markdown("##### 📊 Entradas vs Saídas")

    # Seletor de período
    period_options = list(UI.CHART_PERIODS.keys())
    selected_period = st.selectbox(
        "Período",
        options=period_options,
        index=1,  # 6 meses padrão
        key="chart_period",
        label_visibility="collapsed",
    )

    chart_data = data.get("chart_data")
    if chart_data is not None and not chart_data.empty:
        months_to_show = UI.CHART_PERIODS.get(selected_period, 6)
        display_data = chart_data.tail(months_to_show)
        fig = bar_chart_inflows_outflows(display_data)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados de transações para exibir o gráfico.")


def _render_activity_feed(data: dict, hidden: bool) -> None:
    """Renderiza o feed de atividades recentes."""
    st.markdown("##### ⚡ Atividades Recentes")

    transactions = data.get("transactions", [])

    if not transactions:
        st.caption("Nenhuma atividade recente.")
        return

    feed = build_activity_feed(transactions)

    for item in feed[:UI.RECENT_ACTIVITIES_LIMIT]:
        amount_display = item["amount_str"]
        if hidden:
            amount_display = "R$ ••••••"

        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.4rem 0.6rem;
                margin: 0.2rem 0;
                border-radius: 8px;
                background: rgba(255,255,255,0.03);
                font-size: 0.88rem;
            ">
                <span>{item['icon']} <span style="color: #888;">{item['date_str']}</span> — {item['description']}</span>
                <span style="color: {item['color']}; font-weight: 600;">{amount_display}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_bill_alerts(data: dict, hidden: bool) -> None:
    """Renderiza alertas de contas próximas do vencimento."""
    upcoming = data.get("upcoming_bills", [])

    if not upcoming:
        return

    alerts = build_bill_alerts(upcoming)

    if not alerts:
        return

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### ⚠️ Próximos Vencimentos")

    for alert in alerts:
        amount_display = alert["amount_str"]
        if hidden:
            amount_display = "R$ ••••••"

        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 0.7rem;
                margin: 0.2rem 0;
                border-radius: 8px;
                background: rgba(255, 145, 0, 0.08);
                border-left: 3px solid {Colors.ALERT};
                font-size: 0.88rem;
            ">
                <span>{alert['icon']} {alert['description']}</span>
                <span style="color: {Colors.ALERT}; font-weight: 600;">{amount_display}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
