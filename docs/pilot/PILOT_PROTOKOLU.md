# Pilot Protokolü

Sürüm 1.3 — 16 Ekim 2026. 1.1: Ek A hukuk müşavirliği taslağına göre güncellendi, Ek D eklendi. 1.2: bağımsız derin inceleme (15.10.2026) üzerine ölçüm tanımları kesinleştirildi. **1.3: kendi belirlediğimiz eşikler (B1'de +2 puan tolerans, B2'de %70 bant içi) kaldırıldı; yerlerine uluslararası ve Türkiye'de geçerli standart testler kondu (Basel Komitesi / BDDK geriye dönük test bölgeleri, Kupiec kapsama testi, Diebold-Mariano testi).** Bütün değişiklikler pilot verisi görülmeden yapıldı. Bu belge, ilk gerçek işletme verisi görülmeden yazılmıştır. Başarı ölçütleri pilot sırasında değiştirilmez; değişiklik gerekirse yeni sürüm numarasıyla, gerekçesiyle ve hangi verinin görüldüğü belirtilerek yapılır.

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
2. Sol menü → "5. Pilot: takma adlı veri paketi" → "Takma adlı paketi hazırla". Zip içinde:
   - Müşteri unvanı ve VKN/TCKN, gizli bir anahtarla üretilmiş takma adlarla değişir (HMAC-SHA256). Aynı müşteri her ay aynı takma adı alır.
   - Fatura numaraları da takma numaralarla değişir (fatura serisi işletmeyi, cari ekstredeki numarasız satırların kimliği müşteriyi ele verebilir).
   - E-posta ve telefon silinir. Banka açıklamaları tümüyle yeniden yazılır; yalnızca eşleşen müşterinin takma adı ve fatura numarası kalır.
   - Gider kalemlerinden yalnızca genel kategori adları kalır (maaş, kira, SGK…); diğer her şey "Diğer" olur. Çeklerde keşideci adı silinir.
   - Tutar ve tarihler değişmez.
   - "Pilota katılıyorum" işaretliyse uygulamanın haftalık aldığı ileriye dönük tahmin özetleri (yalnızca tarih, ufuk ve tutar) pilot_kayitlari.csv olarak eklenir.
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

Her pilot raporu "İleriye dönük kayıt" bölümünde, o gün açık faturalardan önümüzdeki 14 ve 30 günde tahsil edilecek tutarı dört yöntemle yazar: model (kötümser P10 / orta P50 / iyimser P90) ve üç basit yöntem:

- **Vadesinde öder:** vadesi ufuk içinde olan ya da geçmiş her fatura ödenir. KOBİ'lerin çoğunun fiilen yaptığı varsayım.
- **Müşteri medyanı:** her fatura, müşterinin geçmiş gecikme medyanı kadar geç ödenir.
- **Tahsilat oranı:** bir önceki aynı uzunluktaki dönemde, dönem başında açık alacağın yüzde kaçı tahsil edildiyse bugünkü açık alacağın da o kadarı tahsil edilir. Muhasebede yaygın yaklaşım.

İlk iki basit yöntem, vadesi çoktan geçmiş faturaları "yakında ödenir" sayar; şüpheli alacağı çok olan işletmede kolay yenilir. Sentetik şirketlerde bu iki yöntemin sapması %80–450 çıktı. Bu yüzden B1, modeli **medyan ve oran yöntemlerinin iyisiyle** karşılaştırır. Yeni satışlar bu kayda dahil değildir; yalnızca o gün var olan faturalar ölçülür. Rapor, sayıları makinece okunur biçimde de içerir.

**Gerçekleşen tahsilat (hedef A).** Tahmin günü açık olan faturalara ufuk içinde gelen **tahsilat olaylarının** toplamı. Olaylar banka ekstresinin faturalara dağıtılmasından gelir; kısmi ödeme kendi tarih ve tutarıyla sayılır (fatura tutarı değil). Banka kaydı olmayan ama dosyada ödendiği görünen faturada bankadan gelmeyen kısım ödeme tarihinde tek olaydır. Ödeme tarihi bilinmeyen kısmi ödemeler ölçüme girmez. Tahsil edilemez olarak kaydedilen fatura açık alacaktan çıkar, ödenmiş sayılmaz.

