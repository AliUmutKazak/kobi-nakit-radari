# Doğrulama: Simülasyon Çalışması

Tarih: 14 Ekim 2026. Yeniden üretmek için: `python run_validation.py 24` (yaklaşık 3 dakika).

## Gerçek açık verilerle doğrulama (14 Ekim 2026)

Sentetik çalışma (aşağıda) kurgunun kendi içinde tutarlı olduğunu gösterir; gerçek dünyada işe yarayıp yaramadığını göstermez. Bunun ilk kanıtı için Małkus, Bobek ve Nalepa'nın (arXiv:2511.03631) KOBİ çalışmasında da kullanılan iki herkese açık gerçek veri seti kullanıldı. Yeniden üretmek için: dosyaları `data/acik/` klasörüne koyup `python -m radar.open_data` (src yolu tanımlıyken).

| Veri seti | Fatura | Müşteri | Dönem |
|---|---|---|---|
| IBM Late Payment Histories (Kaggle: hhenry) | 2.466 | 100 | 01.2012 – 12.2013 |
| Payment Date Dataset (Kaggle: rajattomar132) | 39.158 | 1.056 | 12.2018 – 02.2020 |

Yöntem: geçmiş tarihlere dönülür, o gün bilinen veriyle tahmin yapılır, sonra gerçekleşenle karşılaştırılır (sızıntı yok). Fatura düzeyinde: vadesi henüz gelmemiş faturaların gecikmesi. Kasa düzeyinde: o gün açık faturalardan önümüzdeki 14 ve 30 günde tahsil edilen tutar.

**Fatura düzeyinde gecikme, ortalama mutlak hata (gün; düşük iyi):**

| Veri | Model | Müşteri medyanı | Son 4 fatura ort. | Son 2 fatura ort. | Vadesinde öder | Model P10–P90 kapsama (hedef %80) |
|---|---|---|---|---|---|---|
| IBM | 6,27 | **6,03** | 6,53 | 7,13 | 9,22 | %86 |
| Payment Date | 3,53 | **3,23** | 4,54 | 4,61 | 4,04 | %78 |

**Kasa düzeyinde tahsilat sapması (mutlak hata toplamı / gerçekleşen tahsilat; düşük iyi):**

| Veri | Ufuk | Model | Müşteri medyanı | Tahsilat oranı | Vadesinde öder | Tahsilatın bant içinde kaldığı tarih (8 tarihten) |
|---|---|---|---|---|---|---|
| IBM | 14 gün | %9,6 | %17,9 | **%7,1** | %19,3 | %100 |
| IBM | 30 gün | %4,6 | %3,8 | **%2,6** | %10,9 | %75 |
| Payment Date | 14 gün | %2,7 | **%2,6** | %5,2 | %8,5 | %75 |
| Payment Date | 30 gün | %1,8 | **%1,4** | %3,0 | %2,1 | %62 |

