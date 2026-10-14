# KOBİ Nakit Akışı Radarı

Açık faturaların ne zaman tahsil edileceğini olasılıksal olarak tahmin eder, 90 günlük kasa bandını (P10 / P50 / P90) çıkarır ve açığı kapatmaya en çok yarayacak faturalar için onay bekleyen mesaj taslakları üretir.

Şu an sentetik veriyle çalışır. Tasarım kararlarının gerekçesi: [docs/ARASTIRMA.md](docs/ARASTIRMA.md). Rakip karşılaştırması: [docs/RAKIPLER.md](docs/RAKIPLER.md).

## Kurulum

Windows'ta yol uzunluğu sınırına takılmamak için sanal ortamı kısa bir yola kurun:

```bash
python -m venv C:\Users\HP\.venvs\kobi-radar
C:\Users\HP\.venvs\kobi-radar\Scripts\python -m pip install -r requirements.txt
```

## Çalıştırma

```bash
C:\Users\HP\.venvs\kobi-radar\Scripts\python run_demo.py
C:\Users\HP\.venvs\kobi-radar\Scripts\python -m streamlit run app.py
C:\Users\HP\.venvs\kobi-radar\Scripts\python -m pytest -q
```

## Modüller

| Dosya | Görev |
|---|---|
| `src/radar/synthetic.py` | Sentetik fatura verisi, kasa planı, örnek UBL-TR üretimi |
| `src/radar/ingest.py` | CSV / Excel / UBL-TR dosyalarını standart tabloya çevirme (Türkçe başlık ve sayı biçimi) |
| `ornekler/` | Kendi verini yükleme akışını denemek için örnek dosyalar |
| `src/radar/ubl.py` | UBL-TR e-fatura ayrıştırıcı (vade alanı boşsa yedek kurallar) |
| `src/radar/reconcile.py` | Banka tahsilatı ile fatura eşleştirme (birebir, sonra FIFO ve kısmi) |
| `src/radar/features.py` | Sızıntısız müşteri geçmişi özellikleri |
| `src/radar/model.py` | LightGBM kantil modeli ve aralık kalibrasyonu |
| `src/radar/simulate.py` | Korelasyonlu Monte Carlo kasa simülasyonu |
| `src/radar/actions.py` | Metrikler, önceliklendirme, mesaj taslakları |
| `src/radar/store.py` | Kalıcı kayıt (SQLite): yüklenen tablolar, ayarlar, itiraz / ödeme sözü / mesaj günlüğü |
| `src/radar/pipeline.py` | Uçtan uca akış ve geri testler |
| `app.py` | Streamlit paneli |

## Bilinen sınırlar

- Gerçek veriyle sınanmadı.
- Sentetik veride model, "müşterinin geçmiş medyanı" tahminini nokta isabetinde ancak yakalıyor; katkısı bandın kalibrasyonunda.
- Tahsilat geri testinde P50, gerçekleşenin %1–9 üzerinde; bant içinde kalsa da iyimser bir sapma var.
- Ödenecek faturalar, döviz ve canlı banka/e-fatura bağlantısı yok. Çeklerde keşideci bazlı risk yok.
- Koddaki yasal ve piyasa parametreleri (gecikme faizi, tahsil gideri, çek karşılıksızlık oranı) ikincil kaynaklardan alındı; birincil kaynaktan teyit edilmeli (bkz. docs/ARASTIRMA.md).
- Dosya başlıkları tanınmazsa panel elle sütun eşleştirme ister ve seçimi hatırlar; muhasebe programlarına özel hazır şablon yok.
- Mesaj gönderimi yok; taslak üretilir, kullanıcı kendi hesabından gönderip panelde kayda geçirir.
- Veriler `data/radar.db` dosyasında, yalnızca bu bilgisayarda saklanır; kullanıcı hesabı, yetki ve yedekleme yok.