**Sapma.** Bir işletmenin bütün haftalık kayıtlarında mutlak hataların toplamı / gerçekleşen tahsilat toplamı (pay ve payda ayrıca raporlanır). Tek tek hafta yüzdeleri, tahsilatın az olduğu haftalarda anlamsız büyür; tahsilatı sıfır olan hafta paydaya sıfır katar, payda hatası olduğu gibi girer.

**Kayıt künyesi.** Her haftalık kayıt değiştirilemez biçimde şunlarla saklanır: kesim tarihi, verideki son hareket, veri dosyalarının özeti (hash), yöntem (LightGBM ya da basit yöntem), kod sürümü, banka eşleşme oranı, kapsam (hangi kaynaklar dahil) ve o günkü kasa. Sonradan yüklenen dosya eski kaydı değiştirmez.

**Eşleşme kapısı.** Banka tahsilatlarının tutarca %80'inden azı faturalarla eşleşmişse o haftanın kaydı "uyarılı"dır ve B1/B2 hesabına girmez; sayısı ayrıca raporlanır.

**Bağımlılık.** Haftalık kayıtların 14 ve 30 günlük ufukları üst üste biner; aynı tahsilat birden çok kayıtta yer alır, kayıtlar bağımsız gözlem değildir. Diebold-Mariano testinde kayıp farkının ufuk/7 haftaya kadar otokorelasyonu varyansa katılır (Newey-West türü; Harvey, Leybourne ve Newbold 1997 küçük örneklem düzeltmesi). Model ile en iyi güçlü basit yöntem arasındaki sapma farkı için ayrıca blok bootstrap ile %90 aralık verilir (yorum için; karara girmez).

**Bant.** Bant içi oranın yanında bandın ortalama genişliği (P90 − P10, gerçekleşene oranla) ve aralık skoru (Gneiting ve Raftery 2007, alfa 0,2) raporlanır: yalnızca kapsama, gereksiz geniş bandı ödüllendirir.

| Kod | Ölçüt | Eşik | Dayanak |
|---|---|---|---|
| **B1** (birincil) | Tahsilat isabeti, 14 ve 30 gün, işletme başına | **Diebold-Mariano testi** (1995), Harvey-Leybourne-Newbold (1997) düzeltmesiyle, %5 anlamlılık, mutlak hata kaybı: model, iki güçlü basit yöntemden (müşteri medyanı, tahsilat oranı) toplamda iyi olandan ve "vadesinde öder"den istatistiksel olarak anlamlı biçimde kötü olmamalı. Sonuç "üstün" (anlamlı biçimde iyi), "eşdeğer" ya da "geride" olarak raporlanır; "geride" değilse geçer. Test hesaplanamazsa (4'ten az kayıt) "değerlendirilemedi". | İki tahminin isabetini karşılaştırmada tahmin literatürünün standart testi (Uluslararası Tahminciler Enstitüsü yayınları, M yarışmaları). Kendi toleransımız yoktur. Kodda: pilot.accuracy_test, standards.diebold_mariano |
| **B2** | Bant kalibrasyonu (P10–P90) | (a) Kötümser uç (gerçekleşen < P10) aşım sayısı **Basel Komitesi trafik ışığına** göre **yeşil bölgede** olmalı: doğru modelde "bu kadar ya da daha az aşım" olasılığı %95'in altında (BCBS 1996; Türkiye'de BDDK, Risk Ölçüm Modelleri ile Piyasa Riskinin Hesaplanmasına... İlişkin Tebliğ, RG 03.11.2006/26335, aynı bölge sınırları). (b) **Kupiec (1995) kapsama testi** %5 anlamlılıkta ne merkezi %80 aralık ne alt ne üst uç (%10) için reddetmemeli: bant fazla dar da fazla geniş de olmamalı. | Bölge sınırları gözlem sayısına göre binom dağılımından hesaplanır (Basel belgesinin öngördüğü gibi); küçük işletmenin az sayıdaki haftalık kaydına da uygulanır. Kodda: standards.basel_zone, standards.kupiec_pof, standards.passes |
| **B3** | Kullanım | 13 haftanın en az 10'unda rapor alınmış; tahsilat listesinden en az 10 işlem kaydı (arama, mesaj, söz) | Kullanılmayan araç, isabetli olsa da değer üretmez |
| **B4** | Karar desteği (nitel) | Haftalık formda "Bu hafta bir kasa ya da tahsilat kararında rapora baktım" cevabı en az 6 hafta "evet" | Ürünün iddiası tahmin değil, karar desteğidir |

