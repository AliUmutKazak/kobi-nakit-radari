"""Çalışma bağımlılıklarının (alt bağımlılıklar dahil) lisans listesini docs/LISANSLAR.md'ye yazar.

Kullanım (projenin sanal ortamıyla): python tools/lisanslar.py
"""
from __future__ import annotations

import importlib.metadata as md
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_ONLY = {"pytest"}


def licenses() -> list[tuple[str, str, str]]:
    req = [line.split("==")[0].strip() for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
           if "==" in line and not line.startswith("#")]
    seen, rows = set(), []

    def walk(name: str) -> None:
        key = name.lower().replace("_", "-")
        if key in seen:
            return
        seen.add(key)
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            return
        lic = dist.metadata.get("License-Expression") or dist.metadata.get("License") or ""
        if not lic or len(lic) > 60:
            classifiers = [c.split("::")[-1].strip() for c in (dist.metadata.get_all("Classifier") or [])
                           if c.startswith("License ::")]
            lic = "; ".join(classifiers) or "belirtilmemiş"
        rows.append((dist.metadata["Name"], dist.version, lic.replace("\n", " ")))
        for r in dist.requires or []:
            if "extra ==" not in r:
                walk(re.split(r"[ ;<>=!~\[(]", r, maxsplit=1)[0])

    for name in req:
        if name not in DEV_ONLY:
            walk(name)
    return sorted(rows, key=lambda x: x[0].lower())


DATA_SOURCES = [
    "## Veri kaynakları ve kullanım koşulları", "",
    "| Kaynak | Kullanım | Dağıtım | Koşul |", "|---|---|---|---|",
    "| TCMB–TÜİK, Sektör Bilançoları 2025 (Alacak Devir Hızı çeyreklikleri) | Panelde sektör karşılaştırması "
    "(`src/radar/data/sektor_alacak_2025.csv`), senaryo laboratuvarı | Depoda var; taşınabilir pakete **yalnızca** "
    "`--tcmb-izni` ile girer | TCMB Kullanım Şartları: kaynak gösterilerek yayımlanabilir, ticari amaçlarla kullanımı "
    "TCMB'nin yazılı iznine tabidir (18.10.2026'da okundu) |",
    "| TCMB Tebliği, TTK m.1530/7 değerleri (RG 02.01.2026, sayı 33125) | Kodda sabit (mesaj metnine yazılmaz) | Var | "
    "Resmî Gazete'de yayımlanan resmî metin (FSEK m.31) |",
    "| TBB Risk Merkezi, karşılıksız çek oranı (tek sayı, %3,4) | Simülasyon parametresi | Var | Kaynak gösterilerek; "
    "tek bir istatistik değeri |",
    "| TÜİK, TÜFE yıllık değişim aralığı | Laboratuvar aralığı (atıf) | Veri dağıtılmaz | Kaynak gösterilerek |",
    "| UCI Online Retail II (Chen 2012, doi:10.24432/C5CG6D) | Doğrulama | Veri dağıtılmaz (`data/` dışarıda) | CC BY 4.0: atıf |",
    "| Payment Date Dataset (Kaggle: rajattomar132) | Doğrulama | Veri dağıtılmaz | CC0: Public Domain |",
    "| IBM Late Payment Histories (Kaggle: hhenry) | Doğrulama | Veri dağıtılmaz | Lisans belirtilmemiş (\"Unknown\"); "
    "yalnızca toplu sonuç yayımlanır. Ticari tanıtımda kullanılmadan önce hukuki görüş alınmalı |", ""]


if __name__ == "__main__":
    rows = licenses()
    text = ["# Üçüncü taraf lisansları", "",
            "Taşınabilir pakette dağıtılan çalışma bağımlılıkları ve lisansları (`python tools/lisanslar.py` ile üretilir).",
            "Hepsi ticari kullanıma ve yeniden dağıtıma izin veren lisanslardır (MIT, BSD, Apache-2.0, PSF, MPL-2.0).",
            "Apache-2.0 ve diğer lisansların koşulu olan lisans metinleri, pakette her kütüphanenin kendi",
            "`*.dist-info` klasöründe değiştirilmeden bulunur. certifi (MPL-2.0) değiştirilmeden dağıtılır.",
            "Gömülü Python yorumlayıcısı Python Software Foundation License ile dağıtılır.", "",
            "| Paket | Sürüm | Lisans |", "|---|---|---|",
            *[f"| {n} | {v} | {lic} |" for n, v, lic in rows], "", *DATA_SOURCES]
    (ROOT / "docs" / "LISANSLAR.md").write_text("\n".join(text), encoding="utf-8")
    print(f"{len(rows)} paket yazıldı")
