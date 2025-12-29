@echo off
echo ========================================
echo Remote Access Client - Environment Setup
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.11+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Проверка pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not found!
    echo Installing pip...
    python -m ensurepip --upgrade
)

echo [OK] pip found
echo.

REM Обновление pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Создание виртуального окружения (опционально)
set /p CREATE_VENV="Create virtual environment? (y/n): "
if /i "%CREATE_VENV%"=="y" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    
    echo [OK] Virtual environment created and activated
    echo.
)

REM Установка зависимостей
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [OK] All dependencies installed
echo.

REM Установка PyInstaller для сборки
echo Installing PyInstaller...
pip install pyinstaller
echo.

REM Создание директории resources если не существует
if not exist "resources" (
    echo Creating resources directory...
    mkdir resources
    echo [!] Don't forget to add icon.ico to resources folder
    echo.
)

REM Создание директории для логов
if not exist "logs" (
    mkdir logs
    echo Created logs directory
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Add your icon.ico to resources/ folder (optional)
echo 2. Run: python client/main.py (for testing)
echo 3. Run: build.bat (to build .exe)
echo.
echo Installed packages:
pip list | findstr "socketio pywinauto PyQt5 pyinstaller"
echo.

pause
