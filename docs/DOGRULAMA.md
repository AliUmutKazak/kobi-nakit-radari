# Doğrulama: Simülasyon Çalışması

Tarih: 14 Ekim 2026. Yeniden üretmek için: `python run_validation.py 24` (yaklaşık 3 dakika).

## Neyi ölçüyor, neyi ölçmüyor

Gerçek işletme verisi gelene kadar tahminin sınanabileceği tek yer, gerçeği bilinen sentetik şirketlerdir. Her şirket için veri tahmin tarihinden 90 gün sonrasına kadar üretilir; tahmin yalnızca o güne kadarki bilgiyle yapılır ve sonra gerçekleşen kasa yoluyla karşılaştırılır. Tahmin tarihinden sonra kesilen faturalar da gerçekleşen yola dahildir.

Bu çalışma şunu gösterir: istatistiksel kurgu kendi içinde tutarlı mı, hangi şirket tiplerinde zorlanıyor. Şunu göstermez: gerçek dünyada tutar mı. Sentetik veriyi üreten kurallar bize aittir; gerçek ödeme davranışı bunlardan farklı olabilir.

## Tasarım

192 bağımsız tahmin: 24 rastgele tohum × 8 rejim. Her tahminden üç açılış kasası düzeyi türetilir (toplam 576 şirket durumu); açılış kasası yalnızca bütün yolları sabit kadar kaydırdığı için ayrı tahmin gerektirmez.

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
| Dönem sonu kasa P10–P90 bandında | %80 | %84 ±3 |
| Bandın altında kalan | %10 | %10 ±2 |
| Bandın üstünde kalan | %10 | %5 ±2 |
| Beklenen değerin sapması (aylık ciro; artı = iyimser) | 0 | +0,09 ±0,03 |
| Brier skoru (tahminsiz taban 0,229) | düşük | 0,095 |

Eksiye düşme olasılığının kalibrasyonu:

| Söylenen olasılık | Şirket durumu | Ortalama tahmin | Gerçekleşen sıklık |
|---|---|---|---|
| %0–10 | 44 | %6 | %2 |
| %10–30 | 97 | %21 | %11 |
| %30–70 | 145 | %51 | %54 |
| %70–90 | 97 | %81 | %93 |
| %90–100 | 193 | %97 | %99 |

Okuma: sıralama doğru ve orta bölge isabetli. İki uçta tahmin ortaya doğru çekik: "%21" denen şirketlerin %11'i, "%81" denenlerin %93'ü eksiye düştü. Yani panel düşük riskte biraz fazla, yüksek riskte biraz eksik söylüyor; karar yönünü değiştirmiyor ama düzeltilmesi gereken bir kusur.

Rejim kırılımı:

| Rejim | Bant içi | Altında | Üstünde | Sapma (aylık ciro) |
|---|---|---|---|---|
| 8 müşteri | %81 ±4 | %15 ±4 | %4 ±2 | +0,14 ±0,05 |
| 40 müşteri | %88 ±3 | %6 ±2 | %6 ±2 | +0,05 ±0,03 |
| Gecikmeler sabit | %83 ±4 | %8 ±3 | %8 ±3 | +0,02 ±0,04 |
| Gecikmeler hızla kötüleşiyor | %85 ±4 | %12 ±3 | %2 ±1 | +0,17 ±0,04 |
| Piyasa şoku yok | %89 ±3 | %9 ±3 | %2 ±1 | +0,13 ±0,04 |
| Piyasa şoku var | %80 ±4 | %11 ±3 | %8 ±3 | +0,05 ±0,04 |

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
| Gecikmeler hızla kötüleşirken beklenen değer iyimser | +0,17 ±0,04 aylık ciro | Giderilemedi. Kalibrasyon geçmiş hatayı düzeltiyor ama kötüleşmenin tahmin döneminde de süreceğini öngöremiyor. Eğilimi ileriye uzatmak tahmin literatüründe güvenilmez bulunduğu için yapılmadı. Bunun yerine panel, ödemeler son 90 günde belirgin biçimde gecikmeye başladıysa kullanıcıyı uyarıyor. Bant bu rejimde de %85 kapsıyor. |
| Genel hafif iyimserlik | +0,09 ±0,03 aylık ciro | Büyük kısmı yukarıdaki rejimden geliyor; gecikmeler sabitken sapma +0,02 ±0,04. |
| Bandın üst tarafı fazla geniş | Üstünde %5 (hedef %10) | Yukarı yönlü sürpriz olması gerekenden seyrek; hata temkinli yönde. |
| Olasılık iki uçta ortaya çekik | %21 denilen %11, %81 denilen %93 | Henüz ele alınmadı. |

## Ek ölçümler (tek şirket, 6 geçmiş tarih)

- Vade aşımı tahmininde ortalama mutlak hata: model 15,1 gün, müşteri medyanı 15,7 gün. Nokta isabetinde kazanç küçük; modelin katkısı dağılımın şeklinde.
- Tek faturanın gecikmesi için P10–P90 aralığının isabeti: %80 (hedef %80).

## Kaynaklar

- Gneiting, Balabdaoui, Raftery (2007), [Probabilistic forecasts, calibration and sharpness](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jrssb.pdf), JRSS-B.
- Brier skoru ve güvenilirlik tablosu, tek yönlü rastgele etkiler varyans analizi, sansürlü normal olabilirlik (Tobit) ve Poisson bootstrap standart istatistik yöntemleridir. Bunlar için birincil kaynak taraması henüz yapılmadı; [ARASTIRMA.md](ARASTIRMA.md) içindeki teyit listesine eklenmeli.
