# KOBİ Nakit Akışı Radarı

Açık faturaların ne zaman tahsil edileceğini olasılıksal olarak tahmin eder, 90 günlük kasa bandını (kötümser P10 / orta P50 / iyimser P90) çıkarır, "güvenle harcanabilir tutarı" gösterir ve açığı kapatmaya en çok yarayacak faturalar için onay bekleyen mesaj taslakları üretir.

**Durum (20.10.2026): pilot öncesi.** Türk KOBİ verisiyle henüz sınanmadı. Model, senaryo laboratuvarı ve istatistik çerçevesi pilot verisi gelene kadar donduruldu (aşağıda "Kabul kuralı"). Pilot: [docs/pilot/PILOT_PROTOKOLU.md](docs/pilot/PILOT_PROTOKOLU.md).

## Kurulum (işletme bilgisayarı)

Tek yol taşınabilir pakettir. Python kurmak gerekmez.
1. `KobiRadar-<sürüm>.zip` dosyasını açın.
2. `KOBI_Radar.bat` dosyasına çift tıklayın.

Panel tarayıcıda http://localhost:8501 adresinde açılır ve yalnızca o bilgisayardan erişilebilir. Veriler `%LOCALAPPDATA%\KobiRadar\radar.db` dosyasında saklanır (OneDrive gibi eşitlenen klasörlerin dışında). Pilot için ön koşul: disk şifrelemesi (BitLocker ya da Windows "Cihaz şifrelemesi"). Ortak bilgisayarda isteğe bağlı panel parolası kullanılır. Güvenlik: [docs/GUVENLIK.md](docs/GUVENLIK.md). İşletme sahibi için: [docs/KULLANIM_KILAVUZU.md](docs/KULLANIM_KILAVUZU.md).

## Güncel durum

