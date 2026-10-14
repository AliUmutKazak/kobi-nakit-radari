# Doğrulama: Simülasyon Çalışması

Tarih: 14 Ekim 2026. Yeniden üretmek için: `python run_validation.py 24` (yaklaşık 3 dakika).

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

**Toplam tahsilat düzeyinde kalibrasyon (14 Ekim 2026).** Her geçmiş çeyrek başında o gün açık olan bütün faturaların sonraki 90 günlük tahsilatı simüle edildi ve simülasyonu gerçekleşene eşitleyen ortak kayma, çeyrekler üzerinden ortalanıp uygulandı. Reddedildi:

- İşaret tutarsızdı. Gecikmeleri hızla kötüleşen bir şirkette dört çeyreğin önerdiği kaymalar −0,30 ile +0,08 arasında dağıldı ve ortalaması, gereken yönün tersine (iyimserliği artıracak yönde) çıktı.
- Dört çeyrekle tahmin edilen tek bir sayı, gürültüsüne göre çok az bilgi taşıyor.
- Tahmin süresi 2 saniyeden 9–11 saniyeye çıktı.

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
