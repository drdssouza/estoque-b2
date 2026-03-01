@echo off
title Build Controle B2

echo.
echo ========================================
echo   Build Controle B2 v1.2.0
echo ========================================
echo.

:: Verificar se PyInstaller esta disponivel
where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [ERRO] PyInstaller nao encontrado.
    echo        Ative seu ambiente virtual ou instale: pip install pyinstaller
    pause
    exit /b 1
)

:: Verificar se Inno Setup esta instalado
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo [ERRO] Inno Setup 6 nao encontrado.
    echo        Baixe em: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

:: Passo 1: PyInstaller
echo [1/2] Gerando executavel com PyInstaller...
echo.
pyinstaller build.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo [ERRO] PyInstaller falhou! Veja o log acima.
    pause
    exit /b 1
)

echo.
echo [OK] Executavel gerado em dist\estoque-b2\

:: Passo 2: Inno Setup
echo.
echo [2/2] Criando instalador com Inno Setup...
echo.
"%ISCC%" installer.iss
if errorlevel 1 (
    echo.
    echo [ERRO] Inno Setup falhou! Veja o log acima.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Instalador criado com sucesso!
echo   Local: dist_installer\Controle-B2-Setup-1.2.0.exe
echo ========================================
echo.
pause