**Karar kuralı.**
- Pilot işletmelerinin çoğunda B1 ve B2 sağlanırsa: mevcut yöntem korunur.
- B1, en iyi basit yöntem karşısında çoğunlukta sağlanmazsa: ürün varsayılan olarak o basit yönteme geçer ve öğrenen model yalnızca kendi geri testinde açıkça önde olan işletmelerde açılır. Bu durum belgede ve tanıtımda açıkça yazılır.
- B1, "vadesinde öder" karşısında da sağlanmazsa: kasa tahmini özelliği yeniden tasarlanana kadar "deneysel" etiketi taşır.
- B2 sağlanmazsa: kötümser uç sarı/kırmızı bölgedeyse (risk küçümseniyor) kasa grafiğinde uyarı gösterilir ve bant kalibrasyonu pilot verisiyle değil, yeni bir geri test tasarımıyla yeniden ele alınır; pilot verisine göre ayar yapılıp aynı veriyle başarı ilan edilmez. Yalnızca bant gereğinden genişse (Kupiec, az aşım) güvenlik açısından acil değildir; sonraki sürümde düzeltilir.
- B3 veya B4 sağlanmazsa: sorun teknik değil kullanım sorunudur; görüşmelerle nedeni araştırılır (bkz. ikincil ölçütler).

**Raporlama.** Bütün işletmelerin bütün kayıtları raporlanır; işletme çıkarılacaksa (örneğin veri gönderimi kesildi) nedeni yazılır. Toplu sonucun yanında en iyi ve en kötü işletme ayrıca verilir. Başarısız sonuçlar, reddedilen yöntemler gibi DOGRULAMA.md'de kalır. 5–10 işletmede "çoğunluk" bir fizibilite sonucudur; pazar ya da genel geçerlilik kanıtı olarak sunulmaz. Sonuçlar üç ayrı başlıkta raporlanır: fizibilite (veri hazırlanabildi mi), tahmin kanıtı (B1, B2), ürün kullanımı (B3, B4).

## 6. İkincil ölçütler (yalnızca betimleyici)

- Vadesi geçmiş alacağın toplam alacağa oranı ve ortalama tahsilat süresi (DSO), pilot öncesi 13 hafta ile pilot dönemi arasında.
- Gönderilen mesajlardan sonra 14 gün içinde ödenme oranı (panel bunu "Gönderilen mesajların sonucu" bölümünde hesaplar).
- Eşleşmeyen banka tahsilatı oranı (veri kalitesi).
- **Hedef B, kapanış kasası:** her kayıtta açılış kasasından başlayıp bilinen giderler, borçlar, çekler, açık faturalar ve (açıksa) yeni satışlarla 7, 14 ve 28 gün sonraki kasa (P10/P50/P90) yazılır. Gerçekleşen, ufkun sonuna ±3 gün içindeki kayıtta kullanıcının o gün girdiği kasa ve banka toplamıdır (yalnızca o gün güncellenmiş bakiyeler kullanılır). Karşılaştırma: "kasa değişmez". Hedef A'dan ayrı raporlanır; toplam nakit isabeti tahsilat isabetiyle karıştırılmaz. Kapsam dışı kaynaklar (ör. gider dosyası yok) kayıt künyesinde yazılıdır.
- Pilot sonu görüşmesi: en çok ve en az işe yarayan bölüm, güvenilmeyen sayı, eksik özellik.

Bu ölçütlerde değişim görülse bile araca bağlanamaz: mevsim, faiz ortamı ve müşteri karışımı aynı dönemde değişir. Nedensel bir etki iddiası ancak rastgele seçilmiş karşılaştırma grubuyla (örneğin müşterilerin yarısına öncelik listesi uygulanır, yarısına uygulanmaz) kurulabilir; bu, pilotun ikinci aşamasına bırakılmıştır.

