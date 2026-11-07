import pandas as pd
from carteira import calc
from carteira.config import cfg


def _mkt(c):
    rows = [dict(id=p["id"], preco=p["custo_brl"] / p["qtd"] * 1.1, var_24h=10.0, var_7d=-2.0, var_30d=5.0,
                 var_1a=None, dist_ath=-80.0, rank=100, mcap=1e9, volume=1e7, imagem=None) for p in c["posicoes"]]
    return pd.DataFrame(rows).set_index("id")


def test_posicoes_e_alertas():
    c = cfg()
    df = calc.posicoes(c, _mkt(c))
    assert abs(df["pnl_pct"].mean() - 10) < 1e-6
    assert abs(df["peso"].sum() - 100) < 1e-6
    assert abs(calc.variacao_carteira(df, "var_24h") - 10) < 1e-6
    al = calc.alertas(df, c["alertas"])
    assert any("24h" in a["msg"] for a in al)
