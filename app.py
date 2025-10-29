import os
import json
import requests
import streamlit as st
import pandas as pd
import yaml
from datetime import date
from prompts import planning_prompt
from trello_helpers import TrelloClient

st.set_page_config(page_title="Planner — A Amiga Digital", layout="wide")

st.title("🧠 Planner Automático de Conteúdo — A Amiga Digital")
st.caption("Gera um calendário mensal com Gemini e cria cartões no Trello.")

# Carregar presets
with open("presets.yaml", "r", encoding="utf-8") as f:
    presets = yaml.safe_load(f)

# Sidebar: Configuração
st.sidebar.header("Configuração")
mes_input = st.sidebar.text_input("Mês (ex.: Novembro 2025)", "Novembro 2025")
freq = st.sidebar.slider("Publicações por semana", 1, 7, 3)
dias = st.sidebar.text_input("Dias de publicação", "segunda, quarta e sexta")
pilares = st.sidebar.multiselect("Pilares ativos", presets["pilares"], default=presets["pilares"])

# Gems
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TRELLO_KEY = os.environ.get("TRELLO_KEY", "")
TRELLO_TOKEN = os.environ.get("TRELLO_TOKEN", "")

col_a, col_b = st.columns([1,1])

def call_gemini(mes: str, freq_semana: int, dias_txt: str, pilares_list: list) -> pd.DataFrame:
    if not GEMINI_API_KEY:
        st.error("GEMINI_API_KEY não definido nos Secrets da Streamlit.")
        return pd.DataFrame()

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }
    user_text = (
        f"Marca: A Amiga Digital\n"
        f"Mês: {mes}\n"
        f"Frequência: {freq_semana} posts por semana ({dias_txt})\n"
        f"Público-alvo: {presets['publico']}\n"
        f"Objetivo: {presets['objetivo']}\n\n"
        f"Pilares de conteúdo:\n- " + "\n- ".join(pilares_list) + "\n\n"
        "Formato preferido: carrossel, reel ou publicação de imagem, conforme o tema\n\n"
        "Devolve o resultado APENAS em JSON válido (sem comentários), com esta estrutura:\n"
        "[{\"data\":\"YYYY-MM-DD\",\"pilar\":\"\",\"titulo\":\"\","
        "\"formato\":\"Carrossel / Reel / Foto\",\"gancho\":\"\",\"legenda\":\"\","
        "\"cta\":\"\",\"hashtags\":[\"#aamigadigital\",\"#marketingdigital\","
        "\"#gestaoderedessociais\",\"#portugal\"]}]\n\n"
        "Regras:\n- As datas devem pertencer ao mês indicado e distribuir-se pelos dias fornecidos."
        "\n- Cada legenda até 800 caracteres.\n- Hashtags em minúsculas e relevantes."
        "\n- Mantém coerência de voz e evita tom comercial.\n- Se possível, inclui humor subtil."
    )
    body = {
        "system_instruction": {"parts": [{"text": planning_prompt()}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    resp = requests.post(url, headers=headers, json=body, timeout=90)
    try:
        payload = resp.json()
    except Exception as e:
        st.error(f"Resposta inválida do Gemini: {e}")
        return pd.DataFrame()

    # Extrair texto JSON
    try:
        text_json = payload["candidates"][0]["content"]["parts"][0]["text"]
        df = pd.read_json(text_json)
    except Exception as e:
        st.error(f"Erro a interpretar o JSON devolvido: {e}\nResposta bruta: {payload}")
        return pd.DataFrame()
    # Acrescentar hashtags base, se necessário
    if "hashtags" in df.columns:
        base_tags = presets.get("hashtags_base", [])
        def merge_tags(tags):
            unique = []
            for t in (tags or []):
                if t not in unique:
                    unique.append(t)
            for t in base_tags:
                if t not in unique:
                    unique.append(t)
            return " ".join(unique)
        df["hashtags"] = df["hashtags"].apply(merge_tags)
    return df

with col_a:
    if st.button("🚀 Gerar calendário"):
        df = call_gemini(mes_input, freq, dias, pilares)
        if not df.empty:
            st.session_state["calendar_df"] = df
            st.success("Calendário gerado com sucesso!")
        else:
            st.stop()

# Mostrar calendário e export
if "calendar_df" in st.session_state:
    df = st.session_state["calendar_df"]
    st.subheader("Calendário gerado")
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descarregar CSV", csv, file_name="calendario_aamigadigital.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("📌 Criar cartões no Trello")

    if not TRELLO_KEY or not TRELLO_TOKEN:
        st.info("Define TRELLO_KEY e TRELLO_TOKEN em **Manage app → Settings → Secrets** para ativar esta secção.")
    else:
        try:
            trello = TrelloClient(TRELLO_KEY, TRELLO_TOKEN)
            boards = trello.get_boards()
            if not boards:
                st.warning("Não encontrei boards no Trello para este utilizador/token.")
            else:
                boards_map = {b["name"]: b["id"] for b in boards}
                board_name = st.selectbox("Board", list(boards_map.keys()))
                lists = trello.get_lists(boards_map[board_name])
                lists_map = {l["name"]: l["id"] for l in lists}
                list_name = st.selectbox("Lista", list(lists_map.keys()))
                prefix = st.text_input("Prefixo do nome do cartão", "A Amiga Digital")

                if st.button("🧷 Criar cartões agora"):
                    created = []
                    for _, row in df.iterrows():
                        titulo = str(row.get("titulo", ""))[:60]
                        name = f"{row.get('data','')} · {prefix} · {titulo}"
                        desc_parts = [
                            f"**Pilar:** {row.get('pilar','')}",
                            f"**Formato:** {row.get('formato','')}",
                            f"**Gancho:** {row.get('gancho','')}",
                            "\n**Legenda**\n" + (row.get("legenda","") or ""),
                            "\n**CTA**\n" + (row.get("cta","") or ""),
                            "\n**Hashtags**\n" + (row.get("hashtags","") or ""),
                        ]
                        desc = "\n".join(desc_parts)
                        due = row.get("data", None)
                        labels = [row.get("pilar",""), row.get("formato","")]
                        try:
                            card = trello.create_card(lists_map[list_name], name, desc, due=due, labels=[l for l in labels if l])
                            created.append(card.get("shortUrl", card.get("url", "")))
                        except Exception as e:
                            st.warning(f"Falhou criar cartão para {row.get('data','sem data')}: {e}")
                    if created:
                        st.success(f"Criados {len(created)} cartões.")
                        for u in created:
                            if u:
                                st.write(f"• {u}")
        except Exception as e:
            st.error(f"Erro Trello: {e}")
