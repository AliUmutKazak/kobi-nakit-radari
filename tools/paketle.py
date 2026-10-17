"""Taşınabilir paket üretir: Python kurmaya gerek kalmadan çalışan, zip'lenmiş tek klasör.

Kullanım (geliştirici bilgisayarında, projenin sanal ortamıyla):
    python tools/paketle.py

Çıktı: dist/KobiRadar-<sürüm>.zip. Kullanıcı zip'i açar, KOBI_Radar.bat dosyasına çift tıklar.

İçerik:
- python.org'un resmî "embeddable" Python'u (projeyi çalıştıran sürümün aynısı),
- requirements.txt'teki çalışma paketleri (test araçları hariç),
- panel kodu, ayarlar, örnek dosyalar ve kullanım kılavuzu.

Paket, Windows'un yol uzunluğu sınırına takılmamak ve OneDrive eşitlemesine girmemek için
yerel uygulama klasöründe kurulur; yalnızca son zip proje klasörüne kopyalanır.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "KobiRadar" / "paket"
PY = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
EMBED_URL = f"https://www.python.org/ftp/python/{PY}/python-{PY}-embed-amd64.zip"
DEV_ONLY = {"pytest"}
COPY = ["app.py", "src", ".streamlit", "ornekler", "requirements.txt", "docs/KULLANIM_KILAVUZU.md",
        "docs/pilot/PILOT_PROTOKOLU.md",
        "docs/pilot/mali_musavir_pilot_foyu.docx", "docs/LISANSLAR.md", "docs/LAB_RAPORU.md", "docs/kvkk/VERI_ENVANTERI_VE_IMHA.md"]

START_BAT = r'''@echo off
chcp 65001 >nul
title KOBİ Nakit Akışı Radarı
cd /d "%~dp0"
set "URL=http://127.0.0.1:8501"

rem Panel zaten açıksa ikinci kez başlatmak yerine tarayıcıda göster.
powershell -NoProfile -Command "try { Invoke-WebRequest '%URL%/_stcore/health' -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo Panel zaten açık; tarayıcıda gösteriliyor.
    start "" "%URL%"
    timeout /t 3 >nul
    exit /b 0
)

echo Panel açılıyor: %URL%
echo Tarayıcı kendiliğinden açılmazsa bu adresi tarayıcınıza yazın.
echo Paneli kapatmak için bu pencereyi kapatın.
echo.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "for ($i = 0; $i -lt 240; $i++) { try { Invoke-WebRequest '%URL%/_stcore/health' -UseBasicParsing -TimeoutSec 2 | Out-Null; Start-Process '%URL%'; break } catch { Start-Sleep -Milliseconds 500 } }"
"%~dp0python\python.exe" -m streamlit run app.py
echo.
echo Panel kapandı. Hata mesajı görüyorsanız bu pencerenin ekran görüntüsünü saklayın.
pause
'''

README = """KOBİ Nakit Akışı Radarı
=======================

Kurulum gerekmez.

1. Bu klasörü bilgisayarınızda kalıcı bir yere taşıyın (ör. Belgeler).
2. KOBI_Radar.bat dosyasına çift tıklayın. Panel tarayıcınızda açılır.
3. Kapatmak için siyah pencereyi kapatın.

Ayrıntılı anlatım: KULLANIM_KILAVUZU.md

Verileriniz bu klasörde değil, bilgisayarınızın yerel uygulama klasöründe
(%LOCALAPPDATA%\\KobiRadar) saklanır; klasörü silmek ya da güncellemek verilerinizi silmez.
Panel yalnızca bu bilgisayardan açılabilir ve internete veri göndermez.
"""


def step(text: str) -> None:
    print(f"\n== {text}", flush=True)


def download(url: str, target: Path) -> None:
    if target.exists():
        print(f"önbellekte: {target.name}")
        return
    if not url.startswith("https://www.python.org/"):
        raise SystemExit("Yalnızca python.org'dan indirilir.")
    tmp = target.with_suffix(".indiriliyor")
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    tmp.rename(target)


def main() -> None:
    version = date.today().strftime("%Y.%m.%d")
    app_dir = WORK / "KobiRadar"
    cache = WORK / "onbellek"
    cache.mkdir(parents=True, exist_ok=True)
    if app_dir.exists():
        shutil.rmtree(app_dir)

    step(f"Python {PY} (gömülebilir) hazırlanıyor")
    embed = cache / Path(EMBED_URL).name
    download(EMBED_URL, embed)
    print("SHA-256:", hashlib.sha256(embed.read_bytes()).hexdigest())
    py_dir = app_dir / "python"
    with zipfile.ZipFile(embed) as z:
        z.extractall(py_dir)
    pth = next(py_dir.glob("python*._pth"))
    lines = [l for l in pth.read_text().splitlines() if l.strip() and not l.lstrip().startswith("#")]
    pth.write_text("\n".join(lines + ["Lib\\site-packages", "import site"]) + "\n")

    step("Paketler kuruluyor")
    reqs = [l for l in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#") and l.split("==")[0].strip().lower() not in DEV_ONLY]
    runtime = cache / "calisma_paketleri.txt"
    runtime.write_text("\n".join(reqs) + "\n", encoding="utf-8")
    site = py_dir / "Lib" / "site-packages"
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check", "--no-compile",
                    "--only-binary=:all:", "--target", str(site), "-r", str(runtime)], check=True)
    for junk in list(site.glob("**/__pycache__")) + list(site.glob("bin")):
        shutil.rmtree(junk, ignore_errors=True)

    step("Panel kopyalanıyor")
    for item in COPY:
        src = ROOT / item
        dst = app_dir / (Path(item).name if item.startswith("docs/") else item)
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(src, dst)
    (app_dir / "KOBI_Radar.bat").write_bytes(START_BAT.replace("\n", "\r\n").encode("utf-8"))
    (app_dir / "BENİ_OKU.txt").write_text(README.replace("\n", "\r\n"), encoding="utf-8")

    step("Kendini sınama: paket kendi Python'uyla açılabiliyor mu")
    check = subprocess.run([str(py_dir / "python.exe"), "-c",
                            "import sys; sys.path.insert(0, 'src'); import streamlit, lightgbm, pandas, defusedxml; "
                            "from radar import pipeline; print('tamam', sys.version.split()[0])"],
                           cwd=app_dir, capture_output=True, text=True)
    print(check.stdout.strip() or check.stderr[-2000:])
    if check.returncode:
        raise SystemExit("Paket kendi Python'uyla açılamadı.")

    step("Zip'leniyor")
    out_dir = ROOT / "dist"
    out_dir.mkdir(exist_ok=True)
    archive = shutil.make_archive(str(WORK / f"KobiRadar-{version}"), "zip", WORK, "KobiRadar")
    final = out_dir / Path(archive).name
    shutil.copy2(archive, final)
    size = sum(f.stat().st_size for f in app_dir.rglob("*") if f.is_file())
    print(f"klasör: {size / 1e6:.0f} MB | zip: {final.stat().st_size / 1e6:.0f} MB -> {final}")


if __name__ == "__main__":
    main()
