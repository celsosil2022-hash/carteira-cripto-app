"""Carteira Cripto do Celso - painel pessoal (Streamlit)."""
from __future__ import annotations
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
if not os.environ.get("CARTEIRA_TESTE"):
    for m in [k for k in sys.modules if k.startswith("carteira")]:
        del sys.modules[m]

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from carteira import dados, calc, ai
from carteira.config import cfg, env

st.set_page_config(page_title="Carteira Cripto", page_icon="💼", layout="wide")
NUVEM = os.getcwd().startswith("/mount/src")


def brl(v, casas=2) -> str:
    if v is None or pd.isna(v):
        return "–"
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def pct(v) -> str:
    return "–" if v is None or pd.isna(v) else f"{v:+.1f}%".replace(".", ",")


def preco_fmt(v) -> str:
    if v is None or pd.isna(v):
        return "–"
    return brl(v, 2 if v >= 10 else 4 if v >= 0.01 else 6)


# ---------------- PIN ----------------
def portao():
    pin = env("CARTEIRA_PIN")
    if st.session_state.get("pin_ok"):
        return
    if not pin:
        if NUVEM:
            st.error("Configure o segredo CARTEIRA_PIN nas configurações do app (Settings → Secrets).")
            st.stop()
        return
    st.title("💼 Carteira Cripto")
    v = st.text_input("PIN de acesso", type="password", max_chars=12)
    if v:
        if v.strip() == pin:
            st.session_state["pin_ok"] = True
            st.rerun()
        st.error("PIN incorreto.")
    st.stop()


portao()


# ---------------- Dados (cache) ----------------
@st.cache_data(ttl=300, show_spinner="Buscando cotações...")
def carregar():
    c = cfg()
    mkt = dados.mercado(c["posicoes"])
    return c, mkt, dados.dolar()


@st.cache_data(ttl=3600)
def cdi(desde):
    return dados.cdi_acumulado(desde)


@st.cache_data(ttl=1800, show_spinner="Buscando notícias...")
def news(nome, simbolo):
    return dados.noticias(nome, simbolo, 6)


try:
    c, mkt, usd = carregar()
except Exception as e:
    st.error(f"Não consegui buscar as cotações agora ({e}). Tente de novo em 1 minuto.")
    st.stop()

df = calc.posicoes(c, mkt)
pat, custo = df["valor"].sum(), df["custo"].sum()
hist = dados.historico()
btc_now = mkt.loc["bitcoin", "preco"] if "bitcoin" in mkt.index else None

with st.sidebar:
    st.markdown("### 💼 Carteira Cripto")
    st.caption(f"Cotações ao vivo (CoinGecko), cache de 5 min. Dólar: {brl(usd)}")
    if st.button("Atualizar cotações", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Robô diário às 08:00 grava o histórico; tese por IA toda segunda.")
    if df["estimado"].any():
        st.warning("Custo estimado: " + ", ".join(df.loc[df["estimado"], "simbolo"]) + ". Ajuste no carteira.yaml.")

st.title("💼 Carteira Cripto")

# ---------------- KPIs ----------------
v24, v7, v30 = (calc.variacao_carteira(df, k) for k in ("var_24h", "var_7d", "var_30d"))
k = st.columns(5)
k[0].metric("Patrimônio", brl(pat), pct(v24) + " 24h")
k[1].metric("Investido", brl(custo))
k[2].metric("Resultado", brl(pat - custo), pct((pat / custo - 1) * 100 if custo else None))
k[3].metric("7 dias", pct(v7))
k[4].metric("30 dias", pct(v30))

# Benchmarks desde o início
ini = c.get("data_inicio")
b = st.columns(3)
b[0].metric(f"Carteira desde {pd.to_datetime(ini):%d/%m}", pct((pat / custo - 1) * 100 if custo else None))
btc_ini = None
if not hist.empty and btc_now:
    h0 = hist.sort_values("dia").iloc[0]
    btc_ini = h0["btc_brl"]
b[1].metric("BTC no mesmo período", pct((btc_now / btc_ini - 1) * 100) if btc_ini else "aguardando histórico")
b[2].metric("CDI no período", pct(cdi(ini)))

# ---------------- Alertas ----------------
al = calc.alertas(df, c["alertas"])
if al:
    ic = {"alta": "🟢", "queda": "🔴", "info": "🟡"}
    with st.container(border=True):
        st.markdown("**🔔 Alertas**")
        for a in al:
            st.markdown(f"{ic[a['nivel']]} **{a['simbolo']}**: {a['msg']}")

aba = st.tabs(["Painel", "Moedas", "Notícias", "Histórico", "Tese IA"])

# ---------------- Painel ----------------
with aba[0]:
    c1, c2 = st.columns([1, 1.4])
    with c1:
        fig = px.pie(df, names="simbolo", values="valor", hole=0.55, title="Composição")
        fig.update_traces(textinfo="label+percent")
        fig.update_layout(showlegend=False, height=360, margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig, width="stretch")
    with c2:
        var = df[["simbolo", "var_24h", "var_7d", "var_30d", "pnl_pct"]].set_index("simbolo")
        var.columns = ["24h", "7 dias", "30 dias", "s/ custo"]
        fig = px.imshow(var.astype(float).round(1), text_auto=True, aspect="auto", color_continuous_scale="RdYlGn",
                        color_continuous_midpoint=0, title="Painel de variações (%)")
        fig.update_layout(height=360, margin=dict(t=40, b=0, l=0, r=0), coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
    t = df[["simbolo", "plataforma", "qtd", "preco_medio", "preco", "custo", "valor", "pnl", "pnl_pct", "peso"]].copy()
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "simbolo": "Moeda", "plataforma": "Onde está",
        "qtd": st.column_config.NumberColumn("Quantidade", format="%.4f"),
        "preco_medio": st.column_config.NumberColumn("Preço médio R$", format="%.6f"),
        "preco": st.column_config.NumberColumn("Preço atual R$", format="%.6f"),
        "custo": st.column_config.NumberColumn("Investido R$", format="%.2f"),
        "valor": st.column_config.NumberColumn("Valor R$", format="%.2f"),
        "pnl": st.column_config.NumberColumn("Resultado R$", format="%.2f"),
        "pnl_pct": st.column_config.NumberColumn("Resultado %", format="%.1f%%"),
        "peso": st.column_config.ProgressColumn("Peso", format="%.0f%%", min_value=0, max_value=100)})
    pl = df.groupby("plataforma")["valor"].sum()
    st.caption(("Por plataforma: " + " · ".join(f"{p} {brl(v)} ({v / pat * 100:.0f}%)" for p, v in pl.items())).replace("$", "\\$"))

