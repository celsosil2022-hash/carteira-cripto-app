"""Coleta: preços em R$ (CoinGecko), dólar, CDI (Banco Central), notícias (Google Notícias) e histórico."""
from __future__ import annotations
import time
import urllib.parse
from datetime import date, datetime
import pandas as pd
import requests
from .config import env, HIST

CG = "https://api.coingecko.com/api/v3"
UA = {"User-Agent": "carteira-cripto/1.0"}


def _cg(path: str, params: dict) -> object:
    h = dict(UA)
    k = env("COINGECKO_API_KEY")
    if k:
        h["x-cg-demo-api-key"] = k
    for tent in range(4):
        r = requests.get(f"{CG}{path}", params=params, headers=h, timeout=30)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 0) or 0) or 10 * (tent + 1))
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()


def resolver_id(simbolo: str) -> str | None:
    """Acha o id do CoinGecko pelo símbolo (o de maior valor de mercado)."""
    res = _cg("/search", {"query": simbolo}).get("coins", [])
    for c in res:
        if (c.get("symbol") or "").upper() == simbolo.upper():
            return c["id"]
    return None


def mercado(posicoes: list[dict]) -> pd.DataFrame:
    """Preço e variações em R$ para as moedas da carteira + BTC (referência)."""
    ids = {p["id"] for p in posicoes} | {"bitcoin"}
    campos = "24h,7d,30d,1y"
    dados = _cg("/coins/markets", {"vs_currency": "brl", "ids": ",".join(sorted(ids)),
                                   "price_change_percentage": campos, "per_page": 250})
    achados = {d["id"] for d in dados}
    for p in posicoes:  # id errado? tenta pelo símbolo
        if p["id"] not in achados:
            novo = resolver_id(p["simbolo"])
            if novo:
                p["id"] = novo
                dados += _cg("/coins/markets", {"vs_currency": "brl", "ids": novo,
                                                "price_change_percentage": campos})
    rows = [dict(id=d["id"], preco=d.get("current_price"), mcap=d.get("market_cap"),
                 rank=d.get("market_cap_rank"), volume=d.get("total_volume"),
                 var_24h=d.get("price_change_percentage_24h_in_currency"),
                 var_7d=d.get("price_change_percentage_7d_in_currency"),
                 var_30d=d.get("price_change_percentage_30d_in_currency"),
                 var_1a=d.get("price_change_percentage_1y_in_currency"),
                 ath=d.get("ath"), dist_ath=d.get("ath_change_percentage"),
                 imagem=d.get("image")) for d in dados]
    return pd.DataFrame(rows).drop_duplicates("id").set_index("id")


def dolar() -> float | None:
    try:
        d = _cg("/simple/price", {"ids": "tether", "vs_currencies": "brl"})
        return float(d["tether"]["brl"])
    except Exception:
        return None


def cdi_acumulado(desde: str) -> float:
    """CDI acumulado (%) desde a data, pela série 12 do Banco Central."""
    ini = datetime.strptime(desde, "%Y-%m-%d").strftime("%d/%m/%Y")
    fim = date.today().strftime("%d/%m/%Y")
    try:
        r = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados",
                         params={"formato": "json", "dataInicial": ini, "dataFinal": fim}, headers=UA, timeout=20)
        fator = 1.0
        for x in r.json():
            fator *= 1 + float(x["valor"]) / 100
        return (fator - 1) * 100
    except Exception:
        return 0.0


def noticias(nome: str, simbolo: str, n: int = 6) -> list[dict]:
    """Últimas notícias do ativo no Google Notícias (português e inglês)."""
    import feedparser
    out = []
    for q, hl, gl, ceid in ((f'"{nome}" cripto OR {simbolo}', "pt-BR", "BR", "BR:pt-419"),
                            (f'"{nome}" crypto {simbolo}', "en-US", "US", "US:en")):
        url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:14d")
               + f"&hl={hl}&gl={gl}&ceid={ceid}")
        try:
            f = feedparser.parse(requests.get(url, headers=UA, timeout=20).content)
        except Exception:
            continue
        for e in f.entries[:n]:
            pub = e.get("published_parsed")
            out.append(dict(titulo=e.get("title", ""), link=e.get("link", ""),
                            fonte=(e.get("source") or {}).get("title", ""),
                            data=datetime(*pub[:6]) if pub else None, idioma=hl[:2]))
    out.sort(key=lambda x: x["data"] or datetime.min, reverse=True)
    return out[: n * 2]


def historico() -> pd.DataFrame:
    import io
    from .cofre import ler
    txt = ler(HIST)
    if txt:
        return pd.read_csv(io.StringIO(txt), parse_dates=["dia"])
    return pd.DataFrame(columns=["dia", "simbolo", "qtd", "preco", "valor", "custo", "btc_brl", "dolar"])
