"""Cálculos da carteira: posições, P&L, pesos e alertas."""
from __future__ import annotations
import pandas as pd


def posicoes(cfg: dict, mkt: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for p in cfg["posicoes"]:
        m = mkt.loc[p["id"]] if p["id"] in mkt.index else pd.Series(dtype=object)
        preco = m.get("preco")
        valor = (preco or 0) * p["qtd"]
        rows.append(dict(
            simbolo=p["simbolo"], nome=p.get("nome", p["simbolo"]), id=p["id"], plataforma=p.get("plataforma", ""),
            qtd=p["qtd"], custo=p["custo_brl"], preco_medio=p["custo_brl"] / p["qtd"], preco=preco,
            valor=valor, pnl=valor - p["custo_brl"], pnl_pct=(valor / p["custo_brl"] - 1) * 100 if p["custo_brl"] else None,
            var_24h=m.get("var_24h"), var_7d=m.get("var_7d"), var_30d=m.get("var_30d"), var_1a=m.get("var_1a"),
            dist_ath=m.get("dist_ath"), rank=m.get("rank"), mcap=m.get("mcap"), volume=m.get("volume"),
            imagem=m.get("imagem"), estimado=bool(p.get("estimado")), sem_preco=preco is None))
    df = pd.DataFrame(rows)
    tot = df["valor"].sum()
    df["peso"] = df["valor"] / tot * 100 if tot else 0
    return df.sort_values("valor", ascending=False).reset_index(drop=True)


def variacao_carteira(df: pd.DataFrame, col: str) -> float | None:
    """Variação ponderada da carteira no período (pelos valores atuais)."""
    d = df.dropna(subset=[col])
    if d.empty:
        return None
    ant = (d["valor"] / (1 + d[col] / 100)).sum()
    return (d["valor"].sum() / ant - 1) * 100 if ant else None


def _br(s: str) -> str:
    return s.replace(".", ",")


def alertas(df: pd.DataFrame, lim: dict) -> list[dict]:
    out = []
    for _, r in df.iterrows():
        s = r["simbolo"]
        if r["sem_preco"]:
            out.append(dict(nivel="info", simbolo=s, msg="sem cotação no CoinGecko; confira o id no carteira.yaml"))
            continue
        if pd.notna(r["var_24h"]) and abs(r["var_24h"]) >= lim["var_24h_pct"]:
            out.append(dict(nivel="alta" if r["var_24h"] > 0 else "queda", simbolo=s,
                            msg=_br(f"{r['var_24h']:+.1f}% em 24h")))
        if pd.notna(r["var_7d"]) and abs(r["var_7d"]) >= lim["var_7d_pct"]:
            out.append(dict(nivel="alta" if r["var_7d"] > 0 else "queda", simbolo=s,
                            msg=_br(f"{r['var_7d']:+.1f}% em 7 dias")))
        if pd.notna(r["pnl_pct"]) and r["pnl_pct"] <= lim["perda_custo_pct"]:
            out.append(dict(nivel="queda", simbolo=s, msg=_br(f"{r['pnl_pct']:+.1f}% abaixo do custo (revisar a tese)")))
        if pd.notna(r["pnl_pct"]) and r["pnl_pct"] >= lim["ganho_custo_pct"]:
            out.append(dict(nivel="alta", simbolo=s, msg=_br(f"{r['pnl_pct']:+.1f}% sobre o custo (avaliar realização parcial)")))
        if r["peso"] >= lim["peso_max_pct"]:
            out.append(dict(nivel="info", simbolo=s, msg=_br(f"concentração de {r['peso']:.0f}% da carteira")))
    return out
