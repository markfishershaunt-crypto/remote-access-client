@echo off
echo Building Remote Access Client...

REM Установка зависимостей
pip install -r requirements.txt
pip install pyinstaller

REM Сборка
pyinstaller build.spec --clean

echo.
echo Build complete! Check dist/ folder for RemoteAccessClient.exe
pause