## 7. Durdurma ve güvenlik kuralları

- Takma adlı pakette gerçek bir unvan, VKN, telefon ya da e-posta görülürse: o paket silinir, işletmeye bildirilir, hata düzeltilip test eklenene kadar paket alınmaz.
- Müşteriye yanlış tutar ya da yanlış kişiye mesaj gönderildiği öğrenilirse: mesaj özelliği o işletmede kapatılır, neden araştırılır. Panel mesajları kendiliğinden göndermez; her mesaj kullanıcının onayıyla çıkar.
- İşletme pilottan istediği an çıkabilir; o güne kadar gönderdiği paketler 7 gün içinde silinir.

## 8. Roller ve hukuki çerçeve (avukat incelemesi gerekir)

Aşağıdaki değerlendirme hukuki görüş değildir; pilot başlamadan önce avukat tarafından incelenmesi gereken noktaları sıralar.

15 Ekim 2026'da gelen hukuk müşavirliği taslağı (imzasız) Ek A'yı veri işleme sözleşmesi hükümleriyle birleştirdi. Ek A o taslak esas alınarak güncellendi; taslaktan farklılaşan ve teyit istenen yerler Ek A'da "AVUKAT NOTU" ile işaretlidir. Mesaj şablonlarına ilişkin şerhler (sabit faiz oranı ve tutar yazılmaması, TTK m. 18/3 uyarısının her taslakta sabit gösterilmesi) uygulamaya işlendi.

- **Kişisel veri mi?** 6698 sayılı KVKK kişisel veriyi gerçek kişiler için tanımlar; tüzel kişi unvanı ve VKN kişisel veri sayılmaz. Şahıs işletmesi unvanı, TCKN ve gerçek kişi müşteriler ise kişisel veridir. Takma adlandırılmış veri, anahtar başkasında olsa da kişisel veri olmayı sürdürebilir (KVKK Kurumu'nun silme, yok etme ve anonim hâle getirme rehberi; AB'de GDPR 26. gerekçe).
- **Rol dağılımı.** İşletme, müşteri verisinin veri sorumlusudur. Pakete erişen proje ekibinin veri işleyen mi yoksa ayrı bir veri sorumlusu mu olduğu, paylaşımın amacına göre belirlenmelidir; buna göre veri işleme sözleşmesi ya da veri paylaşım sözleşmesi gerekir.
- **Hukuki sebep.** İşletmenin kendi müşteri verisini pilot için paylaşmasının KVKK m.5 kapsamındaki dayanağı (meşru menfaat ya da açık rıza) ve aydınlatma yükümlülüğü (m.10).
- **Yurt dışına aktarım.** Paketler yalnızca Türkiye'deki bilgisayarlarda işlenir; bulut depolama kullanılacaksa sunucu yeri ve KVKK m.9 şartları ayrıca değerlendirilir.
- **Mali müşavir.** Mali müşavirin müşterisine ait veriyi üçüncü kişiyle paylaşması, 3568 sayılı Kanun kapsamındaki sır saklama yükümlülüğü bakımından ancak işletmenin yazılı onayıyla yapılmalıdır.
- **Ticari sır.** Satış tutarları ve müşteri yoğunlaşması işletme için ticari sır niteliğinde olabilir; gizlilik yükümlülüğü sözleşmeye yazılmalıdır.

## Ek A. Pilot çalışması veri işleme, gizlilik ve muvafakat protokolü — TASLAK

> **Bu metin taslaktır; avukat onayı ve imzası olmadan kullanılmamalıdır.** 15 Ekim 2026'da hukuk müşavirliği taslağı (Belge 2) esas alınarak hazırlandı. "AVUKAT NOTU" ile işaretli yerler, o taslağa göre yapılan değişiklikler ya da avukatın teyit etmesi istenen noktalardır. Köşeli parantezli yerler doldurulacaktır.

