"""Configuração: posições (carteira.yaml) e chaves (segredos do Streamlit, variáveis de ambiente ou chaves.txt)."""
from __future__ import annotations
import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HIST = DATA / "historico.csv"
TESES = DATA / "teses.json"


def cfg() -> dict:
    from .cofre import ler
    return yaml.safe_load(ler(ROOT / "carteira.yaml"))


def _chaves_txt() -> dict:
    for p in (ROOT / "chaves.txt", ROOT.parent / "radar-cripto" / "chaves.txt"):
        if p.exists():
            for enc in ("utf-8-sig", "utf-16", "latin-1"):
                try:
                    out = {}
                    for ln in p.read_text(encoding=enc).splitlines():
                        if "=" in ln and not ln.strip().startswith("#"):
                            k, v = ln.split("=", 1)
                            out[k.strip()] = v.strip().strip('"').strip("'")
                    return out
                except Exception:
                    continue
    return {}


def env(nome: str, padrao: str = "") -> str:
    v = os.environ.get(nome)
    if not v:
        try:
            import streamlit as st
            v = st.secrets.get(nome)
        except Exception:
            v = None
    if not v:
        v = _chaves_txt().get(nome)
    return (str(v).strip().strip('"').strip("'") if v else padrao)
