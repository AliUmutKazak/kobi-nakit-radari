# Doğrulama: Simülasyon Çalışması

Tarih: 14 Ekim 2026. Yeniden üretmek için: `python run_validation.py 8` (yaklaşık 5 dakika).

## Neyi ölçüyor, neyi ölçmüyor

Gerçek işletme verisi gelene kadar tahminin sınanabileceği tek yer, gerçeği bilinen sentetik şirketlerdir. Her şirket için veri tahmin tarihinden 90 gün sonrasına kadar üretilir; tahmin yalnızca o güne kadarki bilgiyle yapılır ve sonra gerçekleşen kasa yoluyla karşılaştırılır. Tahmin tarihinden sonra kesilen faturalar da gerçekleşen yola dahildir.

Bu çalışma şunu gösterir: istatistiksel kurgu kendi içinde tutarlı mı, hangi şirket tiplerinde zorlanıyor. Şunu göstermez: gerçek dünyada tutar mı. Sentetik veriyi üreten kurallar bize aittir; gerçek ödeme davranışı bunlardan farklı olabilir.

## Tasarım

216 şirket: 8 rastgele tohum × 27 rejim.

| Boyut | Değerler | Neden |
|---|---|---|
| Müşteri sayısı | 8, 20, 40 | Az müşteri, tek bir gecikmenin kasayı belirlemesi demek |
| Gecikmelerin kötüleşme hızı | 0, 0,6, 1,2 | Model geçmişten öğrenir; rejim değişirken geride kalabilir |
| Açılış kasası (aylık ciro cinsinden) | 0,2, 0,45, 0,8 | Eksiye düşme olasılığının tüm aralığını kapsamak için |

Ölçütler, olasılıksal tahmin literatürünün standart ikilisidir (Gneiting, Balabdaoui, Raftery 2007): önce kalibrasyon (söylenen olasılık gerçekleşen sıklıkla tutuyor mu), sonra keskinlik.

## Sonuç

| Ölçüt | Hedef | İlk sürüm | Şimdi |
|---|---|---|---|
| Dönem sonu kasa P10–P90 bandında | %80 | %100 (27 şirketlik ön ölçüm) | %86 |
| Bandın altında kalan | %10 | %0 | %3 |
| Bandın üstünde kalan | %10 | %0 | %11 |
| Beklenen değerin sapması (aylık ciro) | 0 | tek tohumla ölçülemedi | −0,03 |
| Brier skoru (tahminsiz taban 0,250) | düşük | 0,122 | 0,088 |

Eksiye düşme olasılığının kalibrasyonu:

| Söylenen olasılık | Şirket sayısı | Ortalama tahmin | Gerçekleşen sıklık |
|---|---|---|---|
| %0–10 | 51 | %4 | %0 |
| %10–30 | 31 | %21 | %10 |
| %30–70 | 50 | %48 | %54 |
| %70–90 | 29 | %83 | %93 |
| %90–100 | 55 | %96 | %96 |

Okuma: panel "%48 olasılıkla eksiye düşer" dediği şirketlerin %54'ü gerçekten düştü. Sıralama doğru ve değerler birbirine yakın; orta bölgede birkaç puanlık fark 30–50 şirketlik gruplarda örnekleme gürültüsünün içinde.

## Bu çalışmanın ortaya çıkardığı ve düzeltilen iki kusur

1. **Bant gereğinden genişti.** Faturaların birlikte gecikme derecesi (piyasa ve müşteri korelasyonu) sabit bir varsayımdı. Artık her şirketin kendi geçmişinden ölçülüyor: gerçekleşen gecikmeler tahmin dağılımındaki yerlerine çevriliyor ve çeyrek ile müşteri bazındaki ortak sapma, tek yönlü rastgele etkiler varyans analiziyle ayrıştırılıyor. Veri 200 faturadan azsa ön değer kullanılıyor.
2. **Yukarı yönlü sürprizler eksik sayılıyordu.** İlk düzeltmeden sonra gerçekleşen kasa, bandın üstüne olması gerekenden sık çıkıyordu (%18). Neden: gelecek satışlar "geçen çeyreğin aynısı" diye sabit alınıyordu. Artık her senaryoda geçmiş dönemin faturaları Poisson(1) ağırlığıyla yeniden örnekleniyor (Poisson bootstrap), yani satışların kendisi de belirsiz. Üst taraf %11'e indi.

## Kalan zayıflıklar

| Bulgu | Değer | Yorum |
|---|---|---|
| Bandın alt tarafı fazla temkinli | Altında kalan %3 (hedef %10) | Kötümser çizgi gerçekte olduğundan kötü. Yanlış alarm yönünde hata; kaçırılan alarm yönünde değil. |
| 40 müşterili şirketlerde bant fazla geniş | Bant içi %100 | Piyasa etkisi için kullanılan ön değer sıfır değil; sentetik veride ise ortak piyasa şoku yok. Gerçek dünyada böyle şoklar var, bu yüzden ön değeri sıfırlamadım. |
| 8 müşterili şirketlerde bant dar ve beklenen değer kötümser | Bant içi %75, sapma −0,15 aylık ciro | Az müşteride tek bir büyük fatura sonucu belirliyor; en zayıf olduğumuz şirket tipi bu. |
| Gecikmeler hızla kötüleşirken hafif iyimserlik | Sapma +0,06 aylık ciro | Model geçmişten öğrendiği için rejim değişimini geriden izliyor. |

## Ek ölçümler (tek şirket, 6 geçmiş tarih)

- Vade aşımı tahmininde ortalama mutlak hata: model 15,1 gün, müşteri medyanı 15,7 gün. Nokta isabetinde kazanç küçük; modelin katkısı dağılımın şeklinde.
- Tek faturanın gecikmesi için P10–P90 aralığının isabeti: %80 (hedef %80).
- Açık faturalardan 90 günlük tahsilat: 6 tarihin 6'sında gerçekleşen bant içinde; beklenen değer gerçekleşenin %2–11 üzerinde.

## Kaynaklar

- Gneiting, Balabdaoui, Raftery (2007), [Probabilistic forecasts, calibration and sharpness](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jrssb.pdf), JRSS-B.
- Brier skoru ve güvenilirlik tablosu, olasılık tahminlerinin standart değerlendirme araçlarıdır; Poisson bootstrap, klasik yeniden örneklemenin her gözleme bağımsız Poisson(1) ağırlık veren biçimidir. Bu iki yöntem için birincil kaynak taraması henüz yapılmadı; [ARASTIRMA.md](ARASTIRMA.md) içindeki teyit listesine eklenmeli.
