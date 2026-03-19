@echo off
echo ========================================
echo   Iniciando Servidores SICFAAE
echo ========================================
echo.

echo [1/2] Iniciando DRH na porta 8000...
start "SICFAAE-DRH" cmd /k "cd sicfaae-drh && python manage.py runserver 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Iniciando DEFC na porta 8001...
start "SICFAAE-DEFC" cmd /k "cd sicfaae-defc && python manage.py runserver 8001"

echo.
echo ========================================
echo   Servidores Iniciados!
echo ========================================
echo.
echo DRH:  http://localhost:8000
echo DEFC: http://localhost:8001
echo.
echo Pressione qualquer tecla para abrir os navegadores...
pause >nul

start http://localhost:8000
start http://localhost:8001

echo.
echo Para parar os servidores, feche as janelas do terminal.
echo.
