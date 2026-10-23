# KOBİ Nakit Akışı Radarı

**Küçük işletmeler için olasılıksal nakit akışı tahmini ve tahsilat karar desteği.**
*Probabilistic 90-day cash-flow forecasting and collections decision support for Turkish SMEs (Python, LightGBM, Monte Carlo, Streamlit).*

Küçük bir işletme için asıl soru "müşteri ne zaman öder?" değil, "önümüzdeki haftalarda kasam eksiye düşer mi?" sorusudur. Radar, açık faturaların ne zaman tahsil edileceğini müşterilerin geçmiş ödeme davranışından tahmin eder; giderler, borçlar, çekler, vergi takvimi ve kur riskiyle birleştirip 90 günlük kasayı bir aralık olarak gösterir:

- **Kasa bandı:** kötümser (P10), orta (P50) ve iyimser (P90) senaryo; kasanın eksiye düşme olasılığı ve "güvenle harcanabilir tutar".
- **Tahsilat listesi:** kasa açığını kapatmaya en çok yarayacak faturalar, onay bekleyen mesaj taslaklarıyla (WhatsApp, e-posta). Panel hiçbir mesajı kendiliğinden göndermez.
- **Kendini sınayan tahmin:** işletmenin kendi geçmişinde geriye dönük test; model basit yöntemlerin gerisindeyse panel bunu açıkça söyler.
- **Türkiye pratiği:** cari hesap ekstresi ve muavin, çek/senet portföyü, UBL-TR e-fatura (KABUL/RED yanıtları dahil), vergi takvimi ve resmî tatiller, dövizli alacak ve borç.

> **Durum: pilot öncesi prototip.** Türk KOBİ verisiyle henüz sınanmadı. Sonuçlar sentetik veri, senaryo laboratuvarı ve yabancı açık veri setleriyle elde edildi. Veriler yalnızca işletmenin bilgisayarında saklanır.

## Doğrulama: neler ölçüldü

Kabul ölçütleri projede uydurulmadı; risk modeli doğrulamasında kullanılan standart testlerden alındı: Basel trafik ışığı (BCBS 1996; BDDK), Kupiec kapsama testi ve Diebold-Mariano isabet testi. Ayrıntı ve denenip reddedilen yöntemler: [docs/DOGRULAMA.md](docs/DOGRULAMA.md).

| Veri | Sonuç | Sınır |
|---|---|---|
| Gerçek açık veri: IBM Late Payment ve Payment Date (Kaggle), 16 geçmiş tahmin tarihi | Kötümser uç dört durumun dördünde Basel yeşil. İsabet, en iyi basit yöntemle istatistiksel olarak **eşdeğer**; üçünde sayısal olarak daha iyi. | Yabancı veri; "akıllı tahmin" üstünlüğü kanıtlanmadı. |
| Senaryo laboratuvarı: 240 sentetik işletme (sınav kümesi, bir kez koşuldu) | Kötümser uç aşımı %7, iyimser %10 (hedef %10); Basel yeşil, Kupiec iki uçta da geçiyor. | Sentetik veriyi üreten kurallar bize ait. |
| Gerçek KOBİ satış verisi: UCI Online Retail II | Yeni satış tahmininde 90 günlük sapma, mevsimsel yöntem işletmenin kendi geçmişinde seçilince %37'den %8'e indi. | Ödeme tarihi yok; yalnızca satış tarafı sınandı. |
| Bilinen kusur | Yüksek riskte eksiye düşme olasılığı ortaya sıkışık (%80 gösterilen durumda gerçekleşme %92). Panel %50 ve üzerini "en az" diye gösterir. | Yeniden ayar gerçek sonuç verisi gerektirir; pilot sonrasına kayıtlı. |

Pilot verisi gelene kadar model ve laboratuvar donduruldu: vekil veride ince ayar yapmak, o veriyi ezberlemek olurdu. Pilot ölçüm planı (önceden kayıtlı başarı ölçütleriyle): [docs/pilot/PILOT_PROTOKOLU.md](docs/pilot/PILOT_PROTOKOLU.md).

