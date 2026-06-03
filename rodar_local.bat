@echo off
cd /d "%~dp0"
"C:\Users\Mykae\OneDrive\Documentos\DEV\pausas_streamlit\.venv\Scripts\streamlit.exe" run app.py --server.port 8501 --server.address 127.0.0.1
pause
