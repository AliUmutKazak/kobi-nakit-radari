# Güvenlik Gözden Geçirmesi

Tarih: 14 Ekim 2026. Kapsam: panelin bu bilgisayarda tek kullanıcıyla çalıştırıldığı mevcut sürüm. Çok kullanıcılı, internette yayınlanan bir sürüm ayrı bir inceleme gerektirir (aşağıda "Henüz ele alınmayanlar").

## Bulunan ve düzeltilen açıklar

| # | Bulgu | Nasıl doğrulandı | Düzeltme |
|---|---|---|---|
| 1 | Panel bilgisayarın bütün ağ arayüzlerinden erişime açıktı (0.0.0.0 ve ::). Aynı ağdaki biri adresi bilirse şirketin alacak verilerini görebilirdi. | Panel çalışırken dinlenen adresler listelendi. | `.streamlit/config.toml` ile yalnızca 127.0.0.1. Yeniden denendi: localhost yanıt veriyor, ağ IP'si bağlantıyı reddediyor. |
| 2 | Streamlit varsayılan olarak kullanım istatistiği gönderiyordu. | `streamlit config show` çıktısı. | `gatherUsageStats = false`. |
| 3 | Veritabanı proje klasöründeydi; proje klasörü OneDrive'da olduğu için müşteri adı, telefonu ve e-postası buluta eşitlenecekti (KVKK açısından yurt dışına aktarım sorusu doğurur). | Klasör yolu. | Varsayılan yer artık `%LOCALAPPDATA%\KobiRadar\radar.db` (eşitlenmeyen yerel klasör). Panel yeri kenar çubuğunda gösteriyor. `RADAR_DB` ortam değişkeniyle değiştirilebilir. |
| 4 | e-Fatura XML'i Python'un standart ayrıştırıcısıyla okunuyordu; kötü niyetli bir XML varlık genişletmesiyle belleği tüketebilir. | Test: iç içe varlık içeren XML. | `defusedxml`; böyle bir dosya reddediliyor. |
| 5 | E-posta konusuna satır sonu girerse ek başlık (ör. gizli alıcı) eklenebilirdi. | Test: konuya "\nBcc: ..." eklendi. | Başlıklar tek satıra indiriliyor; test gizli alıcı oluşmadığını doğruluyor. |
| 6 | Veritabanı tablo adı kontrolü `assert` ile yapılıyordu; Python iyileştirme kipinde (-O) `assert` çalışmaz. | Kod okuma. | Açık kontrol ve hata. |
| 7 | Paket sürümleri sabit değildi; her kurulum farklı sürüm çekebilirdi. | `requirements.txt`. | Sürümler sabitlendi. |
| 8 | Başlatıcı, Streamlit'in ilk çalıştırmada siyah pencerede sorduğu e-posta sorusuna takılıyordu: yeni bir bilgisayarda panel hiç açılmıyordu. | Kimlik dosyası geçici olarak kaldırılıp eski ayarla başlatıldı: 25 saniyede açılmadı, süreç soruda bekledi. | Sunucu soru sormayan kipte başlıyor; tarayıcıyı başlatıcı, sunucu hazır olunca kendisi açıyor. Aynı koşulda 8 saniyede açıldı. Panel açıkken ikinci tıklama yeni sunucu başlatmıyor, açık olanı gösteriyor. |

## Gözden geçirilip sorun görülmeyenler

- **E-posta parolası:** yalnızca açık oturumun belleğinde tutuluyor, veritabanına ya da diske yazılmıyor. Bağlantı TLS ile kuruluyor (465 portunda doğrudan, diğerlerinde STARTTLS), sertifika doğrulaması açık.
- **SQL:** değerler parametreyle geçiyor; tablo adları sabit bir listeden.
- **ECB kur güncellemesi (21.10.2026):** yalnızca kullanıcı düğmeye basınca, yalnızca sabit ECB adresinden (HTTPS) indirme yapılır. Dosya boyutu sınırlıdır (5 MB); arşivde tek CSV beklenir; tablo kullanılmadan önce biçim, uzunluk, pozitif değer, tarih sırası ve olağan dışı sıçrama bakımından denetlenir; sorun varsa paketteki kurlarla devam edilir. İşletme verisi gönderilmez.
- **WhatsApp bağlantısı:** telefon numarası yalnızca rakamlardan oluşacak şekilde temizleniyor, metin URL kodlamasından geçiyor. Gönderme işini kullanıcı kendi WhatsApp'ında yapıyor; panel hiçbir şey göndermiyor.
- **Ekranda gösterilen dosya içeriği:** HTML olarak işlenmiyor (Streamlit tabloları ve metin bileşenleri kaçış uyguluyor; `unsafe_allow_html` kullanılmıyor).
- **Silme:** yüklenen tabloları silmek için ayrıca "Eminim" onayı gerekiyor; olay günlüğü silinmiyor.

## KVKK Kişisel Veri Güvenliği Rehberi ile karşılaştırma (16 Ekim 2026)

Referans: Kişisel Verileri Koruma Kurumu, *Kişisel Veri Güvenliği Rehberi (Teknik ve İdari Tedbirler)*, KVKK Yayınları No: 72, Nisan 2025, Tablo 4.1 ve 4.2. Uygulama işletmenin kendi bilgisayarında çalışır; veri sorumlusu işletmedir. Aşağıdaki tablo uygulamanın hangi tedbiri sağladığını, hangisinin işletmenin kendi sorumluluğunda kaldığını gösterir.