## Çalıştırma

**İşletme bilgisayarında:** taşınabilir paket `KobiRadar-<sürüm>.zip` açılır ve `KOBI_Radar.bat` çift tıklanır; Python kurmak gerekmez. Panel http://localhost:8501 adresinde, yalnızca o bilgisayardan erişilebilir olarak açılır. Kullanım: [docs/KULLANIM_KILAVUZU.md](docs/KULLANIM_KILAVUZU.md). Güvenlik: [docs/GUVENLIK.md](docs/GUVENLIK.md).

**Geliştirme (Python 3.13):**

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m streamlit run app.py
```

Taşınabilir paket: `python tools/paketle.py`. Örnek dosyalar `ornekler/` klasöründe; panelde "Tanıtım için örnek işletme ekle" düğmesi uydurma verilerle dolu bir işletme açar.

## Yapı

| Dosya | Görev |
|---|---|
| `src/radar/ingest.py`, `ubl.py` | Dosyaları standart tabloya çevirme: fatura listesi, cari hesap ekstresi / muavin, banka ekstresi, çek, borç, gider; UBL-TR e-fatura |
| `src/radar/reconcile.py` | Banka tahsilatı ile fatura eşleştirme (birebir, sonra FIFO ve kısmi) |
| `src/radar/features.py`, `model.py` | Sızıntısız müşteri özellikleri; LightGBM kantil modeli ve aralık kalibrasyonu |
| `src/radar/simulate.py`, `fx.py` | Korelasyonlu Monte Carlo kasa simülasyonu; kur belirsizliği (ECB kur geçmişi, konformal genişletme) |
| `src/radar/pipeline.py` | Uçtan uca akış, geri testler ve basit kıyas yöntemleri |
| `src/radar/actions.py`, `mailer.py` | Önceliklendirme, mesaj taslakları, TTK m.1530 hesapları; onaylanan taslağın kullanıcının hesabından gönderimi |
| `src/radar/store.py`, `access.py` | Kalıcı kayıt (SQLite), işlem kaydı, AES-256-GCM şifreli yedek; panel parolası |
| `src/radar/pilot.py`, `anonymize.py` | Pilot kayıtları, çevrimiçi izleme, pilot raporu; takma adlı veri paketi |
| `src/radar/validation.py`, `lab.py`, `open_data.py`, `standards.py` | Doğrulama çerçevesi ve senaryo laboratuvarı |
| `src/radar/ui/` | Streamlit paneli: veri katmanı, özet ve üç sekme (kasa, tahsilat, tahmin doğruluğu) |
| `app.py` | Panelin giriş noktası ve kenar çubuğu |
| `tests/` | 93 test; panel, Streamlit AppTest ile uçtan uca çizilerek sınanır |

Tasarım gerekçeleri: [docs/ARASTIRMA.md](docs/ARASTIRMA.md). Rakip incelemesi: [docs/RAKIPLER.md](docs/RAKIPLER.md), [docs/FARKLILASMA_ANALIZI.md](docs/FARKLILASMA_ANALIZI.md). Senaryo laboratuvarı: [docs/LAB_RAPORU.md](docs/LAB_RAPORU.md). Üçüncü taraf lisansları ve veri kaynakları: [docs/LISANSLAR.md](docs/LISANSLAR.md).

**Veri notu:** Kaggle ve UCI veri setleri depoda yoktur ve yeniden dağıtılmaz. TCMB sektör tablosu, ticari kullanımı TCMB'nin yazılı iznine bağlı olduğu için depoda yoktur; tablo yoksa sektör karşılaştırması gösterilmez.

**Lisans:** Tüm hakları saklıdır; kod inceleme için açıktır, izinsiz kullanılamaz ([LICENSE](LICENSE)).