# ---------------- Moedas ----------------
with aba[1]:
    for r in df.itertuples():
        with st.container(border=True):
            a, b2, c3, d = st.columns([1.3, 1, 1, 1])
            a.markdown(f"**{r.simbolo}** · {r.nome}  \n{r.plataforma}" + (" · custo estimado" if r.estimado else ""))
            b2.metric("Preço", preco_fmt(r.preco), pct(r.var_24h) + " 24h")
            c3.metric("Valor", brl(r.valor), pct(r.pnl_pct))
            d.metric("Distância do topo", pct(r.dist_ath))
            st.caption((f"7d {pct(r.var_7d)} · 30d {pct(r.var_30d)} · 1 ano {pct(r.var_1a)} · "
                       f"rank #{int(r.rank) if pd.notna(r.rank) else '–'} · valor de mercado {brl(r.mcap, 0)} · "
                       f"[CoinGecko](https://www.coingecko.com/pt/moedas/{r.id})").replace("$", "\\$"))

# ---------------- Notícias ----------------
with aba[2]:
    esc = st.selectbox("Moeda", df["simbolo"].tolist())
    r = df[df["simbolo"] == esc].iloc[0]
    itens = news(r["nome"], r["simbolo"])
    if not itens:
        st.info("Nenhuma notícia nos últimos 14 dias.")
    for n in itens:
        dt = f"{n['data']:%d/%m %H:%M}" if n["data"] else ""
        st.markdown(f"[{n['titulo']}]({n['link']})  \n<small>{n['fonte']} · {dt} · {n['idioma']}</small>",
                    unsafe_allow_html=True)

# ---------------- Histórico ----------------
with aba[3]:
    if hist.empty:
        st.info("O histórico começa a ser gravado pelo robô diário (08:00).")
    else:
        h = hist.groupby("dia").agg(valor=("valor", "sum"), custo=("custo", "sum")).reset_index()
        fig = go.Figure()
        fig.add_scatter(x=h["dia"], y=h["valor"], name="Patrimônio", mode="lines+markers")
        fig.add_scatter(x=h["dia"], y=h["custo"], name="Investido", line=dict(dash="dot"))
        fig.update_layout(height=380, yaxis_title="R$", margin=dict(t=20, b=0))
        st.plotly_chart(fig, width="stretch")
        pv = hist.pivot_table(index="dia", columns="simbolo", values="valor", aggfunc="sum")
        st.plotly_chart(px.area(pv, title="Patrimônio por moeda (R$)"), width="stretch")

# ---------------- Tese IA ----------------
with aba[4]:
    teses = ai.carregar()
    if st.button("Gerar tese agora (≈ R\\$ 0,06)"):
        with st.spinner("Claude analisando a carteira..."):
            man = {x.simbolo: [n["titulo"] for n in news(x.nome, x.simbolo)[:4]] for x in df.itertuples()}
            extras = dict(patrimonio=pat, custo=custo, var_7d_carteira=v7, cdi_desde_inicio=cdi(ini), data_inicio=ini)
            try:
                st.session_state["tese_nova"] = ai.gerar_tese(df, extras, man)
            except Exception as e:
                st.error(str(e))
    if st.session_state.get("tese_nova"):
        st.markdown("#### Tese de agora")
        st.markdown(st.session_state["tese_nova"].replace("$", "\\$"))
    for t in teses[:1]:
        st.markdown(f"#### Tese semanal · {t['data']}")
        st.markdown(t["texto"].replace("$", "\\$"))
    if len(teses) > 1:
        with st.expander("Teses anteriores"):
            for t in teses[1:]:
                st.markdown(f"**{t['data']}**")
                st.markdown(t["texto"].replace("$", "\\$"))
    if not teses and not st.session_state.get("tese_nova"):
        st.info("A primeira tese semanal sai na próxima segunda, ou clique no botão acima.")
