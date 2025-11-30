@echo off
REM Inicia o backend do AutoPromo
echo ======================================================================
echo INICIANDO BACKEND AUTOPROMO
echo ======================================================================
echo.

cd /d "%~dp0backend"

echo Backend iniciando na porta 8000...
echo Pressione CTRL+C para parar
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
