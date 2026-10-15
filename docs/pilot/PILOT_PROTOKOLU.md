# Pilot Protokolü

Sürüm 1.0 — 15 Ekim 2026. Bu belge, ilk gerçek işletme verisi görülmeden yazılmıştır. Başarı ölçütleri ve eşikler pilot sırasında değiştirilmez; değişiklik gerekirse yeni sürüm numarasıyla, gerekçesiyle ve hangi verinin görüldüğü belirtilerek yapılır.

## 1. Amaç

Açık verilerdeki sonuç (docs/DOGRULAMA.md) şudur: tahmin, "vadesinde ödenir" varsayımından her durumda daha isabetli, "müşteri her zamanki kadar geç öder" yöntemiyle ise başa baş. Pilot iki soruya cevap arar:

1. Bu sonuç Türk KOBİ'lerinin verisinde, **tahmin anında kimsenin bilmediği** gelecek tahsilatlarda tekrarlanıyor mu?
2. Yönetici, haftalık kasa ve tahsilat kararlarında aracı gerçekten kullanıyor mu?

Pilot, "aracın tahsilatı artırdığını" göstermeye çalışmaz. Kontrol grubu olmadan bu nedensellik iddiası kurulamaz (bkz. 6).

## 2. Kimler katılır

| Ölçüt | Alt sınır | Neden |
|---|---|---|
| Fatura geçmişi | 12 ay | Geri test ve mevsimsellik için; 10 aydan az geçmişte rapor isabet ölçemez |
| Vadesi dolmuş fatura | 300 | Altında öğrenen model yerine müşteri medyanı kullanılır (model.MIN_LGBM_ROWS) |
| Müşteri sayısı | 10 | Daha azında tek bir müşterinin gecikmesi kasayı belirler |
| Satış biçimi | Vadeli satış ağırlıklı | Peşin satış yapan işletmede tahmin edilecek alacak yoktur |
| Banka ekstresi | Tercihen | Ödeme tarihlerini faturalarla eşleştirmenin en güvenilir yolu |

Hedef: farklı sektörlerden 5–10 işletme. Mali müşavir aracılığıyla ulaşılan işletmeler tercih edilir: veri hazırlığını bilen biri vardır.

## 3. Veri akışı

1. İşletme ya da mali müşaviri, paneli **kendi bilgisayarında** açar ve dosyaları yükler (fatura listesi veya cari ekstre, banka ekstresi; varsa giderler, ödenecekler, çekler). Veri bu aşamada bilgisayardan çıkmaz.
2. Sol menü → "5. Pilot: anonim veri paketi" → "Anonim paketi hazırla". Zip içinde:
   - Müşteri unvanı ve VKN/TCKN, gizli bir anahtarla üretilmiş takma adlarla değişir (HMAC-SHA256). Aynı müşteri her ay aynı takma adı alır.
   - E-posta ve telefon silinir. Banka açıklamaları tümüyle yeniden yazılır; yalnızca eşleşen müşterinin takma adı ve fatura numarası kalır.
   - Gider kalemlerinden yalnızca genel kategori adları kalır (maaş, kira, SGK…); diğer her şey "Diğer" olur. Çeklerde keşideci adı silinir.
   - Tutar ve tarihler değişmez.
3. Paketi hazırlayan kişi zip'i açıp **gözle kontrol eder** (özellikle BENİ_OKU.txt'deki sayılar ve rastgele birkaç satır).
4. Paket, uçtan uca şifreli bir kanalla ya da parolalı arşivle (örneğin 7-Zip, AES-256) gönderilir; parola ayrı bir kanaldan iletilir. Şifresiz e-posta eki kullanılmaz.
5. Anahtar dosyası (%LOCALAPPDATA%\KobiRadar\anonim_anahtar.txt) **hiçbir zaman paylaşılmaz**. Kaybolursa sonraki aylarda takma adlar değişir; geçmiş paketle eşleştirme kopar.

**Sınır.** Bu yöntem takma adlandırmadır, tam anonimleştirme değildir: tutar ve tarih örüntüleri, dış bilgiyle birleştirildiğinde bir işletmeyi tanınabilir kılabilir. Müşterisi gerçek kişi olan işletmelerde (şahıs işletmesi unvanı kişi adı içerir) veri kişisel veri olmayı sürdürür. Hukuki çerçeve için 8. bölüme bakın.

## 4. Takvim