**EK A — KOBİ NAKİT AKIŞI RADARI PİLOT ÇALIŞMASI, VERİ İŞLEME, GİZLİLİK VE MUVAFAKAT PROTOKOLÜ**

1. **Taraflar ve KVKK rol dağılımı.** İşbu Protokol; bir tarafta [İşletme unvanı ve VKN] ("İşletme" — 6698 sayılı KVKK kapsamında veri sorumlusu), diğer tarafta [Proje sahibi adı soyadı / unvanı ve TCKN/VKN] ("Proje" — KVKK m. 3/1-ğ kapsamında veri işleyen) ve veri hazırlama sürecine aracılık etmesi hâlinde [Mali müşavir adı soyadı ve oda sicil no] ("Mali Müşavir") arasında [GG/AA/2026] tarihinde akdedilmiştir.

2. **Amaç, talimat ve veri işleme sınırı.** İşletme, Proje'ye paylaşılan verileri yalnızca şu amaçlarla işleme talimatı verir: (a) 90 günlük kasa ve tahsilat tahmininin İşletme'nin verisinde ne kadar isabetli olduğunu ölçmek ve İşletme'ye doğruluk raporu sunmak; (b) bu ölçümlerin sonucuna göre aracın tahmin yöntemini düzeltmek. Proje, verileri bu talimat dışında hiçbir amaçla kullanamaz, satamaz ve üçüncü kişilerle paylaşamaz.
   > AVUKAT NOTU: Taslakta Proje "veri işleyen" olarak tanımlanırken amaç maddesi "aracı kalibre etmek" ve sonuçların yayımlanmasını da içeriyordu. Veri işleyen veriyi yalnızca veri sorumlusu adına ve onun talimatıyla işler; aracın geliştirilmesi Proje'nin kendi amacı sayılırsa Proje o işleme bakımından veri sorumlusu olabilir. Bu nedenle (b) bendi İşletme'nin açık talimatı olarak yazıldı. Bu çözümün yeterli olup olmadığı ya da Proje'nin bu kısım için ayrı veri sorumlusu olarak konumlandırılması gerekip gerekmediği değerlendirilmelidir.

3. **Yerel takma adlandırma akışı ve paylaşılan veri kapsamı.** Veriler, İşletme'nin veya Mali Müşavir'in kendi bilgisayarında çalışan masaüstü uygulamasıyla yerel olarak hazırlanır:
   - a) Müşteri unvanları, VKN/TCKN bilgileri ve fatura numaraları, yalnızca İşletme/Mali Müşavir bilgisayarında (%LOCALAPPDATA%\KobiRadar\anonim_anahtar.txt) kalan gizli bir anahtardan işletme başına türetilen anahtarla (HMAC-SHA256) takma adlara ve takma numaralara dönüştürülür.
   - b) Müşteri telefon numaraları, e-posta adresleri ve çeklerdeki keşideci adları tamamen silinir. Banka açıklamaları tümüyle yeniden yazılarak yalnızca eşleşen müşterinin takma adı ve takma fatura numarası bırakılır; gider kalemlerinden yalnızca genel kategori adları (maaş, kira, SGK vb.) korunur, diğer kalemler "Diğer" olarak işaretlenir.
   - c) Proje ile yalnızca şunlar paylaşılır: takma fatura numarası, takma müşteri kimliği, fatura/vade/ödeme tarihleri ve tutarları; banka, gider, borç ve çek kayıtlarının tarih ve tutarları; uygulamanın haftalık olarak kaydettiği ileriye dönük tahmin özetleri (tarih, ufuk ve tutar; kimlik bilgisi içermez).
     > AVUKAT NOTU: Haftalık tahmin özetleri taslaktan sonra uygulamaya eklendi; listeye bu nedenle girdi.
   - d) Hazırlanan paket gözle kontrol edildikten (BENİ_OKU.txt ve örnek satırlar) sonra uçtan uca şifreli bir kanalla veya parolalı arşivle (7-Zip, AES-256) gönderilir; parola ayrı bir kanaldan iletilir; şifresiz e-posta eki kullanılmaz.