*Tahsilat oranı* (15 Ekim 2026'da eklendi): bir önceki aynı uzunluktaki dönemde, dönem başında açık alacağın yüzde kaçı tahsil edildiyse bugün de o kadarı tahsil edilir. Muhasebede yaygın, fatura tek tek tahmin etmeyen bir yaklaşımdır. Ekleme nedeni: sentetik şirketlerde "vadesinde öder" ve "müşteri medyanı" yöntemleri vadesi çoktan geçmiş faturaları "yakında ödenir" saydığı için %80–450 sapıyordu; modelin yalnızca bu iki yönteme karşı ölçülmesi, şüpheli alacağı çok olan gerçek işletmelerde onu olduğundan iyi gösterirdi.

**Sonuç (tahsilat oranı dahil).** IBM verisinde bu kaba yöntem, kasa düzeyinde her iki ufukta da modelden daha isabetli; Payment Date'te ise modelin ve medyanın gerisinde. Yani tek bir basit yöntem her veride kazanmıyor, model de her veride kazanmıyor. Pilot protokolündeki birincil ölçüt (B1) buna göre kuruldu: model, medyan ve oran yöntemlerinin iyisinden en fazla 2 puan kötü olmalı. Bu ölçütle açık verilerde model 4 durumun 3'ünde geçer, IBM 14 günde kalır (%9,6'ya karşı %7,1 + 2).

**Sonuç (ilk ölçüm, 14 Ekim).** Gerçek veride model, "müşteri her zamanki kadar geç öder" basit yöntemiyle aşağı yukarı başa baş; bir durumda belirgin şekilde önde (IBM, 14 gün), çoğunda biraz geride. KOBİ'lerin çoğunun fiilen kullandığı "vadesinde ödenir" varsayımını ise her durumda yeniyor. Sentetik çalışmadaki büyük üstünlük (aşağıda) gerçek veride tekrarlanmadı; "akıllı tahmin" iddiası bu sonuçlarla desteklenmiyor. Fatura gecikmesi için tahmin aralığı gerçek veride de yaklaşık doğru (%78–86); kasa düzeyindeki bant Payment Date'te gerektiğinden dar (%62–75).

**Düzeltme: ödeme gününün yuvarlanması (15 Ekim 2026).** IBM'de model 14 günlük tahsilatı 8 tarihin 8'inde düşük tahmin ediyordu (ortalama %10). Neden: simülasyon, tahmin edilen ödeme gününü hep yukarı yuvarlıyordu; model tam gün gecikmelerden öğrendiği için bu her ödemeye ortalama yarım gün gecikme ekliyordu. En yakın güne yuvarlamayla (aynı tahmin tarihleri, aynı ayarlar):

| Veri | Ufuk | Model sapması önce → sonra | Ortalama yön önce → sonra | Bant içi önce → sonra |
|---|---|---|---|---|
| IBM | 14 gün | %9,6 → **%6,6** | −%9,6 → −%6,5 | %100 → %100 |
| IBM | 30 gün | %4,6 → **%4,2** | −%3,3 → −%2,5 | %75 → %75 |
| Payment Date | 14 gün | %2,7 → **%2,5** | −%2,5 → +%0,6 | %75 → %88 |
| Payment Date | 30 gün | %1,8 → **%1,7** | −%0,8 → −%0,6 | %62 → **%38** |

Nokta isabeti dört durumda da iyileşti; model IBM 14 günde tahsilat oranı yöntemini (%7,1), Payment Date 14 günde müşteri medyanını (%2,6) geçti. Payment Date 30 günde bandın tutma oranı düştü (8 tarihin 5'inden 3'üne): bu veri setinde bant zaten dardı, düzeltme daraltmayı görünür kıldı. Bant genişliğinin büyük portföylerde yetersiz kalması ayrı bir açık sorun olarak duruyor. Sentetik çalışmada (24 tohum × 8 rejim) fark gürültü düzeyinde ve biraz aleyhte: dönem sonu hatası 0,316 → 0,321, Brier 0,095 → 0,097 (eşleştirilmiş farkların belirsizliği ±0,04). Gerçek veri ve gerekçe öne alındı; sentetik veri de en yakın güne yuvarlanmış gecikmelerle üretildiği için yukarı yuvarlamanın orada tutarlı bir avantajı yoktur.

**Bu düzeltmeden sonra B1 (pilot protokolü) açık verilerde:** IBM 14 gün geçer (%6,6 ≤ %7,1 + 2), IBM 30 gün geçer (%4,2 ≤ %2,6 + 2), Payment Date her iki ufukta geçer. B2 (bant ≥ %70) Payment Date 30 günde sağlanmaz.

**Veri setlerinin sürümü ve dönüşümü.** Sonuçlar şu dosyalarla üretildi (Kaggle'dan elle indirildi; lisans koşulları Kaggle sayfalarındadır, dosyalar depoya konmaz ve yeniden dağıtılmaz):

| Dosya | Satır | SHA-256 |
|---|---|---|
| data/acik/ibm_late_payment.csv | 2.466 | 651bc4225708bf33148a0e177c9221afdf697d3a4de10333725a4af3dd022fcf |
| data/acik/payment_date.csv | 50.000 | 139482bdc3325a734474d08f48ceee71ab67c84b106f2a0c0fe9479d71be8431 |

Dönüşüm kuralları (src/radar/open_data.py): tutarı sıfır ya da negatif, tarihi okunamayan satırlar ve tekrar eden fatura numaraları atılır; IBM'de tarihler ay/gün/yıl, Payment Date'te vade YYYYMMDD, fatura tarihi `posting_date`, ödeme `clear_date`; Payment Date'te `isOpen = 1` satırları (etiketi gizlenmiş test bölümü) çıkarılır. Dosyanın özeti farklıysa sonuçlar karşılaştırılamaz.

**Bağımsız inceleme notu (15 Ekim 2026).** Aynı gün yapılan dış incelemenin sonuç tablosu, ödeme günü yuvarlama düzeltmesinden önceki sayılarla yazılmıştır (ör. IBM 14 gün %9,6). Güncel sayılar yukarıdaki düzeltme tablosundadır. İncelemenin işaret ettiği ve henüz açık olan sorunlar: sentetik çalışmada yüksek risk diliminde eksiye düşme olasılığının düşük tahmin edilmesi (tahmin %81, gerçekleşen %91) ve Payment Date 30 günde bandın dar kalması: aşağı kuyruk yeterince korunmuyor. Pilot raporu bu yüzden bant içi oranın yanında bant genişliğini ve aralık skorunu da ufuk başına verir.

**Veri tuzakları ve alınan önlemler.**
- Payment Date'teki 10.000 "açık" fatura gerçekte ödenmemiş fatura değil; veri setinin, etiketi bilerek gizlenmiş test bölümü (27.02.2020 sonrası). Çıkarıldı; tahmin tarihleri etiketin tam olduğu döneme sınırlandı. Bu yapılmadan ilk ölçümde model %8,4, medyan %2,9 çıkmıştı.
- Bu iki veri setinde hiç ödenmeyen fatura yok (etiketli faturaların hepsi ödenmiş). Gerçek KOBİ alacaklarında var; bu durum, hiç ödenmeme olasılığını hesaba katan modeli bu testte cezalandırır.
- Makaledeki "müşteri başına en fazla 50 fatura" sınırı büyük müşterilerin eski faturalarını attığı için kasa testini bozuyor; kullanılmadı.

**Bu veride denenip reddedilen iki düzeltme:**

| Deneme | Fikir | Sonuç |
|---|---|---|
| Taban tahminden başlama | Model, müşterinin ham medyanından başlayıp yalnızca düzeltmeyi öğrenir (gradyan artırmada başlangıç değeri) | Fatura hatası IBM 6,19 → 6,26, Payment Date 3,43 → 3,51; kasa sapması IBM 14 gün %10,8 → %13,5. Reddedildi. |
| Şirket bazında yöntem seçimi | Geçmiş tarihlerde model ile basit yöntem yarıştırılır, kazanan kullanılır | Kasa sapması Payment Date 14 gün %2,7 → %5,6, bant içi %75 → %62; IBM 14 gün %9,9 → %11,8. Basit yöntemin olasılıklı hâli bütün müşterilere aynı genişlikte belirsizlik verdiği için kasa simülasyonunda daha kötü. Reddedildi. |

**Ürüne yansıması.** Panel, kullanıcının kendi verisinde modeli bu basit yöntemlere karşı sınıyor ve geride kalırsa söylüyor ("Tahmin doğruluğu" sekmesi); bu, gerçek veride en önemli güvence. Ürünün değeri, tek fatura isabetinden çok giderler, borçlar, çekler ve vergi takvimiyle birlikte kasanın aralığını ve eksiye düşme riskini göstermesinde ve "vadesinde ödenir" varsayımının yarattığı iyimserliği düzeltmesinde aranmalı.

## Neyi ölçüyor, neyi ölçmüyor

Gerçek işletme verisi gelene kadar tahminin sınanabileceği tek yer, gerçeği bilinen sentetik şirketlerdir. Her şirket için veri tahmin tarihinden 90 gün sonrasına kadar üretilir; tahmin yalnızca o güne kadarki bilgiyle yapılır ve sonra gerçekleşen kasa yoluyla karşılaştırılır. Tahmin tarihinden sonra kesilen faturalar da gerçekleşen yola dahildir.

Bu çalışma şunu gösterir: istatistiksel kurgu kendi içinde tutarlı mı, hangi şirket tiplerinde zorlanıyor. Şunu göstermez: gerçek dünyada tutar mı. Sentetik veriyi üreten kurallar bize aittir; gerçek ödeme davranışı bunlardan farklı olabilir.

## Tasarım

384 bağımsız tahmin: 48 rastgele tohum × 8 rejim. Her tahminden üç açılış kasası düzeyi türetilir (toplam 1.152 şirket durumu); açılış kasası yalnızca bütün yolları sabit kadar kaydırdığı için ayrı tahmin gerektirmez.

| Boyut | Değerler | Neden |
|---|---|---|
| Müşteri sayısı | 8, 40 | Az müşteri, tek bir gecikmenin kasayı belirlemesi demek |
| Gecikmelerin kötüleşme hızı | 0, 1,2 | 1,2: gecikmeler iki yılda iki katından fazla uzuyor; model geçmişten öğrendiği için geride kalabilir |
| Çeyreklik piyasa şoku | yok, var | Tüm müşterileri birlikte geciktiren, tahmin döneminde değeri bilinmeyen ortak etki |
| Açılış kasası (aylık ciro cinsinden) | 0,2, 0,45, 0,8 | Eksiye düşme olasılığının tüm aralığını kapsamak için |

Ölçütler, olasılıksal tahmin literatürünün standart ikilisidir (Gneiting, Balabdaoui, Raftery 2007): önce kalibrasyon, sonra keskinlik. Her oran standart hatasıyla verilir; standart hatanın içinde kalan fark bulgu sayılmaz.

## Sonuç

| Ölçüt | Hedef | Sonuç |
|---|---|---|
| Dönem sonu kasa P10–P90 bandında | %80 | %81 ±2 |
| Bandın altında kalan | %10 | %14 ±2 |
| Bandın üstünde kalan | %10 | %5 ±1 |
| Beklenen değerin sapması (aylık ciro; artı = iyimser) | 0 | +0,10 ±0,02 |
| Brier skoru (Brier 1950; tahminsiz taban 0,223) | düşük | 0,097 |

Eksiye düşme olasılığının kalibrasyonu:

| Söylenen olasılık | Şirket durumu | Ortalama tahmin | Gerçekleşen sıklık |
|---|---|---|---|
| %0–10 | 97 | %5 | %4 |
| %10–30 | 163 | %21 | %17 |
| %30–70 | 289 | %50 | %53 |
| %70–90 | 194 | %81 | %91 |
| %90–100 | 409 | %97 | %99 |

Okuma: alt ve orta bölge isabetli. Yüksek riskte panel eksik söylüyor: "%81" denen şirketlerin %91'i eksiye düştü. Bu, aşağıdaki iyimser kaymayla aynı kusurun olasılıktaki görüntüsü.

### Basit yöntemlere karşı

Bir modelin "akıllı" sayılması için önce basit yöntemleri yenmesi gerekir (Makridakis vd. 2022, M5 sonuçları; ayrıca kullanıcının 14 Ekim 2026 tarihli inceleme raporundaki öneri). Aynı 384 tahminde, aynı fatura kümesi ve aynı giderlerle, üç basit kasa tahmini kuruldu:

- **Sözleşme vadesi:** her fatura vadesinde ödenir; vadesi geçmişse yarın.
- **Müşteri medyanı:** her müşteri, geçmişte vadeden medyan kaç gün sonra ödediyse yine öyle öder.
- **Tahsilat hızı:** son 90 günde günde ortalama ne kadar tahsil edildiyse önümüzdeki 90 günde de o kadar gelir. Elle tutulan Excel tahminlerinin çoğu budur.

Hatalar aylık ciro cinsindendir; "fark" model eksi yöntemdir, eksi değer modelin daha iyi olduğunu gösterir. Farklar aynı şirketler üzerinde eşleştirilmiştir.

| Yöntem | Dönem sonu kasa hatası | En düşük kasa hatası | Eksiye düşme (Brier) | Fark: dönem sonu | Fark: en düşük kasa | Fark: Brier |
|---|---|---|---|---|---|---|
| **Model** | **0,332** | **0,193** | **0,097** | | | |
| Sözleşme vadesi | 1,585 | 1,412 | 0,607 | −1,253 ±0,034 | −1,219 ±0,028 | −0,509 ±0,016 |
| Müşteri medyanı | 1,033 | 0,879 | 0,527 | −0,701 ±0,027 | −0,686 ±0,023 | −0,429 ±0,015 |
| Tahsilat hızı | 0,780 | 0,420 | 0,345 | −0,448 ±0,040 | −0,227 ±0,018 | −0,247 ±0,014 |

%80 aralık skoru (Gneiting ve Raftery 2007; aralığın genişliği ile dışına düşen gözlemin cezası): 1,494 aylık ciro. Basit yöntemler aralık vermediği için bu ölçüt yalnızca model sürümlerini birbiriyle karşılaştırmak içindir.

Çekince: veri sentetiktir ve modelin bildiği türden davranışlar (çarpık gecikmeler, hiç ödenmeyen faturalar, ödeme günü alışkanlıkları) içerir. Basit yöntemler bunları bilmediği için fark burada büyük çıkıyor; gerçek veride daha küçük olabilir. Aynı karşılaştırma ilk pilot verisinde tekrarlanmalı; model orada da tahsilat hızı yöntemini yenmezse panel "akıllı tahmin" iddiasında bulunmamalı. Yaşlandırma eğrisine dayalı daha güçlü bir basit yöntem henüz eklenmedi.

Rejim kırılımı:

| Rejim | Bant içi | Altında | Üstünde | Sapma (aylık ciro) |
|---|---|---|---|---|
| 8 müşteri | %77 ±3 | %18 ±3 | %5 ±2 | +0,14 ±0,04 |
| 40 müşteri | %85 ±3 | %9 ±2 | %6 ±2 | +0,07 ±0,02 |
| Gecikmeler sabit | %80 ±3 | %11 ±2 | %9 ±2 | +0,03 ±0,03 |
| Gecikmeler hızla kötüleşiyor | %82 ±3 | %16 ±3 | %2 ±1 | +0,18 ±0,03 |
| Piyasa şoku yok | %85 ±3 | %11 ±2 | %4 ±1 | +0,11 ±0,03 |
| Piyasa şoku var | %77 ±3 | %16 ±3 | %7 ±2 | +0,09 ±0,03 |

Not: aynı kodla yalnızca ilk 24 tohum koşulduğunda sonuçlar daha iyi görünüyordu (bant içi %84, altında %10). İkinci 24 tohum daha kötü çıktı (%78, %17). Fark iki standart hatanın içinde; 48 tohumluk birleşik sonuç esas alınmalı.

## Bu çalışmanın ortaya çıkardığı ve düzeltilen kusurlar

1. **Bant gereğinden genişti (ilk ölçümde bant içi %100).** Faturaların birlikte gecikme derecesi sabit bir varsayımdı; artık veriden ölçülüyor.
2. **Yukarı yönlü sürprizler eksik sayılıyordu (üstünde %18).** Gelecek satışlar sabit alınıyordu; artık her senaryoda Poisson(1) ağırlığıyla yeniden örnekleniyor.
3. **Piyasa şokunda bant dardı (bant içi %75).** Belirsizlik, modelin eğitim verisine uyumundan ölçülüyordu; o veri bilinen geçmiştir ve şoku zaten içerir. Artık son dört çeyreğin her birinin başına dönülüp o günkü bilgiyle tahmin yapılıyor ve hata, gerçekleşenle karşılaştırılarak ölçülüyor (ileriye dönük kalibrasyon). Şoklu rejimde bant içi %80'e çıktı.
4. **Hâlâ ödenmemiş faturalar hatayı gizliyordu.** Kalibrasyonda ödenmemiş faturanın gecikmesi yalnızca alt sınırdır; gerçek değer sayılınca iyimserlik görünmez oluyordu. Sansürlü en çok olabilirlik tahminiyle düzeltildi; vadesi geçmiş ve geçmemiş faturalar ayrı kalibre ediliyor.

## Önceki sürümdeki bir yanlış sonuç

Bu belgenin ilk hâlinde "8 müşterili şirketlerde bant dar ve beklenen değer kötümser" yazıyordu. O ölçüm 8 tohuma dayanıyordu ve aynı tohumun farklı rejimleri bağımsız sayılmıştı. 96 bağımsız şirketle yinelendiğinde bulgu kayboldu (bant içi %82, sapma +0,03 ±0,06). Çalışma bu yüzden daha çok bağımsız tohumla ve standart hatayla yeniden kuruldu.

## Kalan zayıflıklar

| Bulgu | Değer | Durum |
|---|---|---|
| Dağılım iyimser yöne kaymış | Altında %14, üstünde %5; sapma +0,10 aylık ciro | Asıl kalan kusur. Gecikmeler sabitken neredeyse yok (+0,03); gecikmeler hızla kötüleşirken (+0,18) ve az müşteride (+0,14) belirgin. |
| Gecikmeler hızla kötüleşirken iyimserlik | +0,18 ±0,03 aylık ciro | Kalibrasyon geçmiş hatayı düzeltiyor ama kötüleşmenin tahmin döneminde de süreceğini öngöremiyor. Eğilimi ileriye uzatmak güvenilmez olduğu için yapılmadı; panel bu durumda uyarı veriyor. |
| Piyasa şokunda alt kuyruk ince | Altında %16 ±3 | Dört çeyreklik geçmişten piyasa korelasyonu güvenilir ölçülemiyor; ön değere büzülüyor. |
| Yüksek riskte olasılık eksik | %81 denilen %91 | Kaymanın olasılıktaki karşılığı. |

## Denenip reddedilen düzeltme

**Kalibrasyonda daha çok geçmiş tahmin tarihi (15 Ekim 2026).** Belirsizlik ayarı (kayma, ölçek, birlikte gecikme payı) geçmişteki 4 tahmin tarihinden (90 gün arayla) ölçülüyor; birlikte gecikmenin piyasa payı bu kadar az grupla gürültülü kalır. Aynı bir yıllık dönemde 8 tarih (45 gün arayla) denendi. Gerçek veride kasa sapması IBM 14 gün %6,60 → %6,66, 30 gün %4,20 → %4,24, Payment Date 14 gün %2,52 → %2,12, 30 gün %1,70 → %1,66; bant içi oranları değişmedi (Payment Date 30 gün %38 kaldı). Sentetik çalışmada (24 tohum × 8 rejim) her ölçüt biraz kötüleşti: dönem sonu hatası 0,321 → 0,328, Brier 0,097 → 0,098, aralık skoru 1,456 → 1,472, kapsama %83 → %81. Hedeflenen sorun (büyük portföyde dar bant) çözülmedi, tahmin süresi uzadı. Reddedildi. Büyük portföyde bant darlığı açık sorun olarak duruyor; gerçek KOBİ verisi olmadan açık veri setlerine göre ayar yapılmayacak.

**Toplam tahsilat düzeyinde kalibrasyon (14 Ekim 2026).** Her geçmiş çeyrek başında o gün açık olan bütün faturaların sonraki 90 günlük tahsilatı simüle edildi ve simülasyonu gerçekleşene eşitleyen ortak kayma, çeyrekler üzerinden ortalanıp uygulandı. Reddedildi:

- İşaret tutarsızdı. Gecikmeleri hızla kötüleşen bir şirkette dört çeyreğin önerdiği kaymalar −0,30 ile +0,08 arasında dağıldı ve ortalaması, gereken yönün tersine (iyimserliği artıracak yönde) çıktı.
- Dört çeyrekle tahmin edilen tek bir sayı, gürültüsüne göre çok az bilgi taşıyor.
- Tahmin süresi 2 saniyeden 9–11 saniyeye çıktı.

**Geçmiş çeyrek modellerinde tek eğitim (14 Ekim 2026).** Hız için, kalibrasyonun geçmiş çeyreklerde kurduğu modeller kalibrasyon payı ayrılmış hâliyle bırakıldı (tüm veriyle yeniden eğitilmedi). Tahmin %35–40 hızlandı, ama aynı 384 tahminde sonuç her ölçütte aynı yönde kötüleşti: bant içi %81 → %79, bandın altında %14 → %16, sapma +0,10 → +0,12 aylık ciro; 40 müşterili şirketlerde bandın altında kalma %9 → %14. Geri alındı. Sonucu birebir aynı bırakan hızlandırmalar (zamandan bağımsız özelliklerin bir kez hesaplanması, piyasa medyanının tarih başına bir kez hesaplanması; fark sayısal olarak 0) tutuldu; kazanç yaklaşık %20.

**Yakın geçmişe ağırlık (14 Ekim 2026).** Zamanla değişen davranışa karşı yaygın bir yöntem: eğitimde her faturanın ağırlığı 180 günde bir yarıya indi. Aynı 384 tahminde sapma azalmadı, arttı: genel +0,10 → +0,13, gecikmeler hızla kötüleşirken +0,18 → +0,21 aylık ciro; bant içi %81 → %80, altında %14 → %15. Reddedildi. Yorum: ağırlıklandırma veriyi fiilen azaltıp tahmini gürültülü yapıyor ama asıl sorunu çözmüyor; sorun, kötüleşmenin tahmin döneminde de süreceğini öngörememek.

Kalan iyimserlik bu yüzden düzeltilmedi, açıkça bildiriliyor: panel, ödemeler son 90 günde belirgin biçimde gecikmeye başladıysa kötümser çizgiyi esas almayı öneriyor.

## Ek ölçümler (tek şirket, 6 geçmiş tarih)

- Vade aşımı tahmininde ortalama mutlak hata: model 15,1 gün, müşteri medyanı 15,7 gün. Nokta isabetinde kazanç küçük; modelin katkısı dağılımın şeklinde.
- Tek faturanın gecikmesi için P10–P90 aralığının isabeti: %80 (hedef %80).

## Kaynaklar

- Gneiting, Balabdaoui, Raftery (2007), [Probabilistic forecasts, calibration and sharpness](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jrssb.pdf), JRSS-B.
- Brier (1950), Verification of forecasts expressed in terms of probability, Monthly Weather Review 78(1), 1–3.
- Tobin (1958), [Estimation of relationships for limited dependent variables](https://jstor.econometricsociety.org/publications/econometrica/1958/01/01/estimation-relationships-limited-dependent-variables), Econometrica 26(1), 24–36: sansürlü normal olabilirlik.
- Kaplan ve Meier (1958), Nonparametric estimation from incomplete observations, JASA 53(282), 457–481: yaşlandırma eğrisi.
- Romano, Patterson, Candès (2019), [Conformalized Quantile Regression](https://proceedings.neurips.cc/paper_files/paper/2019/file/5103c3584b063c431bd1268e9b5e76fb-Paper.pdf), NeurIPS: gecikme modelindeki aralık kalibrasyonu.
- Hanley ve MacGibbon (2006), Poisson bootstrap; künye ikincil kaynaklardan, dergi sayfası teyit edilmedi.