**Teknik tedbirler (Tablo 4.1)**

| Tedbir | Durum |
|---|---|
| Yetki matrisi, yetki kontrol | Tek kullanıcılı yerel uygulama; Windows hesabı birinci kontrol. Ortak bilgisayar için isteğe bağlı panel parolası (scrypt özeti, `radar/access.py`). Rol bazlı yetki yok (çok kullanıcılı sürümde gerekir). |
| Erişim logları, log kayıtları | Var. Yükleme, geri alma, silme, takma adlı paket, pilot raporu, şifreli yedek, geri yükleme, panel girişi ve başarısız giriş `audit_log` tablosuna Windows kullanıcı adıyla yazılır; uygulama içinden silinemez; panelde görüntülenir. |
| Kullanıcı hesap yönetimi | Panel parolası ayarlanır/kaldırılır (mevcut parola gerekir). |
| Ağ güvenliği | Panel yalnızca 127.0.0.1'i dinler (bulgu 1); dışarıya veri göndermez (kullanım istatistiği kapalı). |
| Uygulama güvenliği | defusedxml, e-posta başlığı temizleme, parametreli SQL, HTML işlenmeyen tablolar; sürümleri sabit bağımlılıklar. |
| Şifreleme | Yedek AES-256-GCM (parolayla). Veritabanı dosyası şifresiz: disk şifrelemesi (BitLocker / Cihaz şifrelemesi) pilot için ön koşul. Takma adlı paket taşınırken parolalı arşiv (AES-256) zorunlu. |
| Sızma testi | Yapılmadı. Bağımlılık açık taraması yapıldı: `pip-audit` (16 Ekim 2026) cryptography 44.0.2'de 10 bilinen açık buldu; 50.0.2'ye yükseltildi; tüm ortamda bilinen açık kalmadı. Her sürümden önce tekrarlanır. |
| Saldırı tespit ve önleme, güvenlik duvarı, anti-virüs | İşletmenin bilgisayarının sorumluluğunda (Windows Defender ve güvenlik duvarı açık olmalı). |
| Veri maskeleme | Paylaşımda takma adlandırma (HMAC-SHA256; ad, VKN/TCKN, fatura no), e-posta ve telefon silme, banka açıklamasının yeniden yazılması. Pilot raporunda "adları gizle" seçeneği. |
| Veri kaybı önleme | Yüklemede önceki sürüm saklanır (geri alınabilir); geri yüklemeden önce mevcut veri ayrı dosyaya kopyalanır. |
| Yedekleme | Şifreli yedek ve doğrulanmış geri yükleme. |
| Silme, yok etme, anonim hâle getirme | "Tabloları sil": `secure_delete` ve `VACUUM` ile silinen veri dosyadan da sıfırlanır (testle doğrulandı). "İşletmeyi tamamen sil": bütün tablolar ve geri yükleme öncesi kopyalar kalıcı silinir. Paylaşılan pakette tam anonimlik iddia edilmez (takma adlandırma). |
| Anahtar yönetimi | Takma ad anahtarı yalnızca yerel klasörde; işletme başına türetilir; paylaşılmaz. Yedek parolası hiçbir yere yazılmaz. |

**İdari tedbirler (Tablo 4.2)** — işletmenin (veri sorumlusunun) sorumluluğunda. Uygulamayla birlikte taslaklar verilir: kişisel veri işleme envanteri ve saklama-imha politikası (iç belge; avukat onayı bekliyor), veri işleyen sözleşmesi ve gizlilik taahhüdü (pilot protokolü Ek A). VERBİS kaydı, çalışan eğitimi, iç denetim ve kriz/ihlal bildirimi süreçleri işletmenin kendi kurumsal süreçleridir.

## Henüz ele alınmayanlar

- **Veritabanı dosyası şifreli değil.** Disk şifrelemesi (BitLocker ya da Cihaz Şifrelemesi) ön koşuldur (Ayarlar → Gizlilik ve güvenlik → Cihaz şifrelemesi). Çok kullanıcılı sürümde veritabanı şifrelemesi gerekir.
- **Rol bazlı yetki ve sızma testi yok.** Çok kullanıcılı ya da internette yayınlanan sürümden önce zorunludur.
- **Excel dosyaları:** `openpyxl` ile okunuyor; kullanıcının kendi dosyaları olduğu için risk düşük, ama dışarıdan gelen Excel için ayrı bir sınırlama yok (yükleme boyutu 50 MB ile sınırlı).
- **İnternette yayın:** panel şu an yalnızca yerel kullanım için tasarlandı. Sunucuya taşınırsa HTTPS, kimlik doğrulama, oturum yönetimi, KVKK m.12 kapsamında veri işleyen sözleşmesi ve yurt dışına aktarım değerlendirmesi gerekir.

Yedekleme (15 Ekim 2026): "Diğer ayarlar → Şifreli yedek" yedeği AES-256-GCM ile şifreler; anahtar parolandan scrypt ile türetilir (n = 2^15, r = 8, p = 1; tuz ve nonce her yedekte rastgele). GCM, dosya değiştirilirse geri yüklemeyi reddeder. Kütüphane: cryptography (PyCA) 50.0.2.
