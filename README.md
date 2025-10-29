# Planner Automático — A Amiga Digital (Streamlit + Gemini + Trello)

App web em **Streamlit** que gera um **calendário mensal de conteúdos** para a **A Amiga Digital** usando **Google Gemini** e cria **cartões no Trello** automaticamente.

## ✅ O que precisas
- Conta GitHub (grátis)
- Conta Streamlit Cloud (grátis)
- **GEMINI_API_KEY**: criar em https://aistudio.google.com/app/apikey
- **TRELLO_KEY** e **TRELLO_TOKEN**: em https://trello.com/app-key

## 🚀 Deploy (passo a passo)
1. Cria um repositório público chamado `planner-aamigadigital` e faz upload destes ficheiros.
2. Vai a https://share.streamlit.io → **New app** → escolhe o repositório e `app.py`.
3. Depois do deploy, abre **Manage app → Settings → Secrets** e cola:
```
GEMINI_API_KEY = "a_tua_gemini_key"
TRELLO_KEY = "a_tua_trello_key"
TRELLO_TOKEN = "o_teu_trello_token"
```
4. Recarrega a app. Introduz **Mês**, **Frequência** e **Dias** → clica **Gerar calendário**.
5. Se quiseres cartões no Trello: seleciona o **Board** e **Lista** → clica **Criar cartões**.

## 🧩 Notas
- O Gemini devolve JSON; a app mostra como tabela e permite **download CSV**.
- A criação de cartões usa a API do Trello via `trello_helpers.py`.
- Mantém o tom da **A Amiga Digital** e evita a palavra “dicas”.

## 🛠️ Troubleshooting
- **Erro Gemini**: garante que `GEMINI_API_KEY` está nos *Secrets*. 
- **Erro Trello**: verifica `TRELLO_KEY` e `TRELLO_TOKEN` e que tens acesso ao board selecionado.
- Logs: vê **Manage app → Logs** na Streamlit Cloud.
