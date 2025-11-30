@echo off
REM Testa o mirror do AutoPromo
echo ======================================================================
echo TESTE DO MIRROR - AutoPromo
echo ======================================================================
echo.
echo Verificando se backend esta rodando...
echo.

cd /d "%~dp0"

python scripts\test_mirror.py

echo.
echo Pressione qualquer tecla para sair...
pause > nul
