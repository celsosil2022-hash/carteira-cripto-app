"""Robô: python -m carteira snapshot | tese"""
from __future__ import annotations
import sys
from datetime import date
import pandas as pd
from . import dados, calc, ai
from .config import cfg, HIST


def snapshot() -> pd.DataFrame:
    c = cfg()
    mkt = dados.mercado(c["posicoes"])
    df = calc.posicoes(c, mkt)
    btc = mkt.loc["bitcoin", "preco"] if "bitcoin" in mkt.index else None
    hoje = date.today().isoformat()
    novo = df[["simbolo", "qtd", "preco", "valor", "custo"]].assign(dia=hoje, btc_brl=btc, dolar=dados.dolar())
    h = dados.historico()
    if not h.empty:
        h = h[h["dia"].astype(str).str[:10] != hoje]
    out = pd.concat([h, novo[["dia", "simbolo", "qtd", "preco", "valor", "custo", "btc_brl", "dolar"]]])
    from .cofre import gravar
    gravar(HIST, out.to_csv(index=False))
    print(f"{hoje}: histórico gravado (cifrado).")
    return df


def tese() -> None:
    c = cfg()
    df = calc.posicoes(c, dados.mercado(c["posicoes"]))
    man = {r.simbolo: [n["titulo"] for n in dados.noticias(r.nome, r.simbolo, 4)] for r in df.itertuples()}
    extras = dict(patrimonio=df["valor"].sum(), custo=df["custo"].sum(),
                  var_7d_carteira=calc.variacao_carteira(df, "var_7d"),
                  cdi_desde_inicio=dados.cdi_acumulado(c["data_inicio"]), data_inicio=c["data_inicio"])
    ai.salvar(ai.gerar_tese(df, extras, man))
    print("Tese gerada.")


if __name__ == "__main__":
    {"snapshot": snapshot, "tese": tese}[sys.argv[1] if len(sys.argv) > 1 else "snapshot"]()