| Zaman | Yapılan |
|---|---|
| Hafta 0 | Kurulum. İlk pilot raporu: kendi geçmişinde geri test (tahmin geçmişte ne kadar tuttu). Bu rapor yalnızca bilgi içindir; başarı ölçütü değildir. |
| Hafta 1–13 | Her pazartesi: güncel dosyalar yüklenir, "Tahmin doğruluğu" sekmesinden pilot raporu indirilir ve **değiştirilmeden** saklanır (dosya adı tarihlidir). Haftalık kayıt formu doldurulur (Ek B). |
| Hafta 17 | Son raporun 30 günlük ufku dolar. Güncel fatura dosyasıyla bütün raporlar puanlanır (Ek C). |
| Hafta 18 | Sonuçlar, başarılı ya da başarısız, docs/DOGRULAMA.md'ye işlenir. |

## 5. Önceden kayıtlı ölçütler

Her pilot raporu "İleriye dönük kayıt" bölümünde, o gün açık faturalardan önümüzdeki 14 ve 30 günde tahsil edilecek tutarı dört yöntemle yazar: model (kötümser / beklenen / iyimser) ve üç basit yöntem:

- **Vadesinde öder:** vadesi ufuk içinde olan ya da geçmiş her fatura ödenir. KOBİ'lerin çoğunun fiilen yaptığı varsayım.
- **Müşteri medyanı:** her fatura, müşterinin geçmiş gecikme medyanı kadar geç ödenir.
- **Tahsilat oranı:** bir önceki aynı uzunluktaki dönemde, dönem başında açık alacağın yüzde kaçı tahsil edildiyse bugünkü açık alacağın da o kadarı tahsil edilir. Muhasebede yaygın yaklaşım.

İlk iki basit yöntem, vadesi çoktan geçmiş faturaları "yakında ödenir" sayar; şüpheli alacağı çok olan işletmede kolay yenilir. Sentetik şirketlerde bu iki yöntemin sapması %80–450 çıktı. Bu yüzden B1, modeli **medyan ve oran yöntemlerinin iyisiyle** karşılaştırır. Yeni satışlar bu kayda dahil değildir; yalnızca o gün var olan faturalar ölçülür. Rapor, sayıları makinece okunur biçimde de içerir.

Sapma: bir işletmenin bütün haftalık kayıtlarında mutlak hataların toplamı / gerçekleşen tahsilat toplamı. (Tek tek hafta yüzdeleri, tahsilatın az olduğu haftalarda anlamsız büyür.)

| Kod | Ölçüt | Eşik | Dayanak |
|---|---|---|---|
| **B1** (birincil) | Kasa isabeti, 14 ve 30 gün, işletme başına | Model sapması < "vadesinde öder" sapması **ve** ≤ min("müşteri medyanı", "tahsilat oranı") sapması + 2 puan | Açık verilerde model ile medyan farkı 0,1–0,8 puan. 2 puan, "başa baş"ı ölçüm gürültüsünden ayırmak için seçildi. Kodda: pilot.passes_b1, pilot.NONINFERIORITY_POINTS |
| **B2** | Bant kalibrasyonu | Gerçekleşen tahsilatın kötümser–iyimser bant içinde kaldığı kayıt oranı ≥ %70 (hedef %80) | Açık verilerde kasa bandı %62–100. Kodda: pilot.COVERAGE_FLOOR |
| **B3** | Kullanım | 13 haftanın en az 10'unda rapor alınmış; tahsilat listesinden en az 10 işlem kaydı (arama, mesaj, söz) | Kullanılmayan araç, isabetli olsa da değer üretmez |
| **B4** | Karar desteği (nitel) | Haftalık formda "Bu hafta bir kasa ya da tahsilat kararında rapora baktım" cevabı en az 6 hafta "evet" | Ürünün iddiası tahmin değil, karar desteğidir |

**Karar kuralı.**
- Pilot işletmelerinin çoğunda B1 ve B2 sağlanırsa: mevcut yöntem korunur.
- B1, en iyi basit yöntem karşısında çoğunlukta sağlanmazsa: ürün varsayılan olarak o basit yönteme geçer ve öğrenen model yalnızca kendi geri testinde açıkça önde olan işletmelerde açılır. Bu durum belgede ve tanıtımda açıkça yazılır.
- B1, "vadesinde öder" karşısında da sağlanmazsa: kasa tahmini özelliği yeniden tasarlanana kadar "deneysel" etiketi taşır.
- B2 sağlanmazsa: bant genişliği kalibrasyonu (pipeline.calibrate) pilot verisiyle değil, yeni bir geri test tasarımıyla yeniden ele alınır; pilot verisine göre ayar yapılıp aynı veriyle başarı ilan edilmez.
- B3 veya B4 sağlanmazsa: sorun teknik değil kullanım sorunudur; görüşmelerle nedeni araştırılır (bkz. ikincil ölçütler).

