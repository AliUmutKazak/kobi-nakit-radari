# Üçüncü taraf lisansları

Taşınabilir pakette dağıtılan çalışma bağımlılıkları ve lisansları (`python tools/lisanslar.py` ile üretilir).
Hepsi ticari kullanıma ve yeniden dağıtıma izin veren lisanslardır (MIT, BSD, Apache-2.0, PSF, MPL-2.0).
Apache-2.0 ve diğer lisansların koşulu olan lisans metinleri, pakette her kütüphanenin kendi
`*.dist-info` klasöründe değiştirilmeden bulunur. certifi (MPL-2.0) değiştirilmeden dağıtılır.
Gömülü Python yorumlayıcısı Python Software Foundation License ile dağıtılır.

| Paket | Sürüm | Lisans |
|---|---|---|
| altair | 6.3.0 | BSD License |
| anyio | 4.15.1 | MIT |
| attrs | 26.1.0 | MIT |
| certifi | 2026.7.22 | MPL-2.0 |
| cffi | 2.1.1 | MIT-0 |
| charset-normalizer | 3.5.2 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| cloudpickle | 3.1.2 | BSD-3-Clause |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause |
| defusedxml | 0.7.1 | PSFL |
| et_xmlfile | 2.0.0 | MIT |
| h11 | 0.16.0 | MIT |
| httptools | 0.9.0 | MIT |
| idna | 3.20 | BSD-3-Clause |
| itsdangerous | 2.2.0 | BSD License |
| Jinja2 | 3.1.6 | BSD License |
| joblib | 1.6.0 | BSD-3-Clause |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| lightgbm | 4.7.0 | MIT |
| MarkupSafe | 3.0.4 | BSD-3-Clause |
| narwhals | 2.27.1 | MIT |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| openpyxl | 3.1.5 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pandas | 3.0.6 | BSD License |
| pillow | 12.3.0 | MIT-CMU |
| plotly | 7.1.0 | MIT |
| protobuf | 7.36.2 | 3-Clause BSD License |
| pyarrow | 25.0.1 | Apache-2.0 |
| pycparser | 3.11 | BSD-3-Clause |
| pydeck | 0.9.3 | Apache License 2.0 |
| python-dateutil | 2.9.0.post0 | Dual License |
| python-multipart | 0.0.32 | Apache-2.0 |
| referencing | 0.37.0 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| rpds-py | 2026.9.1 | MIT |
| scikit-learn | 1.9.1 | BSD-3-Clause |
| scipy | 1.18.1 | BSD License |
| six | 1.17.0 | MIT |
| starlette | 1.8.0 | BSD-3-Clause |
| streamlit | 1.65.0 | Apache-2.0 |
| threadpoolctl | 3.7.0 | BSD-3-Clause |
| toml | 0.10.2 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| tzdata | 2026.5 | Apache-2.0 |
| urllib3 | 2.8.0 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| watchdog | 6.0.0 | Apache-2.0 |
| websockets | 17.2 | BSD-3-Clause |

## Veri kaynakları ve kullanım koşulları

| Kaynak | Kullanım | Dağıtım | Koşul |
|---|---|---|---|
| TCMB–TÜİK, Sektör Bilançoları 2025 (Alacak Devir Hızı çeyreklikleri) | Panelde sektör karşılaştırması (`src/radar/data/sektor_alacak_2025.csv`), senaryo laboratuvarı | Depoda var; taşınabilir pakete **yalnızca** `--tcmb-izni` ile girer | TCMB Kullanım Şartları: kaynak gösterilerek yayımlanabilir, ticari amaçlarla kullanımı TCMB'nin yazılı iznine tabidir (18.10.2026'da okundu) |
| TCMB Tebliği, TTK m.1530/7 değerleri (RG 02.01.2026, sayı 33125) | Kodda sabit (mesaj metnine yazılmaz) | Var | Resmî Gazete'de yayımlanan resmî metin (FSEK m.31) |
| TBB Risk Merkezi, karşılıksız çek oranı (tek sayı, %3,4) | Simülasyon parametresi | Var | Kaynak gösterilerek; tek bir istatistik değeri |
| TÜİK, TÜFE yıllık değişim aralığı | Laboratuvar aralığı (atıf) | Veri dağıtılmaz | Kaynak gösterilerek |
| UCI Online Retail II (Chen 2012, doi:10.24432/C5CG6D) | Doğrulama | Veri dağıtılmaz (`data/` dışarıda) | CC BY 4.0: atıf |
| Payment Date Dataset (Kaggle: rajattomar132) | Doğrulama | Veri dağıtılmaz | CC0: Public Domain |
| IBM Late Payment Histories (Kaggle: hhenry) | Doğrulama | Veri dağıtılmaz | Lisans belirtilmemiş ("Unknown"); yalnızca toplu sonuç yayımlanır. Ticari tanıtımda kullanılmadan önce hukuki görüş alınmalı |
