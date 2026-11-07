"""Tese semanal da carteira por IA (Claude)."""
from __future__ import annotations
import json
from datetime import datetime
import pandas as pd
from .config import env, TESES

MODELOS = ["claude-sonnet-5-5", "claude-sonnet-4-5"]


def gerar_tese(df: pd.DataFrame, extras: dict, manchetes: dict[str, list[str]]) -> str:
    import anthropic
    cli = anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY"))
    tabela = df[["simbolo", "nome", "plataforma", "valor", "custo", "pnl_pct", "peso", "var_24h", "var_7d",
                 "var_30d", "var_1a", "dist_ath", "rank", "mcap"]].round(2).to_string(index=False)
    news = "\n".join(f"- {s}: " + " | ".join(t[:4]) for s, t in manchetes.items() if t)
    prompt = f"""Você é analista de cripto de longo prazo escrevendo para um CFO (investidor experiente).
Carteira atual (valores em R$):
{tabela}

Contexto: {json.dumps(extras, ensure_ascii=False, default=str)}
Manchetes recentes:
{news}

Escreva em português, direto e estruturado, no máximo 450 palavras:
1. **Leitura da semana** (2-3 linhas: patrimônio, desempenho vs BTC e CDI).
2. **Por moeda**: tabela markdown com Moeda | Tese em 1 linha | Risco principal | Ação (Manter / Reforçar / Reduzir / Observar).
3. **Riscos da carteira** (concentração, correlação, liquidez, small caps, desbloqueios de tokens).
4. **Rebalanceamento sugerido** (percentuais-alvo e por quê).
5. **O que monitorar na próxima semana** (3 bullets).
Não invente números que não estão nos dados. Termine com: "Não é recomendação de investimento."."""
    erro = None
    for m in MODELOS:
        try:
            r = cli.messages.create(model=m, max_tokens=2500, messages=[{"role": "user", "content": prompt}])
            return "\n".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()
        except Exception as e:  # modelo indisponível: tenta o próximo
            erro = e
    raise RuntimeError(f"Falha ao gerar a tese: {erro}")


def salvar(texto: str) -> None:
    lst = carregar()
    lst.insert(0, dict(data=datetime.now().strftime("%Y-%m-%d %H:%M"), texto=texto))
    from .cofre import gravar
    gravar(TESES, json.dumps(lst[:30], ensure_ascii=False, indent=1))


def carregar() -> list[dict]:
    from .cofre import ler
    txt = ler(TESES)
    return json.loads(txt) if txt else []
