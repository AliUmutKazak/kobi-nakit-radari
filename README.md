# KOBİ Nakit Akışı Radarı

Açık faturaların ne zaman tahsil edileceğini olasılıksal olarak tahmin eder, 90 günlük kasa bandını (P10 / P50 / P90) çıkarır ve açığı kapatmaya en çok yarayacak faturalar için onay bekleyen mesaj taslakları üretir.

Şu an sentetik veriyle çalışır. Tasarım kararlarının gerekçesi: [docs/ARASTIRMA.md](docs/ARASTIRMA.md). Rakip karşılaştırması: [docs/RAKIPLER.md](docs/RAKIPLER.md). Doğrulama sonuçları: [docs/DOGRULAMA.md](docs/DOGRULAMA.md).

## Kullanım

İşletme sahibi için: [docs/KULLANIM_KILAVUZU.md](docs/KULLANIM_KILAVUZU.md). Dağıtım için taşınabilir paket: `python tools/paketle.py` komutu `dist/KobiRadar-<tarih>.zip` üretir (python.org'un gömülebilir Python'u ve paketler içinde; kullanıcının Python kurması gerekmez, ~150 MB). Kısaca: Python 3.13'ü kurun, `KOBI_Radar_Baslat.bat` dosyasına çift tıklayın. İlk açılışta gerekli paketler kurulur; panel tarayıcıda http://localhost:8501 adresinde açılır ve yalnızca bu bilgisayardan erişilebilir.

Güvenlik ayarları ve gözden geçirme: [docs/GUVENLIK.md](docs/GUVENLIK.md). Veriler `%LOCALAPPDATA%\KobiRadar\radar.db` dosyasında saklanır (OneDrive gibi eşitlenen klasörlerin dışında).

## Geliştirme

Sanal ortam, Windows yol uzunluğu sınırına takılmamak için kısa bir yolda durur:

```bash
python -m venv C:\Users\HP\.venvs\kobi-radar
C:\Users\HP\.venvs\kobi-radar\Scripts\python -m pip install -r requirements.txt
C:\Users\HP\.venvs\kobi-radar\Scripts\python -m pytest -q
C:\Users\HP\.venvs\kobi-radar\Scripts\python run_demo.py
C:\Users\HP\.venvs\kobi-radar\Scripts\python run_validation.py 48
```

## Modüller

| Dosya | Görev |
|---|---|
| `src/radar/synthetic.py` | Sentetik fatura verisi, kasa planı, örnek UBL-TR üretimi |
| `src/radar/ingest.py` | CSV / Excel / UBL-TR dosyalarını, banka ekstresini ve cari hesap ekstresini / muavin defteri standart tabloya çevirme (Türkçe başlık ve sayı biçimi, başlık satırı tespiti) |
| `ornekler/` | Kendi verini yükleme akışını denemek için örnek dosyalar |
| `src/radar/ubl.py` | UBL-TR e-fatura ayrıştırıcı (vade alanı boşsa yedek kurallar) |
| `src/radar/reconcile.py` | Banka tahsilatı ile fatura eşleştirme (birebir, sonra FIFO ve kısmi) |
| `src/radar/features.py` | Sızıntısız müşteri geçmişi özellikleri |
| `src/radar/model.py` | LightGBM kantil modeli ve aralık kalibrasyonu |
| `src/radar/simulate.py` | Korelasyonlu Monte Carlo kasa simülasyonu |
| `src/radar/actions.py` | Metrikler, önceliklendirme, mesaj taslakları |
| `src/radar/store.py` | Kalıcı kayıt (SQLite): yüklenen tablolar, ayarlar, itiraz / ödeme sözü / mesaj günlüğü |
| `src/radar/mailer.py` | Onaylanan taslağın kullanıcının e-posta hesabından gönderilmesi |
| `src/radar/validation.py` | 192 sentetik şirkette kalibrasyon çalışması (`run_validation.py`) |
| `src/radar/pipeline.py` | Uçtan uca akış ve geri testler |
| `app.py` | Streamlit paneli |

## Bilinen sınırlar

- İki herkese açık gerçek veri setinde (IBM, Payment Date) model, "müşteri her zamanki kadar geç öder" basit yöntemiyle başa baş; "vadesinde ödenir" varsayımını yeniyor (docs/DOGRULAMA.md). Bir Türk KOBİ'sinin verisiyle henüz sınanmadı.
- Sentetik veride model, "müşterinin geçmiş medyanı" tahminini nokta isabetinde ancak yakalıyor; katkısı bandın kalibrasyonunda.
- Tahsilat geri testinde P50, gerçekleşenin %1–9 üzerinde; bant içinde kalsa da iyimser bir sapma var.
- Ödenecek faturalar, döviz ve canlı banka/e-fatura bağlantısı yok. Çeklerde keşideci bazlı risk yok.
- Koddaki yasal ve piyasa parametreleri (gecikme faizi, tahsil gideri, çek karşılıksızlık oranı) ikincil kaynaklardan alındı; birincil kaynaktan teyit edilmeli (bkz. docs/ARASTIRMA.md).
- Dosya başlıkları tanınmazsa panel elle sütun eşleştirme ister ve seçimi hatırlar; muhasebe programlarına özel hazır şablon yok.
- Ödenecek faturalar ayrı dosyayla girer ve kasa çıkışına çevrilir; vadesi geçmiş borç ertesi gün ödenecek sayılır. Borç tarafında model yok: ödeme tarihini kullanıcı belirler.
- Dövizli faturalar kullanıcının girdiği kurla TL'ye çevrilir; kur değişimi tahmin bandına dahil değildir. İade faturaları müşterinin en eski açık faturalarından düşülür.
- E-posta, kullanıcının kendi SMTP hesabı üzerinden ve yalnızca düğmeye basınca gönderilir; gerçek bir sunucuyla denenmedi (sahte sunucuyla test edildi). WhatsApp gönderimi yok.
- Veriler yalnızca bu bilgisayarda, şifrelenmemiş bir dosyada saklanır; kullanıcı girişi, yetki ve yedekleme yok.
