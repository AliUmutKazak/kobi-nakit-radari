@echo off
chcp 65001 >nul
title KOBİ Nakit Akışı Radarı
cd /d "%~dp0"
set "VENV=%USERPROFILE%\.venvs\kobi-radar"
set "URL=http://127.0.0.1:8501"

rem Panel zaten açıksa ikinci kez başlatmak yerine tarayıcıda göster.
powershell -NoProfile -Command "try { Invoke-WebRequest '%URL%/_stcore/health' -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo Panel zaten açık; tarayıcıda gösteriliyor.
    start "" "%URL%"
    timeout /t 3 >nul
    exit /b 0
)

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

rem Paketler yalnızca ilk kurulumda ya da requirements.txt değiştiğinde kurulur.
fc /b requirements.txt "%VENV%\kurulu_paketler.txt" >nul 2>&1
if errorlevel 1 (
    echo Gerekli paketler kuruluyor...
    "%VENV%\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Paket kurulumu tamamlanamadı. İnternet bağlantınızı kontrol edip yeniden deneyin.
        pause
        exit /b 1
    )
    copy /y requirements.txt "%VENV%\kurulu_paketler.txt" >nul
)

echo.
echo Panel açılıyor: %URL%
echo Tarayıcı kendiliğinden açılmazsa bu adresi tarayıcınıza yazın.
echo Paneli kapatmak için bu pencereyi kapatın.
echo.
rem Sunucu hazır olunca tarayıcıyı aç (Streamlit'in kendi açma davranışına güvenilmez).
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "for ($i = 0; $i -lt 240; $i++) { try { Invoke-WebRequest '%URL%/_stcore/health' -UseBasicParsing -TimeoutSec 2 | Out-Null; Start-Process '%URL%'; break } catch { Start-Sleep -Milliseconds 500 } }"
"%VENV%\Scripts\python.exe" -m streamlit run app.py
echo.
echo Panel kapandı. Hata mesajı görüyorsanız bu pencerenin ekran görüntüsünü saklayın.
pause
