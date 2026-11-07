# Carteira Cripto (privado)
Painel pessoal da carteira cripto: valores em R$, variações, alertas, notícias, histórico e tese semanal por IA.
- Posições: `carteira.yaml` (quantidade, custo em R$, plataforma).
- App: `app.py` (Streamlit, protegido pelo segredo `CARTEIRA_PIN`).
- Robô: `.github/workflows/robo.yml` grava `data/historico.csv` todo dia e `data/teses.json` às segundas.
