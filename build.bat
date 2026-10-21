@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --windowed --name OpenAnime --collect-submodules yt_dlp main.py
echo.
echo Listo: dist\OpenAnime\OpenAnime.exe
pause
