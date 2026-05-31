# Controle de Pausas

Aplicativo em Streamlit para calcular pausas por colaborador a partir do horario de entrada.

## O que ele faz

- Filtra por supervisora.
- Filtra por horario de entrada.
- Calcula jornada de 6h20.
- Calcula duas pausas de 10 minutos e uma pausa de 20 minutos.
- Mostra uma tabela completa e uma visualizacao em cards para celular.
- Exporta a escala em CSV ou Excel.

## Rodar localmente

```powershell
cd C:\Users\Mykae\OneDrive\Documentos\DEV\pausas_streamlit
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Subir no Streamlit Cloud

1. Envie esta pasta para um repositorio no GitHub.
2. No Streamlit Cloud, crie um app novo apontando para `app.py`.
3. Quando quiser atualizar a base, use a opcao "Atualizar base de colaboradores" no proprio app.

## Regra inicial das pausas

O app vem com estes valores padrao:

- Pausa 1: 90 minutos depois da entrada.
- Pausa de 20 minutos: 195 minutos depois da entrada.
- Pausa 2: 315 minutos depois da entrada.
