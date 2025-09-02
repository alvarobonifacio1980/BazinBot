import streamlit as st
import yfinance as yf
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re

# ---------- CARREGAR CHAVE API (opcional, pode remover se não usar mais IA) ----------
load_dotenv()

st.set_page_config(page_title="Valuation pelo Método de Bazin", layout="centered")
st.title("Valuation pelo Método de Bazin")

st.write("Insira o ticker da ação para calcular o valuation.")

# -------- Inputs conforme layout --------
ticker = st.text_input("Digite o ticker da ação (ex: PETR4):", value="PETR4").upper()
taxa_retorno = st.number_input("Taxa de retorno desejada (%)", min_value=1.0, max_value=20.0, value=6.00, step=0.1, format="%.2f")
anos_dividendos = st.number_input("Anos de histórico para média dos dividendos", min_value=1, max_value=10, value=5, step=1)

if st.button("Calcular"):
    with st.spinner("Calculando..."):
        try:
            acao = yf.Ticker(ticker + ".SA")
            info = acao.info
            preco_atual = info.get("regularMarketPrice", None)
            nome_empresa = info.get("shortName", "-")
            
            # Média de dividendos dos últimos N anos
            fim = datetime.today()
            inicio = fim - timedelta(days=anos_dividendos * 365)
            divs = acao.dividends

            # Trata erro de índice ao pesquisar ticker inexistente ou sem dividendos
            if not isinstance(divs.index, pd.DatetimeIndex):
                st.error("Ticker não encontrado ou não possui histórico de dividendos.")
                st.stop()

            divs.index = divs.index.tz_localize(None)  # Remove timezone
            divs_periodo = divs[(divs.index >= inicio) & (divs.index <= fim)]
            total_dividendo = divs_periodo.resample('YE').sum()
            if len(total_dividendo) > 0:
                media_dividendo = total_dividendo[-anos_dividendos:].mean()
                media_dividendo_str = f"{media_dividendo:.2f}"
            else:
                media_dividendo = 0
                media_dividendo_str = "N/A"

            # Valor Intrínseco (Bazin)
            valor_intrinseco = (media_dividendo / (taxa_retorno/100)) if media_dividendo else None
            valor_intrinseco_str = f"{valor_intrinseco:.2f}" if valor_intrinseco else "N/A"

            # Dividend Yield
            if preco_atual and media_dividendo:
                dividend_yield = (media_dividendo / preco_atual) * 100
                dividend_yield_str = f"{dividend_yield:.2f}"
            else:
                dividend_yield = None
                dividend_yield_str = "N/A"

            # Status
            if valor_intrinseco and preco_atual:
                status = "Subvalorizada" if preco_atual < valor_intrinseco else "Supervalorizada"
            else:
                status = "Dados insuficientes"

            # EXIBE O RESULTADO
            st.success("Resultado do Valuation:")
            st.markdown(f"""
**Ticker:** {ticker}.SA  
**Média de Dividendos Anuais (BRL):** {media_dividendo_str}  
**Valor Intrínseco (BRL):** {valor_intrinseco_str}  
**Preço Atual (BRL):** {preco_atual if preco_atual else 'N/A'}  
**Dividend Yield (%):** {dividend_yield_str}  
**Status:** {status}
""")

            # ---------- EXPLICAÇÃO PADRONIZADA ----------
            if status == "Subvalorizada":
                explicacao_padrao = (
                    f"Para um investidor moderado, isso significa que o preço atual da ação {ticker.upper()} está significativamente abaixo do seu valor intrínseco calculado pelo método Bazin. "
                    "Isso sugere que a ação pode estar subvalorizada no mercado, o que pode representar uma oportunidade de compra com potencial de valorização no longo prazo. "
                    "Vale ressaltar que esta análise é baseada em dados históricos e projeções futuras, então é importante sempre considerar outros fatores antes de realizar um investimento."
                )
            elif status == "Supervalorizada":
                explicacao_padrao = (
                    f"Para um investidor moderado, isso significa que o preço atual da ação {ticker.upper()} está acima do seu valor intrínseco calculado pelo método Bazin. "
                    "Isso sugere que a ação pode estar supervalorizada no mercado, o que pode indicar menor potencial de valorização no longo prazo ou a necessidade de cautela antes de investir. "
                    "Lembre-se de considerar outros fatores fundamentais e de mercado antes de tomar uma decisão de investimento."
                )
            else:
                explicacao_padrao = (
                    "Não foi possível calcular a explicação pois os dados da ação ou dos dividendos estão incompletos. "
                    "Tente ajustar o período ou conferir o ticker informado."
                )

            st.markdown("**Explicação do especialista:**")
            st.markdown(explicacao_padrao)

            # ---------- FÓRMULA EXPLICADA EM PARÁGRAFO NORMAL ----------
            if valor_intrinseco and media_dividendo and taxa_retorno:
                formula_paragrafo = (
                    f"<p style='margin-top: 24px'><b>Cálculo do valor intrínseco:</b> "
                    f"O valor intrínseco pelo método Bazin é calculado dividindo a média dos dividendos anuais "
                    f"({media_dividendo_str}) pela taxa de retorno desejada ({taxa_retorno:.2f}% ou {taxa_retorno/100:.2f}). "
                    f"Neste caso: <b>Valor Intrínseco = {media_dividendo_str} / {taxa_retorno/100:.2f} = {valor_intrinseco_str}</b>.</p>"
                )
                st.markdown(formula_paragrafo, unsafe_allow_html=True)
            else:
                st.markdown(
                    "<p style='margin-top: 24px'><b>Cálculo do valor intrínseco:</b> Não foi possível exibir a fórmula devido a dados insuficientes.</p>",
                    unsafe_allow_html=True,
                )

        except Exception as e:
            st.error(f"Erro ao buscar/calcular dados: {e}")