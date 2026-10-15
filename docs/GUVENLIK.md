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
- **WhatsApp bağlantısı:** telefon numarası yalnızca rakamlardan oluşacak şekilde temizleniyor, metin URL kodlamasından geçiyor. Gönderme işini kullanıcı kendi WhatsApp'ında yapıyor; panel hiçbir şey göndermiyor.
- **Ekranda gösterilen dosya içeriği:** HTML olarak işlenmiyor (Streamlit tabloları ve metin bileşenleri kaçış uyguluyor; `unsafe_allow_html` kullanılmıyor).
- **Silme:** yüklenen tabloları silmek için ayrıca "Eminim" onayı gerekiyor; olay günlüğü silinmiyor.

## Henüz ele alınmayanlar

- **Veritabanı şifreli değil.** Bilgisayara erişimi olan herkes dosyayı okuyabilir. Tek kullanıcılı yerel kullanımda Windows hesabının parolası ve disk şifrelemesi (BitLocker ya da Cihaz Şifrelemesi) korur. **Pilot için ön koşul:** veriyi hazırlayan bilgisayarda disk şifrelemesi açık olmalı (Ayarlar → Gizlilik ve güvenlik → Cihaz şifrelemesi). Çok kullanıcılı sürümde veritabanı şifrelemesi gerekir.
- **Yedek artık şifreli (15 Ekim 2026).** "Diğer ayarlar → Şifreli yedek" yedeği AES-256-GCM ile şifreler; anahtar kullanıcının parolasından scrypt ile türetilir (n = 2^15, r = 8, p = 1; tuz ve nonce her yedekte rastgele). GCM, dosya değiştirilirse geri yüklemeyi reddeder. Parola saklanmaz; unutulursa yedek açılamaz. Geri yüklemeden önce mevcut veri aynı klasöre ayrı bir dosya olarak kopyalanır ve yüklenen dosyanın KOBİ Radar veritabanı olduğu doğrulanır. Kütüphane: cryptography (PyCA).
- **Kullanıcı girişi yok.** Panel bu bilgisayarda açan herkese açık.
- **Yedekleme yok.** Veritabanı dosyası elle kopyalanmalı.
- **Excel dosyaları:** `openpyxl` ile okunuyor; kullanıcının kendi dosyaları olduğu için risk düşük, ama dışarıdan gelen Excel için ayrı bir sınırlama yok (yükleme boyutu 50 MB ile sınırlı).
- **İnternette yayın:** panel şu an yalnızca yerel kullanım için tasarlandı. Sunucuya taşınırsa HTTPS, kimlik doğrulama, oturum yönetimi, KVKK m.12 kapsamında veri işleyen sözleşmesi ve Türkiye'de barındırma gerekir.