| Alan | Durum | Ayrıntı |
|---|---|---|
| Gerçek Türk KOBİ verisiyle doğrulama | **Yok** | Pilotla yapılacak. Bütün sonuçlar sentetik veri, senaryo laboratuvarı ve yabancı açık veri setleriyle (IBM, Payment Date, UCI Online Retail II) ya da ECB kurlarıyla. |
| Modelin basit yöntemlere üstünlüğü | **Belirsiz** | Açık veride "müşteri her zamanki kadar geç öder" yöntemiyle başa baş; 14 günde önde, IBM 30 günde "son dönemin tahsilat oranı" önde. Panel her işletmede modeli basit yöntemlerle geriye dönük karşılaştırır: hızlı geri test ve pilot için son 52 haftalık "Aşama 0" testi (Diebold-Mariano, Basel, Kupiec). Model bir ufukta gerideyse o ufkun tahsilatı için en isabetli basit yöntemin sayısı panelin üstünde gösterilir. [DOGRULAMA.md](docs/DOGRULAMA.md) |
| Kasa bandı kalibrasyonu | Laboratuvarda kabul aralığında | Geçerli sonuç: laboratuvar sürüm 6 sınavı, 240 işletme. Kötümser uç aşımı %7, iyimser %10; Basel yeşil, Kupiec iki uçta geçiyor. Pilottaki çevrimiçi izleme (protokol 1.5) sıralı laboratuvarda %10,7 / %8,9. Eski sürümlerin sonuçları: [LAB_RAPORU.md](docs/LAB_RAPORU.md). |
| Eksiye düşme olasılığı | Sentetikte ortaya sıkışık | Yüksek riskte gerçek risk gösterilenden yüksek çıktı (%80 → %92). Panel %50 ve üzerini "en az" diye gösterir; karar için kötümser çizgi esas alınır. Yeniden ayar (izotonik) gerçek sonuç verisi gerektirir, pilot sonrasına kayıtlı. |
| Veri alma | Dosya ile | Excel/CSV fatura listesi, UBL-TR e-fatura XML, cari hesap ekstresi / muavin, banka ekstresi (giriş/çıkış yönü otomatik), çek portföyü, ödenecek faturalar, gider planı. Tanınmayan başlıkta elle sütun eşleştirme; seçim hatırlanır. Muhasebe programlarına özel hazır şablon ve canlı banka / e-fatura bağlantısı yok. |
| Çek ve senet | Var | Portföydeki çekler vadesinde, karşılıksız çıkma olasılığıyla (TBB oranı) sayılır. Cirolanan, iskontoya verilen ve "riskli" işaretlenen çekler sayılmaz. Çekle ödeme alışkanlığı işletmenin kendi kayıtlarından öğrenilir. Keşideci bazlı istatistiksel risk yok. |
| Giderler ve borçlar | Var | Gider planı, aylık sabit giderler (vergi takvimi ve resmî tatiller dahil), ödenecek faturalar. Gider planı banka geçmişiyle karşılaştırılır, eksik kısım "plan dışı ödeme" olarak eklenir. Giderlerin dalgalanması banda girer. Borç ödeme tarihi kullanıcının verdiği vadedir; vadesi geçmiş borç ertesi gün ödenmiş sayılır. |
| Döviz | Var | Dövizli alacak, çek, borç ve gider girilen kurla TL'ye çevrilir. Kur belirsizliği ECB kur geçmişinden banda girer; her dövizde kasa aleyhine olan taraf esas alınır. ECB'nin son kurları panelde gösterilir; kurlar isteğe bağlı olarak internetten güncellenir. [HATA_AZALTMA_ANALIZI.md](docs/HATA_AZALTMA_ANALIZI.md), bölüm 7 |
| Tahsilat aksiyonu | Var, gerçek sunucuyla denenmedi | Mesaj taslağı; WhatsApp'ta yazılmış hâlde açma; panoya kopyalama; kullanıcının kendi SMTP hesabıyla e-posta (yalnızca sahte sunucuyla test edildi). Gönderen kimliği (MERSİS / VKN) eksikse gönderme kapalı. |
| Pilot ölçümü | Hazır (protokol 1.7) | Birincil ölçüt B1, önceden kayıtlı marjlı eşdeğerlik kararıdır (FDA 2016): kanıt yoksa sonuç "kanıtlanamadı" olur, "geçti" sayılmaz. Marj işletmenin Aşama 0 verisinden gelir. Haftalık kayıt kendiliğinden alınır. Kapanış kasası için kasa tutarı o gün girilmelidir; ekstrede bakiye varsa "Ekstre bakiyesini kasa tutarına yaz" düğmesi bunu tek tıka indirir. Pilot puanlaması kayıt alınmayan haftaları ve kasası güncellenmemiş kayıtları sayıp gösterir. Ödeme tarihi bilinmeyen kısmi ödemeler ölçüme girmez. |
| Yeni satış tahmini | Yabancı açık veride sınandı | UCI Online Retail II ile: geçen yılın aynı dönemi işletmenin geçmişinde anlamlı biçimde daha isabetliyse o kullanılır (90 günlük sapma %37'den %8'e). Bir yıldan kısa geçmişte mevsimsellik bilinemez, panel uyarır. Pilotta B1 yalnızca açık faturaları ölçer; yeni satış ayrıca betimlenir. |
| Hukuk | Açık sorular var | Doğrulanan hükümler ve avukata sorulacaklar: [docs/hukuk/MEVZUAT_KONTROLU.md](docs/hukuk/MEVZUAT_KONTROLU.md). TCMB sektör verisinin ticari kullanımı TCMB'nin yazılı iznine bağlı; pakete varsayılan olarak konmaz. |
| Güvenlik | Pilot için yeterli | Yerel çalışma, isteğe bağlı panel parolası, işlem kaydı, AES-256-GCM şifreli yedek. Veritabanı dosyası şifresiz (disk şifrelemesi ön koşul). Çok kullanıcılı yetki yok. |

## Kabul kuralı (model ve özellik dondurma)