**Raporlama.** Bütün işletmelerin bütün kayıtları raporlanır; işletme çıkarılacaksa (örneğin veri gönderimi kesildi) nedeni yazılır. Başarısız sonuçlar, reddedilen yöntemler gibi DOGRULAMA.md'de kalır.

## 6. İkincil ölçütler (yalnızca betimleyici)

- Vadesi geçmiş alacağın toplam alacağa oranı ve ortalama tahsilat süresi (DSO), pilot öncesi 13 hafta ile pilot dönemi arasında.
- Gönderilen mesajlardan sonra 14 gün içinde ödenme oranı (panel bunu "Gönderilen mesajların sonucu" bölümünde hesaplar).
- Eşleşmeyen banka tahsilatı oranı (veri kalitesi).
- Pilot sonu görüşmesi: en çok ve en az işe yarayan bölüm, güvenilmeyen sayı, eksik özellik.

Bu ölçütlerde değişim görülse bile araca bağlanamaz: mevsim, faiz ortamı ve müşteri karışımı aynı dönemde değişir. Nedensel bir etki iddiası ancak rastgele seçilmiş karşılaştırma grubuyla (örneğin müşterilerin yarısına öncelik listesi uygulanır, yarısına uygulanmaz) kurulabilir; bu, pilotun ikinci aşamasına bırakılmıştır.

## 7. Durdurma ve güvenlik kuralları

- Anonim pakette gerçek bir unvan, VKN, telefon ya da e-posta görülürse: o paket silinir, işletmeye bildirilir, hata düzeltilip test eklenene kadar paket alınmaz.
- Müşteriye yanlış tutar ya da yanlış kişiye mesaj gönderildiği öğrenilirse: mesaj özelliği o işletmede kapatılır, neden araştırılır. Panel mesajları kendiliğinden göndermez; her mesaj kullanıcının onayıyla çıkar.
- İşletme pilottan istediği an çıkabilir; o güne kadar gönderdiği paketler 7 gün içinde silinir.

## 8. Roller ve hukuki çerçeve (avukat incelemesi gerekir)

Aşağıdaki değerlendirme hukuki görüş değildir; pilot başlamadan önce avukat tarafından incelenmesi gereken noktaları sıralar.

- **Kişisel veri mi?** 6698 sayılı KVKK kişisel veriyi gerçek kişiler için tanımlar; tüzel kişi unvanı ve VKN kişisel veri sayılmaz. Şahıs işletmesi unvanı, TCKN ve gerçek kişi müşteriler ise kişisel veridir. Takma adlandırılmış veri, anahtar başkasında olsa da kişisel veri olmayı sürdürebilir (KVKK Kurumu'nun silme, yok etme ve anonim hâle getirme rehberi; AB'de GDPR 26. gerekçe).
- **Rol dağılımı.** İşletme, müşteri verisinin veri sorumlusudur. Pakete erişen proje ekibinin veri işleyen mi yoksa ayrı bir veri sorumlusu mu olduğu, paylaşımın amacına göre belirlenmelidir; buna göre veri işleme sözleşmesi ya da veri paylaşım sözleşmesi gerekir.
- **Hukuki sebep.** İşletmenin kendi müşteri verisini pilot için paylaşmasının KVKK m.5 kapsamındaki dayanağı (meşru menfaat ya da açık rıza) ve aydınlatma yükümlülüğü (m.10).
- **Yurt dışına aktarım.** Paketler yalnızca Türkiye'deki bilgisayarlarda işlenir; bulut depolama kullanılacaksa sunucu yeri ve KVKK m.9 şartları ayrıca değerlendirilir.
- **Mali müşavir.** Mali müşavirin müşterisine ait veriyi üçüncü kişiyle paylaşması, 3568 sayılı Kanun kapsamındaki sır saklama yükümlülüğü bakımından ancak işletmenin yazılı onayıyla yapılmalıdır.
- **Ticari sır.** Satış tutarları ve müşteri yoğunlaşması işletme için ticari sır niteliğinde olabilir; gizlilik yükümlülüğü sözleşmeye yazılmalıdır.

