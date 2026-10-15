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


if __name__ == "__main__":
    rows = licenses()
    text = ["# Üçüncü taraf lisansları", "",
            "Taşınabilir pakette dağıtılan çalışma bağımlılıkları ve lisansları (`python tools/lisanslar.py` ile üretilir).",
            "Hepsi ticari kullanıma ve yeniden dağıtıma izin veren lisanslardır (MIT, BSD, Apache-2.0, PSF, MPL-2.0).",
            "Apache-2.0 ve diğer lisansların koşulu olan lisans metinleri, pakette her kütüphanenin kendi",
            "`*.dist-info` klasöründe değiştirilmeden bulunur. certifi (MPL-2.0) değiştirilmeden dağıtılır.",
            "Gömülü Python yorumlayıcısı Python Software Foundation License ile dağıtılır.", "",
            "| Paket | Sürüm | Lisans |", "|---|---|---|",
            *[f"| {n} | {v} | {lic} |" for n, v, lic in rows], ""]
    (ROOT / "docs" / "LISANSLAR.md").write_text("\n".join(text), encoding="utf-8")
    print(f"{len(rows)} paket yazıldı")