4. **Anahtar güvenliği ve kimliği geri çözme yasağı.** Takma adları üreten anahtar dosyası yalnızca İşletme'de (veya yetkilendirdiği Mali Müşavir'de) kalır ve hiçbir zaman Proje ile paylaşılmaz. Proje, takma addan gerçek müşteriye veya kimliğe ulaşmaya çalışmamayı, başka veri kaynaklarıyla eşleştirme yapmamayı taahhüt eder.

5. **Saklama yeri, veri güvenliği ve imha (KVKK m. 9 ve m. 12).** Veriler yurt dışına aktarılmaz; yalnızca Türkiye sınırları içinde bulunan şifreli disklerde saklanır; bulut depolama kullanılmaz. Veriler, pilotun bitiminden itibaren en geç 30 (otuz) gün içinde ya da İşletme'nin talebi üzerine en geç 7 (yedi) gün içinde geri döndürülemez biçimde silinir ve silindiği İşletme'ye yazılı olarak bildirilir.

6. **Veri ihlali bildirimi.** Proje, verilerin yetkisiz kişilerce elde edildiğini veya buna ilişkin ciddi bir şüpheyi öğrendiği andan itibaren en geç 24 (yirmi dört) saat içinde İşletme'ye yazılı olarak bildirir; bildirimde olayın kapsamını, etkilenen verileri ve alınan önlemleri belirtir. KVKK m. 12/5 kapsamındaki Kurul'a ve ilgililere bildirim yükümlülüğü veri sorumlusu olarak İşletme'ye aittir; Proje bu süreçte gereken bilgi ve desteği sağlar.
   > AVUKAT NOTU: Hukuk müşavirliği taslağının 4. kontrol noktasında istenen 24 saatlik bildirim yükümlülüğü, Ek A metnine eklenmemişti; bu madde o şerh üzerine yazıldı.

7. **Alt işleyen ve erişim.** Proje, İşletme'nin önceden yazılı onayı olmadan verileri başka bir veri işleyene veya hizmet sağlayıcıya aktaramaz. Verilere yalnızca pilotta çalışan ve gizlilik taahhüdü vermiş kişiler erişebilir. İşletme, makul bir bildirimle Proje'den verilerin nasıl saklandığına ve silindiğine ilişkin bilgi ve belge isteyebilir.

8. **Ticari sır, gizlilik ve sonuçların kullanımı.** Proje, İşletme'nin satış tutarlarını ve müşteri yoğunlaşmasını içeren verilerini ticari sır olarak korur. İşletme, pilot sonuçlarının, İşletme'nin adı ve tanınmasını sağlayacak hiçbir bilgi verilmeden, yalnızca birden çok işletmenin toplu ve istatistiksel sonuçları olarak yayımlanmasına izin verir; tek bir işletmeye ait sayı yayımlanmaz.

9. **Hukuki sebep ve müşterilere karşı yükümlülük (KVKK m. 5 ve m. 10).** İşletme, muhasebe ve fatura kayıtlarındaki verilerin KVKK m. 5/2-c (sözleşmenin ifası) ve m. 5/2-f (veri sorumlusunun meşru menfaati) kapsamında hukuka uygun olarak işlendiğini ve bu verilerin takma adlandırılarak veri işleyen sıfatıyla Proje'ye aktarılmasının kendi aydınlatma ve hukuki sebep yükümlülükleriyle uyumlu olduğunu kabul ve beyan eder.

10. **Mali müşavir yetkilendirmesi (3568 sayılı Kanun).** İşletme, Mali Müşavir [ad soyad]'ı işbu Protokolün 3. maddesinde tanımlanan takma adlandırılmış veri paketini kendi bilgisayarında hazırlayarak Proje'ye iletmek üzere açıkça yetkilendirir; bu paylaşımın 3568 sayılı Kanun kapsamındaki sır saklama yükümlülüğüne aykırılık teşkil etmediğini yazılı olarak onaylar.
    > AVUKAT NOTU: Taslakta "3568 sayılı Kanun m. 43" atfı vardı; madde numarasının teyidi rica olunur.

11. **Gönüllülük ve sorumluluk sınırı.** Katılım gönüllüdür; İşletme dilediği an gerekçe göstermeden pilottan ayrılabilir. Araç yalnızca karar desteği sağlar; kasa ve tahsilat kararları tümüyle İşletme'ye aittir ve araç İşletme adına mesaj göndermez.