## Ek A. Bilgilendirme ve veri paylaşım onayı — TASLAK

> **Bu metin taslaktır. Avukat incelemesi ve onayı olmadan kullanılmamalıdır.** Köşeli parantezli yerler doldurulacaktır.

**KOBİ Nakit Akışı Radarı Pilot Çalışması — Bilgilendirme ve Onay**

[İşletme unvanı] ("İşletme"), [proje sahibi adı/unvanı] ("Proje") tarafından yürütülen pilot çalışmaya katılmayı kabul eder.

1. **Amaç.** Pilotun amacı, kasa ve tahsilat tahmininin İşletme'nin verisinde ne kadar isabetli olduğunu ölçmek ve aracı geliştirmektir. Veriler başka bir amaçla kullanılmaz, satılmaz, üçüncü kişilerle paylaşılmaz.
2. **Paylaşılan veri.** Fatura numarası, takma adlandırılmış müşteri kimliği, fatura ve vade tarihi, tutar, ödeme tarihi; banka tahsilatlarının tarih ve tutarı; isteğe bağlı olarak gider, borç ve çek tarih ve tutarları. Müşteri unvanı, vergi/kimlik numarası, telefon ve e-posta paylaşılmaz; bunlar İşletme'nin bilgisayarında takma adlarla değiştirilir.
3. **Anahtar.** Takma adları üreten anahtar yalnızca İşletme'de kalır. Proje, takma addan gerçek müşteriye ulaşmaya çalışmaz.
4. **Saklama ve silme.** Veriler [Türkiye'de bulunan, şifreli diskte] saklanır; pilotun bitiminden itibaren en geç [30] gün içinde ya da İşletme'nin talebi üzerine [7] gün içinde silinir ve silindiği yazılı olarak bildirilir.
5. **Sonuçların kullanımı.** Pilot sonuçları, İşletme'nin adı ve tanınmasını sağlayacak bilgi verilmeden, yalnızca toplu ve istatistiksel olarak yayımlanabilir.
6. **Gizlilik.** Proje, İşletme'nin verisini ticari sır olarak korur; erişimi pilotta çalışan kişilerle sınırlar.
7. **Gönüllülük.** Katılım gönüllüdür; İşletme dilediği an gerekçe göstermeden ayrılabilir.
8. **Sorumluluk.** Araç karar desteği sağlar; kasa ve tahsilat kararları İşletme'ye aittir. Araç İşletme adına mesaj göndermez.
9. **Müşterilere karşı yükümlülük.** İşletme, müşteri verisinin bu amaçla takma adlandırılarak paylaşılmasının kendi aydınlatma ve hukuki sebep yükümlülükleriyle uyumlu olduğunu [avukat görüşüne göre düzenlenecek].

İşletme adına: [ad soyad, unvan, tarih, imza] — Proje adına: [ad soyad, tarih, imza] — Mali müşavir (varsa): [ad soyad, oda sicil no, tarih, imza]

## Ek B. Haftalık kayıt formu

| Soru | Cevap |
|---|---|
| Tarih (pazartesi) | |
| Pilot raporu indirildi ve saklandı mı? | Evet / Hayır |
| Bu hafta bir kasa ya da tahsilat kararında rapora baktım. | Evet / Hayır |
| Evet ise hangi karar? (örn. ödemeyi erteledim, müşteriyi aradım, kredi limitine baktım) | |
| Raporda yanlış ya da şüpheli bulduğum sayı | |
| Plan dışı büyük gelir/gider (tahminin bilmediği) | |

Plan dışı kalemler not edilir çünkü kasa tahmininin değil, tahsilat tahmininin puanlandığı B1'i etkilemezler; ama yöneticinin rapora güvenini etkilerler.

## Ek C. Değerlendirme

Hafta 17'de, işletmenin güncel fatura dosyası (anonim paketteki faturalar.csv) ve saklanan raporlar bir klasörde toplanır:

```
python -m radar.pilot <raporlar_klasoru> <guncel_faturalar.csv>
```

Komut her kayıt için gerçekleşen tahsilatı hesaplar, ufku dolmamış kayıtları atlar ve 14/30 gün için B1 ile B2'nin sağlanıp sağlanmadığını yazar. Gerçekleşen tahsilat, tahmin günü açık olup ufuk içinde ödenen faturaların tutarıdır; kısmi ödemeler fatura tutarı üzerinden sayılır (yaklaşım; kısmi ödemesi çok olan işletmede ayrıca belirtilir).
