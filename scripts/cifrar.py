"""Roda no seu PC: cria a chave (1a vez) e cifra o carteira.yaml -> carteira.yaml.enc."""
from pathlib import Path
from cryptography.fernet import Fernet

raiz = Path(__file__).resolve().parent.parent
chave = raiz / "chave_carteira.txt"
if not chave.exists():
    chave.write_text(Fernet.generate_key().decode(), encoding="utf-8")
f = Fernet(chave.read_text(encoding="utf-8").strip().encode())
(raiz / "carteira.yaml.enc").write_bytes(f.encrypt((raiz / "carteira.yaml").read_bytes()))
print("OK: carteira.yaml cifrado")
