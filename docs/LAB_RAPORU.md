# Senaryo Laboratuvarı

Tarih: 18 Ekim 2026. Kod: `src/radar/lab.py`. Güncel sürüm 4 (16 boyut: çek, tahsilat kayıt gecikmesi, tahmin günü, kısmi ödeme ve eksik vade dahil). Ayrıntılı tablolar: sürüm 4 [geliştirme](lab/gelistirme_v4.md), [sınav](lab/sinav_v4.md); sürüm 3 [geliştirme](lab/gelistirme_v3.md), [geliştirme, kesim düzeltmesi kapalı](lab/gelistirme_v3_kesim_duzeltmesi_kapali.md), [sınav](lab/sinav_v3.md); sürüm 2 [geliştirme](lab/gelistirme_v2.md), [geliştirme, çek düzeltmesi kapalı](lab/gelistirme_v2_cek_duzeltmesi_kapali.md), [sınav](lab/sinav_v2.md); sürüm 1 [geliştirme](lab/gelistirme_v1.md), [sınav](lab/sinav_v1.md). Sınav koşuları kaydı: [lab/sinav_kaydi.csv](lab/sinav_kaydi.csv) (tohum 0: sürüm 1; tohum 1: sürüm 2; tohum 2: sürüm 3; tohum 3: sürüm 4).

## Sürüm 4: kısmi ödemeler ve eksik vade (18 Ekim 2026)

Aynı 120 geliştirme işletmesi üç koşulda eşleştirilerek koşuldu: temel, müşterilerin %40'ı faturalarını iki taksitte kapatıyor, faturaların %30'unda vade girilmemiş. Vadesi girilmemiş faturalara panel, TTK m.1530/4-a'daki gibi 30 gün vade verir.

| Koşul | Orta tahmin sapması, temele göre fark (aylık ciro) | Alt aşım | Üst aşım | Aralık skoru farkı |
|---|---|---|---|---|
| Temel | 0 | %7,5 | %12,5 | 0 |
| Kısmi ödeme (%40 müşteri) | −0,13 ± 0,02 | %5,8 | %16,7 | +0,25 ± 0,13 |
| Eksik vade (%30 fatura) | +0,002 ± 0,006 | %6,7 | %11,7 | +0,05 ± 0,05 |

- **Eksik vade** tahmini bozmuyor: model gecikmeyi aynı varsayılan vadeye göre öğreniyor; tutarlı bir kaydırma olarak kalıyor.
- **Kısmi ödeme** tahmini kötümser yapıyor. Panel kısmen ödenmiş açık faturada kalan tutarı doğru simüle ediyor. Ama henüz hiç ödenmemiş faturalarda ilk taksidin erken geleceğini bilmiyor, çünkü model ödemenin tamamını faturanın kapandığı günde öğreniyor. Hata güvenli yönde: kasa olduğundan boş görünüyor ve gereksiz alarm riski doğuyor.
- **Düzeltme planı:** Geçmiş taksit tarihlerinin saklanması gerekiyor. Banka ekstresi yüklendiğinde kısmi tahsilatlar olay olarak zaten çıkıyor (`reconcile.collection_events`); cari hesap yolunda ise yalnızca son ödeme günü tutuluyor. Taksit alışkanlığının (pay, ilk taksit oranı ve zamanı) müşteri bazında öğrenilmesi sonraki sürüme planlandı.

**Sınav (sürüm 4, tohum 3, 240 işletme, bir kez koşuldu):** alt aşım %6, üst %12 (Basel yeşil, Kupiec alt p = 0,043, üst p = 0,24), Spiegelhalter p = 0,23. Benjamini-Hochberg düzeltmesinden sonra zayıf bölge yok. Kısmi ödeme ve eksik vadenin saklı (geliştirme aralığı dışı) rejimleri de yeşil. Geliştirme kümesinde (son kod): alt %5, üst %12.

**Süreklilik gösteren bulgu.** Sürüm 3 ve 4'ün dört koşusunda da (geliştirme ve sınav) bant kötümser tarafa hafif kaymış: alt aşım %5–6, üst aşım %10–12. Basel/BDDK ölçütü açısından sorun değil, Kupiec "az aşım"ı verimsizlik olarak işaretliyor. Nedeni tasarımda: kötümser bant hiç daraltılmıyor. Ön kayıtlı düzeltme pilota bağlı. Pilot kayıtları biriktikçe çevrimiçi kantil izleme kötümser uçta da, işletmenin kendi gerçekleşmelerine göre ve alt sınırla birlikte daraltabilecek. Sınav verisiyle ayar yapılmadı.