**İmzalar**

| İşletme adına (veri sorumlusu) | Proje adına (veri işleyen) | Mali müşavir (varsa) |
|---|---|---|
| Ad soyad: | Ad soyad: | Ad soyad: |
| Unvan: | Tarih: .... / .... / 2026 | Oda sicil no: |
| Tarih: .... / .... / 2026 | İmza: | Tarih: .... / .... / 2026 |
| İmza / kaşe: | | İmza / kaşe: |

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

Hafta 17'de, işletmenin güncel fatura ve banka dosyaları (takma adlı paketteki faturalar.csv ve ekstre.csv) ve saklanan raporlar bir klasörde toplanır:

```
python -m radar.pilot <raporlar_klasoru> <guncel_faturalar.csv> <guncel_ekstre.csv>
```

Komut ekstreyi faturalara dağıtıp tahsilat olaylarını çıkarır, her kayıt için gerçekleşen tahsilatı (kısmi ödemeler dahil) hesaplar, ufku dolmamış kayıtları atlar ve 14/30 gün için B1 ile B2'yi, bant genişliğini, aralık skorunu ve farkın %90 aralığını yazar. Panelde aynı hesap "Tahmin doğruluğu → Pilot kayıtları" bölümündedir ve kapanış kasası hedefini de içerir.

## Ek D. Mali müşavir için veri hazırlama föyü

Ek A imzalandıktan sonra veriyi hazırlayacak mali müşavire ya da ön muhasebe yetkilisine verilir.

**1. Uygun işletme.** En az 12 aylık düzenli satış faturası geçmişi (Paraşüt, Logo, Mikro, BizimHesap, Luca çıktısı ya da cari hesap ekstresi); en az 10 aktif cari müşteri; vadeli satış ağırlıklı. Hukuki sadelik için müşterileri ağırlıklı olarak şirket (Ltd. Şti., A.Ş.) olan işletmeler tercih edilir.

**2. Hazırlık adımları.**
- Ek A, İşletme, Proje ve Mali Müşavir arasında imzalanmadan paket hazırlanmaz.
- Uygulamayı kendi bilgisayarınızda açın; "Kendi verim" → "İşletme ekle" ile işletmeyi ekleyin; dosyaları yükleyin (fatura listesi ya da cari ekstre, banka ekstresi; varsa giderler, ödenecekler, çekler). Veriler bilgisayarınızdan çıkmaz.
- Sol menü → "5. Pilot: takma adlı veri paketi" → "Pilota katılıyorum" kutusunu işaretleyin; sonra "Takma adlı paketi hazırla".
- Zip'i açıp kontrol edin:
  - [ ] Müşteri unvanları ve VKN/TCKN'ler "Müşteri XXXXXX" biçiminde takma adlara dönüşmüş.
  - [ ] Fatura numaraları "ANO" ile başlayan takma numaralar.
  - [ ] Telefon, e-posta, çek keşideci adları ve banka açıklamalarındaki serbest metin yok.
  - [ ] BENİ_OKU.txt'deki fatura ve müşteri sayıları beklediğiniz gibi.
- Paketi 7-Zip (AES-256) ile parolalayın ya da uçtan uca şifreli bir kanaldan gönderin; parolayı başka bir kanaldan (telefon, SMS) iletin. Şifresiz e-posta eki kullanmayın.
- %LOCALAPPDATA%\KobiRadar\anonim_anahtar.txt dosyasını paylaşmayın ve silmeyin: sonraki aylarda aynı müşterinin aynı takma adı alması bu dosyaya bağlıdır. Bilgisayar değişecekse dosyayı güvenli biçimde taşıyın.

**3. Her hafta (13 hafta).** Pazartesi güncel fatura ve banka dosyalarını yükleyin ve tahmin tarihini bugün bırakarak paneli açın; haftalık kayıt kendiliğinden alınır. "Tahmin doğruluğu" sekmesinden pilot raporunu indirip saklayın; Ek B'deki iki soruyu cevaplayın.
