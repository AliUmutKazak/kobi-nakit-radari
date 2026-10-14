@echo off
chcp 65001 >nul
title KOBİ Nakit Akışı Radarı
cd /d "%~dp0"
set "VENV=%USERPROFILE%\.venvs\kobi-radar"

if not exist "%VENV%\Scripts\python.exe" (
    echo İlk kurulum yapılıyor; internet bağlantısıyla birkaç dakika sürer...
    py -3 -m venv "%VENV%" 2>nul || python -m venv "%VENV%"
    if not exist "%VENV%\Scripts\python.exe" (
        echo.
        echo Python bulunamadı. python.org adresinden Python 3.13 kurun, kurulumda
        echo "Add python.exe to PATH" kutusunu işaretleyin ve bu dosyayı yeniden çalıştırın.
        pause
        exit /b 1
    )
)

rem Gerekli paketler eksikse ya da sürümleri değiştiyse kurulur; tamsa birkaç saniyede geçer.
"%VENV%\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo.
    echo Paket kurulumu tamamlanamadı. İnternet bağlantınızı kontrol edip yeniden deneyin.
    pause
    exit /b 1
)

echo.
echo Panel tarayıcınızda açılıyor: http://localhost:8501
echo Paneli kapatmak için bu pencereyi kapatın.
echo.
"%VENV%\Scripts\python.exe" -m streamlit run app.py
pause
