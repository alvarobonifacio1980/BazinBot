import streamlit as st
import yfinance as yf
import openai
import os
import pandas as pd
import PyPDF2
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="BazinBot – Valuation Automatizado", layout="centered")
st.title("BazinBot")
st.write("Assessor de Valuation de Ações pelo método Bazin + IA")
st.caption("Protótipo para XP Educação")

ticker = st.text_input("Digite o ticker da ação (ex: PETR4)", max_chars=10)

if st.button("Calcular Valuation"):
    st.info("Buscando dados do Yahoo Finance...")
    try:
        acao = yf.Ticker(ticker + '.SA')
        info = acao.info
        preco_atual = info.get("regularMarketPrice", None)
        dy = info.get("dividendYield", None)
        if dy: dy = round(dy * 100, 2)
        nome_empresa = info.get("shortName", "-")
        if dy:
            preco_teto_bazin = round((preco_atual / (dy / 100)) * 0.06, 2)
            status = "Subvalorizado" if preco_atual < preco_teto_bazin else "Supervalorizado"
        else:
            preco_teto_bazin = "N/A"
            status = "Dados insuficientes"
        st.subheader(f"{nome_empresa} ({ticker.upper()})")
        st.metric("Preço Atual", f"R$ {preco_atual}")
        st.metric("Dividend Yield (%)", dy or "N/A")
        st.metric("Preço Teto Bazin", f"R$ {preco_teto_bazin}")
        st.success(f"Status: {status}")

        # IA – explicação do resultado
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            prompt = f"Explique de forma simples, para um investidor moderado, por que a ação {ticker.upper()} está considerada '{status}' pelo método Bazin, considerando os dados: preço atual R$ {preco_atual}, DY {dy}%, preço teto R$ {preco_teto_bazin}."
            with st.spinner("Gerando explicação com IA..."):
                resposta = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.write("**Explicação do especialista:**")
                st.info(resposta["choices"][0]["message"]["content"])
        else:
            st.warning("API do ChatGPT não configurada. Adicione sua chave ao arquivo .env.")

    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")

# CONSULTA A DOCUMENTOS INTERNOS
st.markdown("---")
st.subheader("Consultar Documentos Internos da Empresa")
docs_path = "docs"
if not os.path.exists(docs_path):
    os.makedirs(docs_path)
arquivos = [f for f in os.listdir(docs_path) if f.endswith(('.pdf', '.xls', '.xlsx'))]
arquivo_escolhido = st.selectbox("Escolha um documento para buscar informações:", [""] + arquivos)
busca_termo = st.text_input("Buscar termo no documento (ex: PETR4, dividendos, etc)")

if st.button("Buscar no documento") and arquivo_escolhido:
    file_path = os.path.join(docs_path, arquivo_escolhido)
    resultado = ""
    if arquivo_escolhido.endswith('.pdf'):
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            for page in pdf.pages:
                texto = page.extract_text()
                if texto and busca_termo.lower() in texto.lower():
                    resultado += texto + "\n\n"
        st.write(f"Resultados para **{busca_termo}** em **{arquivo_escolhido}**:")
        st.code(resultado if resultado else "Nenhum resultado encontrado.")
    elif arquivo_escolhido.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_path)
        mask = df.apply(lambda row: row.astype(str).str.contains(busca_termo, case=False).any(), axis=1)
        st.write(df[mask])
    else:
        st.warning("Formato de arquivo não suportado.")

# CHATBOT INTERATIVO (PERGUNTAS LIVRES)
st.markdown("---")
st.subheader("Pergunte ao BazinBot")
pergunta = st.text_input("Sua pergunta:", key="pergunta_bot")
if st.button("Enviar pergunta"):
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        contexto = f"Dados recentes de {ticker.upper()}: preço atual R$ {preco_atual}, DY {dy}%, preço teto Bazin R$ {preco_teto_bazin}. "
        if 'resultado' in locals() and resultado:
            contexto += f"Trecho relevante do documento '{arquivo_escolhido}': {resultado[:1000]}"
        prompt = f"Contexto: {contexto}\nPergunta: {pergunta}\nResponda de forma clara e fundamentada para um investidor de perfil moderado."
        with st.spinner("Aguarde, consultando o especialista..."):
            resposta = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            st.info(resposta["choices"][0]["message"]["content"])
    else:
        st.warning("API do ChatGPT não configurada. Adicione sua chave ao arquivo .env.")