- Pilot verisi gelene kadar modele, laboratuvara ve istatistik çerçevesine yeni sürüm, boyut ya da test eklenmez. İstisna: sonucu yalnızca daha ihtiyatlı yapan güvenlik düzeltmeleri.
- **Özellik dondurması (21.10.2026):** pilot başlayana kadar yeni özellik eklenmez. Yalnızca hata ve güvenlik düzeltmeleri ile bir pilot işletmesinin ya da mali müşavirin açıkça istediği şeyler yapılır.
- Bir uçtaki aşım oranı, örneklem büyüklüğü için Basel trafik ışığında yeşilse ve Kupiec testi geçiyorsa (p ≥ 0,05) o sonuç kabul edilir; ayar yapılmaz. Gerçek oran %10 olsa bile ölçülen oran örneklem küçükken %10'dan belirgin biçimde sapabilir. Basel yeşil bölgesinin üst sınırı (%10'luk uç, `standards.basel_zone`):

  | Gözlem sayısı | Yeşil bölgede en çok aşım |
  |---|---|
  | 35 | 6 (%17) |
  | 50 | 8 (%16) |
  | 100 | 14 (%14) |
  | 240 | 31 (%12,9) |
  | 1.000 | 115 (%11,5) |

- Bu oranlar bandın ne sıklıkla aşıldığını ölçer; kasa tahmininin yüzde hatası değildir.

## Geliştirme

Sanal ortam, Windows yol uzunluğu sınırına takılmamak için kısa bir yolda durur:

```bash
python -m venv C:\Users\HP\.venvs\kobi-radar
C:\Users\HP\.venvs\kobi-radar\Scripts\python -m pip install -r requirements.txt
C:\Users\HP\.venvs\kobi-radar\Scripts\python -m pytest -q
C:\Users\HP\.venvs\kobi-radar\Scripts\python tools/paketle.py
```

Tasarım gerekçeleri: [docs/ARASTIRMA.md](docs/ARASTIRMA.md). Rakipler: [docs/RAKIPLER.md](docs/RAKIPLER.md). Lisanslar ve veri kaynakları: [docs/LISANSLAR.md](docs/LISANSLAR.md).

## Modüller

| Dosya | Görev |
|---|---|
| `src/radar/ingest.py` | Dosyaları standart tabloya çevirme: fatura listesi, cari hesap ekstresi / muavin, banka ekstresi, çek, borç, gider; vergi takvimi ve resmî tatiller |
| `src/radar/ubl.py` | UBL-TR e-fatura ayrıştırıcı |
| `src/radar/reconcile.py` | Banka tahsilatı ile fatura eşleştirme (birebir, sonra FIFO ve kısmi) |
| `src/radar/features.py`, `model.py` | Sızıntısız müşteri özellikleri; LightGBM kantil modeli ve aralık kalibrasyonu |
| `src/radar/simulate.py` | Korelasyonlu Monte Carlo kasa simülasyonu |
| `src/radar/fx.py` | Kur belirsizliği (ECB kur geçmişi, konformal genişletme), kurların internetten güncellenmesi |
| `src/radar/pipeline.py` | Uçtan uca akış, geri testler ve basit kıyas yöntemleri |
| `src/radar/actions.py` | Metrikler, önceliklendirme, mesaj taslakları, TTK m.1530 hesapları |
| `src/radar/store.py`, `access.py` | Kalıcı kayıt (SQLite), işlem kaydı, şifreli yedek; panel parolası |
| `src/radar/mailer.py` | Onaylanan taslağın kullanıcının e-posta hesabından gönderilmesi |
| `src/radar/pilot.py`, `anonymize.py` | Pilot kayıtları, çevrimiçi izleme, pilot raporu; takma adlı veri paketi |
| `src/radar/validation.py`, `lab.py`, `open_data.py`, `standards.py` | Doğrulama çerçevesi (dondurulmuş) |
| `src/radar/synthetic.py`, `benchmark.py` | Sentetik veri; TCMB sektör karşılaştırması (izin gerektirir) |
| `app.py` | Streamlit paneli |