## Sürüm 3: geç işlenen tahsilatlar, tahmin günü ve nominal büyüme (18 Ekim 2026)

**Laboratuvarın bulduğu kusur.** Panele yüklenen tahsilat kayıtları bugünden geride kalabilir. Bunun iki meşru nedeni var. Birincisi, kayıtlar yasal süre içinde ama günü gününe işlenmeyebilir (VUK m.219: muameleler deftere 10 günden fazla geciktirilmeden, muhasebe fişi ve bordroya dayanan kayıtlarda esas deftere en geç 45 günde işlenir). İkincisi, dosya muhasebe programından birkaç gün önce alınmış olabilir. E-faturalar ise zamanında düşer. Bu durumda gerçekte ödenmiş faturalar açık görünür, para hem bugünkü banka bakiyesinde hem "gelecek tahsilat"ta sayılır. Panelin eski uyarısı yalnızca verideki en son hareketin tarihine bakıyordu. Faturalar güncel olduğu için bu gecikmeyi göremiyordu.

**Ölçülen etki.** Tek bir senaryo tipinde (40 müşteri, tahmin ayın 1'inde) 7 günlük kayıt gecikmesi kötümser uç aşımını %7'den %43'e, 30 günlük gecikme %77'ye çıkardı. Laboratuvarın geniş senaryo uzayında etki daha küçük çıktı, çünkü model gecikmenin bir kısmını kendi kalibrasyonunda "müşteriler yavaşladı" diye emiyor. Aynı 120 işletmenin gecikmesiz ve 7–14 gün gecikmeli hâlleri eşleştirilerek ölçüldü:

| | Orta tahmin sapması (gecikmesiz hâle göre fark, aylık ciro) | Alt aşım | Aralık skoru |
|---|---|---|---|
| Gecikme yok | 0 | %4,2 | 1,94 |
| Gecikme var, düzeltme yok | +0,13 ± 0,02 (iyimser) | %8,3 | 2,03 |
| Gecikme var, kesim günü kayıtlardan tahmin edildi | −0,03 ± 0,02 | %4,2 | 1,95 |
| Gecikme var, kullanıcı gerçek tarihi girdi | −0,03 ± 0,02 | %4,2 | 1,90 |

**Çözüm.** Tahmin "tahsilatların işlendiği son gün"e göre kurulur: model, kalibrasyon ve gecikme eğrileri o güne göre hesaplanır. Simülasyonda o günden bugüne kadar ödenmiş çıkan faturaların parası bugünkü kasanın içinde sayılır, ikinci kez eklenmez (`pipeline.payments_cutoff`, `simulate(lag=...)`). Kullanıcı tarihi girebilir; girmezse tarih kayıtlardan tahmin edilir. Son tahsilattan bu yana geçen günlerde hiç tahsilat görülmeme olasılığı, işletmenin son 90 günlük tahsilat sıklığına göre %5'in altındaysa kayıtlar orada kesilmiş sayılır. Gecikme olmayan işletmede bu kural sonucu değiştirmedi (fark −0,002). Panel kesimi sarı bir uyarıyla bildirir.

**Laboratuvar tasarımındaki bir eksik giderildi.** Sürüm 1 ve 2'de bütün tahminler 1 Temmuz'da yapılıyordu. Sürüm 3'te tahmin günü yılın herhangi bir günü. Farklı işletmeleri ayın farklı günlerine göre karşılaştıran ilk bakış, ayın gününe bağlı bir sapma gösterdi. Aynı işletmeler ayın 3'ünde, 9'unda, 16'sında ve 24'ünde tahmin edilince bu desen kayboldu (sapma −0,20 ile −0,29 arasında, standart hata ~0,07).

**Denenip reddedilen: ödeme gününe oturtma.** Panel müşterinin "ayın 15'i / ay sonu" ödeme alışkanlığını zaten tanıyor (hatırlatma tarihi için). Simülasyonda ödemeyi en yakın ödeme gününe oturtmak 160 işletmede eşleştirilmiş olarak sınandı. Aralık skoru farkı +0,03 ± 0,03 çıktı, yani iyileşme yok; bant biraz daha kötümser oldu. Kapalı.

**Eklenen: satış tahmininde nominal büyüme.** Yeni satış tahmini geçmişin fiyatlarıyla yapılıyordu: "geçen yılın aynı dönemi" bir yıl, "son dönemin hızı" 90 gün öncesinin fiyatıyla. Yüksek enflasyonda bu, yeni satışları düşük gösterir. Laboratuvarda iyimser uç aşımı enflasyonla artıyordu: %0–17'de %7, %33–50'de %15. Tahminler artık işletmenin yıllık büyümesiyle, kaydırılan süre kadar ölçekleniyor (`pipeline.sales_growth`). Büyüme, son 26 haftanın satışının geçen yılın aynı 26 haftasına oranı. Oran pozitif kısımlı James–Stein kestiricisiyle gürültüsü oranında 1'e büzülür. Sonuçlar:
- Gerçek KOBİ verisinde (Online Retail II, düşük enflasyon) sonuçlar birebir aynı kaldı. Büzmeden uygulamak orada gürültü ekliyordu (90 günde %7,6'dan %9,0'a).
- Sentetik işletmelerde enflasyon yokken çarpan 1,00; %30'da 1,14–1,33; %50'de 1,36–1,56.
- Laboratuvardaki etkisi küçük ve anlamsız (aralık skoru −0,011 ± 0,019). Yönü her enflasyon diliminde doğru.
- Kötümser kaymanın ana nedeni enflasyon değil.

**Sınav (sürüm 3, tohum 2, 240 işletme, bir kez koşuldu):**

| Kesit | İşletme | Alt aşım | Üst aşım | Basel | Kupiec alt / üst p | Spiegelhalter p | Model − basit yöntem |
|---|---|---|---|---|---|---|---|
| Geliştirme (son kod) | 240 | %6 | %10 | yeşil | 0,025 / 1,00 | 0,57 | −1,44 ± 0,11 |
| **Sınav** | **240** | **%6** | **%12** | **yeşil** | **0,025 / 0,45** | **0,90** | **−1,42 ± 0,11** |

- Riskli uç Basel yeşil, olasılıklar kalibre. Model her kesitte basit yöntemlerden iyi.
- Saklı rejimde tek sarı kesit aşırı şok oldu (13 işletme, alt %31). Geliştirme tarafında 120 yeni işletmeyle incelendi: yeşil, alt aşım %5,8.
- **Açık kalan: kötümser uç gereğinden geniş.** Alt aşım %6; Kupiec iki yönlüdür ve "az aşım"ı da reddeder (p = 0,025). Bu bir tehlike değil, verimsizlik: gereksiz alarm riski. Basel/BDDK trafik ışığı yalnızca fazla aşımı cezalandırır ve yeşildir. Nedeni tasarımda: konformal genişletme ve çevrimiçi izleme kötümser bandı hiç daraltmaz (küçük işletmeyi korumak için ihtiyat ilkesi). Pilot verisi biriktikçe çevrimiçi izlemenin kötümser uçta da daraltabilmesi, ön kayıtlı kalibrasyon güncellemesinin konusu olacak.

## Sürüm 2: çekle ödeyen müşteriler (17 Ekim 2026)

**Laboratuvarın bulduğu kusur.** Türk KOBİ'lerinde müşterinin çekle ödemesi yaygındır. Cari hesapta çek alındığında fatura kapanır, para ise çekin vadesinde gelir. Sistem elde bulunan çekleri vadesinde sayıyordu. Ama henüz açık olan faturaların ve gelecek satışların da çekle ödenebileceğini hesaba katmıyordu. Bu yüzden çekle ödeyen müşterisi olan işletmede kasa olduğundan erken dolu görünüyordu.

**Kaynak durumu.** TCMB ve TBB karşılıksız çek oranını yayımlar (TBB Risk Merkezi, 2026'da tutar bazında %2,8–3,4). Çekle tahsilatın payını ya da çek vadesinin dağılımını veren kurumsal bir istatistik bulunamadı. Bu yüzden iki değer dışarıdan sabit alınmaz. Ürün, her işletmenin son bir yıllık cari hesap kayıtlarından öğrenir (`pipeline.cheque_habits`):
- müşteri bazında çekle kapanan fatura payı, işletme ortalamasına büzülerek,
- çek vadeleri (müşterinin kendi çekleri, yetmezse işletmenin bütün çekleri).

Simülasyonda çekle kapanan faturanın parası vadede gelir ve karşılıksız çıkabilir. Karşılıksızlık TBB oranıyla ve piyasa şokuyla birlikte modellenir. Cari hesap ekstresinde "çek", "müşteri çeki", "alınan çekler", "senet", "bono" açıklamalı alacak satırı faturayı kapatırsa, faturaya çekin vadesi yazılır. Laboratuvarda çekle ödeyen müşteri payı (%0–60, saklı %60–90) ve çek vadesi (30–120 gün, saklı 120–180) varsayımdır. Karşılıksızlık oranı TBB aralığından, saklı rejimde kriz düzeyinden (%3,4–7) çekilir.

**Etkisi (aynı 240 geliştirme işletmesi):**

| | Alt aşım (hedef %10) | Üst aşım | Basel | Orta tahmin sapması (aylık ciro) | Ortalama hata | Aralık skoru |
|---|---|---|---|---|---|---|
| Çek düzeltmesi kapalı | %40 | %3 | kırmızı (37 kesitin hepsinde sarı/kırmızı) | +0,56 | 0,83 | 4,15 |
| Çek düzeltmesi açık | %10 | %7 | yeşil | −0,06 | 0,46 | 2,19 |

Düzeltme olmadan model, basit "son 90 günün tahsilat hızı sürer" yönteminin (0,68) bile gerisindeydi. Düzeltmeyle bütün basit yöntemleri geçiyor ("müşteri her zamanki kadar geç öder": 1,61; "vadesinde ödenir": 2,23).

**Denenip reddedilen.** Geliştirme kümesinde çekle ödeme payı en yüksek kesitte (%40–60) alt aşım %14 çıktı. Akla gelen açıklama şuydu: gerçekte müşteri ya hep çekle ya hep havaleyle öder, simülasyon ise ödeme aracını fatura fatura bağımsız çekiyordu. Bu açıklama, bu bölgede yeni 120 işletmeyle sınandı. Müşteri bazında çekmek bandı gereğinden fazla genişletti (alt %7,5, üst %5,8) ve aralık skorunu kötüleştirdi (2,19'a karşı 2,11). Fatura bazında çekmek bu bölgede tam hedefteydi (alt %10,0). Yöntem değişmedi; %14 örneklem değişkenliğiydi.

**Sınav (sürüm 2, yeni tohumlar, 240 işletme, bir kez koşuldu):**

| Kesit | İşletme | Alt aşım | Üst aşım | Basel | Kupiec alt / üst p | Spiegelhalter p | Model − basit yöntem |
|---|---|---|---|---|---|---|---|
| Tümü | 240 | %8 | %6 | yeşil | 0,29 / 0,043 | 0,011 | −0,95 ± 0,08 |
| Geliştirme aralığı içi | 120 | %6 | %5 | yeşil | 0,13 / 0,054 | 0,09 | −1,03 ± 0,13 |

- Kötümser uç hedefte. Ortalama hata aylık cironun 0,37'si.
- İyimser uç ve eksiye düşme olasılıkları reddedildi: bant iyimser tarafta biraz geniş, olasılıklar ortaya sıkışık. Bu iki bulgu önceki çalışmalarla aynı yönde; pilot sonrası için ön kayıtlı kalibrasyon güncellemesinin konusu.
- Saklı rejimlerde iki küçük kesit sarı çıktı: aşırı hızlı kötüleşme (11 işletme, alt %36) ve kriz düzeyinde karşılıksızlık (13 işletme, alt %23). Geliştirme tarafında 120'şer yeni işletmeyle incelendi. İkisi de yeşil çıktı (alt aşım %5,8 ve %6,7; Kupiec p 0,13 ve 0,23). Kriz düzeyinde karşılıksızlıkta olasılık kalibrasyonu reddedildi (Spiegelhalter p = 0,016). Karşılıksızlık oranı TBB verisinden aylık güncellenmelidir. İşletmenin kendi karşılıksız çek geçmişinden öğrenmek, pilot verisiyle yapılacak bir sonraki adım.

## Amaç: ezber değil genelleme

Tahmin modeli hiçbir senaryoda eğitilmez. Her sentetik işletmede, gerçek kullanımdaki gibi, yalnızca o işletmenin tahmin gününe kadarki geçmişiyle kurulur ve 90 gün sonra gerçekleşen kasayla karşılaştırılır. Senaryolar yalnızca sınavdır. Böylece model belirli bir veri kombinasyonunu ezberleyemez. Ölçülen şey şudur: "Daha önce görmediği türden bir işletmede, kendi geçmişinden öğrenip doğru belirsizliği verebiliyor mu?"

Sistem dört katmandan oluşur:

1. **Kaynaklara dayanan senaryo üreticisi.** Boyutların aralıkları gerçek kaynaklardan alınır (aşağıda); varsayım olanlar açıkça yazılıdır.
2. **Gerçekçilik denetimi.** Üretilen senaryoların kaynağa gerçekten oturduğu her koşuda ölçülür.
3. **Geliştirme ve sınav ayrımı.** Yöntem değişiklikleri yalnızca geliştirme kümesinde denenir. Sınav kümesi ayrı tohumlarla üretilir ve senaryolarının yarısında bir boyut geliştirme aralığının dışından çekilir: modelin geliştirilirken hiç karşılaşmadığı rejimler (saklı rejim). Sınav, açık onay olmadan koşmaz ve her koşusu tarih ve sürümle kayda yazılır. Böylece sınava kaç kez bakıldığı görünür kalır.
4. **Gerçek veri son hakemdir.** Laboratuvar, kodun ve istatistiksel kurgunun geniş bir işletme çeşitliliğinde tutarlı olduğunu gösterir. Gerçek dünyada tuttuğunu ise açık gerçek veriler (DOGRULAMA.md) ve pilot gösterir.

## Boyutlar ve dayanakları

| Boyut | Geliştirme aralığı | Saklı aralık (yalnızca sınavda) | Dayanak |
|---|---|---|---|
| Ölçek | mikro / küçük / orta (%35 / %40 / %25) | | TCMB–TÜİK Sektör Bilançoları ölçek kırılımı |
| Müşteri sayısı | mikro 5–15, küçük 15–50, orta 50–120 | | varsayım |
| Sektör ve tahsil süresi | Ölçeğe uygun iki haneli sektör; hedef tahsil süresi sektörün iyi ve kötü çeyrek sınırları arasından (15–180 güne kırpılır) | | TCMB–TÜİK Sektör Bilançoları 2025, Alacak Devir Hızı çeyreklikleri |
| Mevsimsellik genliği | 0–0,30 (tepe ayı rastgele) | 0,30–0,45 | UCI Online Retail II: gerçek bir KOBİ'de 0,30 |
| Yıllık enflasyon (fatura tutarları) | %0–50 | %50–85 | TÜİK TÜFE yıllık değişimi, 2021–2025 |
| Müşteri yoğunlaşması (büyüklük yayılımı) | 0,6–1,3 | 1,3–1,7 | Online Retail II'nin 40 müşterilik alt örneklemlerinde Gini 0,56–0,70 |
| Geçmiş uzunluğu | 15–36 ay | 8–15 ay | varsayım |
| Gecikmelerin kötüleşmesi | 0–1,2 | 1,2–1,8 | varsayım |
| Çeyreklik piyasa şoku | 0–0,30 | 0,30–0,45 | varsayım |
| Çekle ödeyen müşteri payı (sürüm 2) | %0–60 | %60–90 | varsayım (kurumsal istatistik yok) |
| Çek vadesi ortancası (sürüm 2) | 30–120 gün | 120–180 gün | varsayım (kurumsal istatistik yok) |
| Karşılıksız çek oranı (sürüm 2) | %2,8–3,4 | %3,4–7 | TBB Risk Merkezi 2026; saklı aralık kriz varsayımı |
| Tahsilat kayıt gecikmesi (sürüm 3) | 0–14 gün | 14–31 gün | VUK m.219: genel sınır 10 gün, fişe dayanan kayıtta esas deftere 45 gün; aralığın kendisi varsayım |
| Tahmin günü (sürüm 3) | 2026'nın herhangi bir günü | | tasarım: ayın başı, ortası, sonu |
| Kısmi ödeme yapan müşteri payı (sürüm 4) | %0–40 | %40–70 | varsayım |
| Vadesi girilmemiş fatura payı (sürüm 4) | %0–30 | %30–60 | varsayım; panel 30 gün verir (TTK m.1530/4-a) |

Örnekleme Latin hiperküp yöntemiyle yapılır; her boyut kendi aralığında eşit kaplanır.

**Tahsil süresi nasıl oturtulur:** Her senaryoda gecikme ölçeği, işletmenin tahsil süresi hedefe eşit olana kadar ikiye bölme yöntemiyle aranır. Hedefin altında kalan sektörlerde (peşine yakın satış yapanlar) vadeler de aynı oranda kısaltılır. Karşılaştırmada vadesini 180 günden fazla geçmiş açık alacaklar şüpheli alacak sayılıp dışarıda bırakılır. TCMB oranının dayandığı bilanço tutarında da şüpheli alacaklar karşılıkla netleşir (Tekdüzen Hesap Planı 128/129).

**Laboratuvarın ortaya çıkardığı bir üretici kusuru:** Eski sentetik veri, gerçek bir KOBİ'ye göre daha az yoğunlaşmıştı. 40 müşteride Gini 0,56 çıkıyordu; gerçek KOBİ'nin alt örneklemlerinde ise 0,61. Laboratuvar artık gerçek aralığı kapsıyor. Eski çalışmaların varsayılan verisi değişmedi; yeni boyutlar ayrı rastgele sayı akışıyla eklendi.

## Sürüm 1 sonuçları (9 boyut, çek yok)

### Gerçekçilik denetimi

| | Geliştirme | Sınav |
|---|---|---|
| Hedef tahsil süresi medyanı | 68 gün | 65 gün |
| Ulaşılan tahsil süresi medyanı | 69 gün | 63 gün |
| Hedefin ±%10'u içinde kalan senaryo | %83 | %78 |
| Sektör değeri 15–180 gün dışında olduğu için kırpılan | %8 | %12 |

### Genel tablo (dönem sonu kasa, 90 gün)

Her satır, bağımsız sentetik işletmelerden oluşur. Alt aşım, gerçekleşen kasanın kötümser senaryonun (P10) altında kaldığı işletmelerin oranıdır; hedef %10.

| Küme | İşletme | Alt aşım | Üst aşım | Basel (kötümser uç) | Kupiec alt / üst p | Spiegelhalter p | Model hatası − basit yöntem hatası (aylık ciro) |
|---|---|---|---|---|---|---|---|
| Geliştirme | 240 | %7 | %6 | yeşil | 0,13 / 0,025 | 0,004 | −1,04 ± 0,09 |
| **Sınav** | **240** | **%10** | **%9** | **yeşil** | **1,00 / 0,67** | **0,28** | **−0,93 ± 0,09** |

- **Sınavda iki uç da hedefte.** Eksiye düşme olasılıkları kalibre (Spiegelhalter reddetmiyor). Model her ölçek ve her boyut kesitinde "müşteri her zamanki kadar geç öder" yönteminden anlamlı olarak daha iyi.
- **Geliştirme kümesinde bant biraz geniş.** İyimser uç %6 (Kupiec p = 0,025) ve olasılık kalibrasyonu reddediliyor. Bu, sınavda tekrarlanmadı; iki küme arasındaki fark örneklem değişkenliği düzeyinde. Daha önceki sentetik çalışmada da aynı yönde bir bulgu vardı (DOGRULAMA.md); pilot sonrası için ön kayıtlı kalibrasyon güncellemesi bu yüzden açık kalıyor.

### Sağlamlık haritası

Her boyut üç eşit sayılı kesite bölündü ve her kesit Basel ve Kupiec ile ayrı ayrı sınandı. Onlarca kesit birlikte sınandığı için Kupiec ve karşılaştırma p değerleri Benjamini-Hochberg (1995) ile düzeltilir; Basel bölgesi ise ihtiyat gereği düzeltilmez.

- **Geliştirme:** 28 kesitin hepsinde Basel yeşil. Ham p < 0,05 olan 3 kesit düzeltmeden sonra kalmıyor; çoklu testte şansla beklenen düzey bu kadardır. Zayıf bölge yok.
- **Sınav, geliştirme aralığı içi:** bütün kesitler yeşil.
- **Sınav, saklı rejimler:** geçmiş uzunluğu (8–15 ay), yüksek enflasyon, güçlü mevsimsellik ve hızlı kötüleşme yeşil. Çok yoğunlaşmış müşteri yapısı (17 işletme, alt aşım %24) ve aşırı piyasa şoku (20 işletme, alt aşım %20) Basel sarı çıktı.

### Saklı rejimdeki sarı bölgelerin incelenmesi

Sınav verisiyle ayar yapılmaz. İki bölge geliştirme tarafında yeni tohumlarla, bölge başına 120 işletmeyle yeniden incelendi (odak çalışması, `lab.run(..., focus=...)`):

| Bölge | İşletme | Alt aşım | Üst aşım | Basel | Kupiec alt / üst p | Spiegelhalter p | Model − basit yöntem |
|---|---|---|---|---|---|---|---|
| Çok yoğunlaşmış müşteri (1,3–1,7) | 120 | %5,8 | %9,2 | yeşil | 0,13 / 0,77 | 0,26 | −0,93 ± 0,15 |
| Aşırı piyasa şoku (0,30–0,45) | 120 | %6,7 | %11,7 | yeşil | 0,23 / 0,65 | 0,55 | −0,98 ± 0,17 |

Büyük örneklemde iki bölge de yeşil. Sınavdaki sarı, 17–20 işletmelik kesitlerin örneklem değişkenliğiydi; yöntem değişikliği gerekmedi. Yine de bu iki bölgede hata daha büyük (aylık cironun 0,7–0,9'u, genel ortalamada 0,6). Ortalama sapma eksi yönde, yani tahmin ihtiyatlı; medyan sapma ise sıfıra yakın. Az sayıda büyük müşterisi olan işletmede tek bir müşterinin ödemesi kasayı belirler. Model bu belirsizliği bandın genişliğine yansıtıyor.

## Kapsamadıkları (sonraki sürüm)

- Mükerrer fatura laboratuvarda yok. Aynı fatura numarası yüklemede tekilleştirilir; farklı numarayla iki kez girilmiş fatura ayırt edilemez. Kısmi ödeme ve eksik vade sürüm 4'te, tahsilat kayıt gecikmesi sürüm 3'te eklendi.
- Çek ve senet sürüm 2'de eklendi. Ciro edilen ya da iskontoya verilen çekler ve keşideci bazlı risk laboratuvarda yok. Karşılıksızlık oranı ülke geneli (TBB) olarak alınıyor.
- Müşteri sayısı aralıkları ve geçmiş uzunluğu varsayımdır. Fatura düzeyinde açık bir Türk KOBİ verisi bulunamadı; pilot verisi geldikçe bu aralıklar gerçek dağılıma çekilecek.

## Kullanım

```
python -m radar.lab --bolum gelistirme --n 240 --cikti sonuc.csv
python -m radar.lab --bolum sinav --n 240 --sinav-onayi      # yalnızca bir sürüm tamamlandığında
```

`PYTHONPATH=src` gerekir; geliştirme koşusu 20 çekirdekte yaklaşık 10 dakika sürer. Kural: Bir yöntem değişikliği önce geliştirme kümesinde zayıf bölgeyi düzeltmeli ve hiçbir kesiti bozmamalıdır. Bir sürüm tamamlandığında sınav bir kez koşulur. Sınavda bir bölge zayıf çıkarsa sınav verisine dokunulmaz: bölge geliştirme tarafında yeni tohumlarla incelenir, düzeltme orada yapılır ve sonraki sınav yeni tohumlarla (`--seed 1`, `2`, …) koşulur.

## Kaynaklar

- TCMB ve TÜİK, Sektör Bilançoları İstatistikleri 2023–2025, standart oranlar (ölçek kırılımı).
- TÜİK, Tüketici Fiyat Endeksi, yıllık değişim, 2021–2025.
- Chen, D. (2012), Online Retail II veri seti, UCI Machine Learning Repository (CC BY 4.0).
- McKay, M., Beckman, R. ve Conover, W. (1979), "A comparison of three methods for selecting values of input variables in the analysis of output from a computer code", Technometrics 21(2): Latin hiperküp örneklemesi.
- Benjamini, Y. ve Hochberg, Y. (1995), Journal of the Royal Statistical Society B 57(1); Benjamini, Y. ve Yekutieli, D. (2001), Annals of Statistics 29(4).
- Basel BCBS 22 (1996), Kupiec (1995), Spiegelhalter (1986): bkz. `src/radar/standards.py`.
- Morris, T., White, I. ve Crowther, M. (2019), "Using simulation studies to evaluate statistical methods", Statistics in Medicine 38(11): simülasyon çalışmalarının tasarımı ve raporlanması (ADEMP).
