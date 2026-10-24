import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="BazinBot | Valuation pelo Método de Bazin", page_icon="📊", layout="centered")

st.title("📊 BazinBot")
st.caption("Valuation educacional de ações brasileiras pelo Método de Bazin")

st.info(
    "Projeto acadêmico para fins educacionais. Os resultados não constituem recomendação de investimento."
)

st.write("Informe o ticker de uma ação brasileira para estimar seu valor intrínseco com base na média histórica de dividendos.")

ticker = st.text_input("Ticker da ação", value="PETR4").strip().upper()
taxa_retorno = st.number_input(
    "Taxa de retorno desejada (%)",
    min_value=1.0,
    max_value=20.0,
    value=6.0,
    step=0.1,
    format="%.2f",
)
anos_dividendos = st.number_input(
    "Anos de histórico para a média dos dividendos",
    min_value=1,
    max_value=10,
    value=5,
    step=1,
)

def brl(valor):
    if valor is None or pd.isna(valor):
        return "N/A"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

if st.button("Calcular", type="primary"):
    if not ticker:
        st.warning("Informe um ticker.")
        st.stop()

    ticker_yf = ticker if ticker.endswith(".SA") else f"{ticker}.SA"

    with st.spinner("Consultando dados e calculando..."):
        try:
            acao = yf.Ticker(ticker_yf)
            historico = acao.history(period="5d", auto_adjust=False)

            if historico.empty or "Close" not in historico.columns:
                st.error("Não foi possível obter o preço do ativo. Confira o ticker informado.")
                st.stop()

            preco_atual = float(historico["Close"].dropna().iloc[-1])

            fim = datetime.today()
            inicio = fim - timedelta(days=int(anos_dividendos) * 365 + 10)
            divs = acao.dividends

            if divs is None or len(divs) == 0:
                st.error("Não foi encontrado histórico de dividendos para o ativo informado.")
                st.stop()

            if isinstance(divs.index, pd.DatetimeIndex) and divs.index.tz is not None:
                divs.index = divs.index.tz_localize(None)

            divs_periodo = divs[(divs.index >= inicio) & (divs.index <= fim)]
            dividendos_anuais = divs_periodo.resample("YE").sum().tail(int(anos_dividendos))

            if dividendos_anuais.empty:
                st.error("Não há dados suficientes no período selecionado.")
                st.stop()

            media_dividendo = float(dividendos_anuais.mean())
            valor_intrinseco = media_dividendo / (taxa_retorno / 100)
            dividend_yield = (media_dividendo / preco_atual) * 100 if preco_atual else None
            margem = ((valor_intrinseco / preco_atual) - 1) * 100 if preco_atual else None

            status = (
                "Preço abaixo do valor estimado"
                if preco_atual < valor_intrinseco
                else "Preço acima do valor estimado"
            )

            st.subheader("Resultado")
            c1, c2 = st.columns(2)
            c1.metric("Preço atual", brl(preco_atual))
            c2.metric("Valor intrínseco estimado", brl(valor_intrinseco))

            c3, c4 = st.columns(2)
            c3.metric("Média anual de dividendos", brl(media_dividendo))
            c4.metric(
                "Dividend Yield estimado",
                f"{dividend_yield:.2f}%" if dividend_yield is not None else "N/A",
            )

            st.write(f"**Status:** {status}")
            if margem is not None:
                st.write(f"**Diferença entre valor estimado e preço atual:** {margem:.2f}%")

            st.markdown("### Como o cálculo é feito")
            st.write(
                f"O Método de Bazin, nesta implementação acadêmica, divide a média anual de dividendos "
                f"({brl(media_dividendo)}) pela taxa de retorno desejada ({taxa_retorno:.2f}%). "
                "O resultado é uma estimativa simplificada e deve ser analisado junto com outros fundamentos."
            )

            with st.expander("Dividendos anuais utilizados"):
                tabela = dividendos_anuais.rename("Dividendos (R$)").to_frame()
                tabela.index = tabela.index.year
                tabela.index.name = "Ano"
                st.dataframe(tabela, use_container_width=True)

        except Exception as e:
            st.error(f"Não foi possível concluir a consulta: {e}")

st.divider()
st.caption("Projeto acadêmico desenvolvido por Álvaro Bonifácio • Dados via Yahoo Finance / yfinance")
