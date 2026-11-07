"""Cofre: posições, histórico e teses ficam criptografados no repositório público (Fernet / AES).
A chave CARTEIRA_CHAVE existe só nos segredos (Streamlit e GitHub) e no chave_carteira.txt do seu PC."""
from __future__ import annotations
from pathlib import Path
from .config import env, ROOT


def _f():
    from cryptography.fernet import Fernet
    k = env("CARTEIRA_CHAVE")
    if not k:
        p = ROOT / "chave_carteira.txt"
        k = p.read_text(encoding="utf-8-sig").strip() if p.exists() else ""
    if not k:
        raise RuntimeError("Chave CARTEIRA_CHAVE não configurada nos segredos.")
    return Fernet(k.encode())


def ler(plano: Path) -> str | None:
    """Lê o arquivo: a versão aberta local (se existir) ou a cifrada (.enc)."""
    if plano.exists():
        return plano.read_text(encoding="utf-8")
    enc = plano.with_name(plano.name + ".enc")
    if enc.exists():
        return _f().decrypt(enc.read_bytes()).decode("utf-8")
    return None


def gravar(plano: Path, texto: str) -> None:
    """Grava somente a versão cifrada (.enc)."""
    enc = plano.with_name(plano.name + ".enc")
    enc.parent.mkdir(exist_ok=True)
    enc.write_bytes(_f().encrypt(texto.encode("utf-8")))
