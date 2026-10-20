# Hata azaltma analizi: kaynaklar, benzer ürünler, eksiklerimiz

Tarih: 20 Ekim 2026.

## 1. Temel soru ve görüşüm

**Soru.** Küçük bir işletme için kasanın biraz eksik görünmesi, şişkin görünüp işletmenin buna güvenerek harcama yapmasından daha iyidir. Bu doğru mu, ve sistem buna göre nasıl kurulmalı?

**Görüşüm: Evet, maliyetler asimetrik.** Kasayı olduğundan dolu göstermek, maaşın ödenememesi, çekin karşılıksız kalması ya da pahalı acil kredi demektir. Kasayı biraz eksik göstermenin bedeli ise ertelenmiş bir harcama ya da gereksiz bir telefon görüşmesidir. Ama bunu tahmini bilerek aşağı çekerek sağlamak yanlış olur. Bunun üç nedeni var:

1. **Mevzuat.** KGK Kavramsal Çerçeve md. 142'ye göre ihtiyatlılık, belirsizlik altında temkinli davranmaktır: varlıklar ve gelirler olduğundan yüksek, giderler olduğundan düşük gösterilmez. Ama aynı madde gelirlerin kasten düşük gösterilmesine izin vermez, çünkü o zaman bilgi tarafsız ve güvenilir olmaz. 1 Sıra No.lu Muhasebe Sistemi Uygulama Genel Tebliği'ndeki ihtiyatlılık kavramı da aynıdır: muhtemel gelir ve kârlar gerçekleşene kadar kayda alınmaz, ama kavram gizli yedek ya da aşırı karşılık için gerekçe yapılamaz.
2. **Bilim.** Maliyetler asimetrikse en iyi tek sayılık tahmin, tahmin dağılımının maliyet oranına karşılık gelen yüzdeliğidir (Gneiting 2011, "Quantiles as optimal point forecasts"; Patton ve Timmermann 2007). Doğru yöntem iki adımlıdır. Önce dağılım dürüst kurulur: %10'luk kötümser senaryo gerçekten %10 olasılıkla aşılmalıdır. Sonra karar kötümser uçtan verilir. %10'luk uçtan karar vermek, kasayı fazla göstermenin eksik göstermekten 9 kat pahalı sayılması demektir. Basel de risk ölçümünü dağılımın riskli ucundan yapar; 2016'daki piyasa riski reformu (FRTB), uçtaki kaybın büyüklüğünü de görmek için tek bir yüzdelikten beklenen açığa geçmiştir.
3. **Kullanıcı davranışı.** Hep kötümser çıkan bir araç bir süre sonra dikkate alınmaz. Uyarılar sıradanlaşır ve gerçek tehlike geldiğinde de görmezden gelinir; bu, ters köşenin öbür yüzüdür. Hava tahmini araştırmalarında, belirsizliği dürüstçe gösterilen tahminlerle insanların daha iyi karar verdiği bulunmuştur (Joslyn ve LeClerc 2012). Olasılıklar "10 benzer durumun 1'inde" biçiminde anlatıldığında da daha doğru anlaşılır (Gigerenzer ve Hoffrage 1995).

**Sonuç olarak tasarım kuralı şu:**
- Bant dürüst kalır: Basel, Kupiec ve Spiegelhalter testleriyle ölçülür.
- Karar sayıları kötümser uçtan gösterilir ("güvenle harcanabilir tutar", kötümser çizgi).
- Asıl iyimserlik kaynakları veri düzeyinde kesilir: kaydedilmemiş giderler, gerçekleşmemiş satışlar, yanlış okunan banka hareketleri.

Analizin en önemli bulgusu da bu son maddede çıktı.

## 2. Taranan kaynaklar

| Kaynak | Ne söylüyor | Bizim için anlamı |
|---|---|---|
| [AFP, "10 Best Practices in Cash Forecasting"](https://www.financialprofessionals.org/training-resources/resources/articles/Details/10-Best-Practices-in-Cash-Forecasting) | Tahmin ile gerçekleşen her dönem kalem bazında karşılaştırılır; doğruluk ölçütü baştan kararlaştırılır; her tahsilat ve ödeme türünün öngörülebilirliği ayrı anlaşılır | Pilot kayıtları ve ölçütler var. Kalem bazında karşılaştırma (açık faturalar, yeni satışlar, giderler) panelde yok: **eksik** |
| [Gneiting 2011, IJF 27(2)](https://ideas.repec.org/a/eee/intfor/v27y2011i2p197-207.html) | Asimetrik maliyette en iyi tek sayı, maliyet oranına karşılık gelen yüzdeliktir | "Güvenle harcanabilir tutar" %10'luk uçtan hesaplanır (bugün eklendi) |
| KGK Kavramsal Çerçeve md. 142 (kgk.gov.tr) | İhtiyatlılık: gelir yüksek, gider düşük gösterilmez; ama kasten düşük gösterme de yok | Bant tarafsız, karar temkinli. Giderlerin eksik kalmaması için banka geçmişiyle karşılaştırma eklendi |
| 1 Sıra No.lu Muhasebe Sistemi Uygulama Genel Tebliği (RG 26.12.1992, 21447 mük.), ihtiyatlılık kavramı | Muhtemel gelirler gerçekleşmeden kaydedilmez | Henüz kesilmemiş satışlar ayrı gösterilir ve kapatılabilir |
| [HM Treasury Green Book, "Optimism bias" ek rehberi](https://www.gov.uk/government/publications/green-book-supplementary-guidance-optimism-bias) | Tahmin yapanlar sistematik olarak iyimserdir; geçmiş benzer projelerin sonuçlarına dayanan açık düzeltme yapılmalıdır (referans sınıfı tahmini) | Bizim karşılığımız: düzeltme sabit bir yüzdeyle değil, işletmenin kendi geçmiş hatalarından (konformal ayar, çevrimiçi izleme) yapılır |
| [Cooper, Woo ve Dunkelberg 1988, J. Business Venturing 3](https://gwern.net/doc/psychology/cognitive-bias/1988-cooper.pdf) | 2.994 yeni işletme sahibinin %81'i başarı şansını 10'da 7 ya da üstü gördü; hazırlıksız olanlar da aynı iyimserlikteydi | Kullanıcının elle girdiği tahminler (ödeme sözü, beklenen satış) iyimser olabilir; araç bunları kendi geçmişiyle sınamalıdır |
| [Joslyn ve LeClerc 2012, J. Exp. Psych.: Applied 18](https://www.sci.utah.edu/~kpotter/Library/Papers/joslyn:2012:UFID/index.html) | Belirsizlik bilgisi verilince kararlar iyileşir | Tek sayı değil, bant ve olasılık gösterilir |
| [Makridakis vd. 2022, M5 belirsizlik yarışması](https://www.insead.edu/faculty-research/publications/journal-articles/m5-uncertainty-competition-results-findings-and) | Olasılıklı tahminler yüzdelik kaybıyla (pinball) değerlendirilir; en iyi ekiplerin çoğu gradyan artırmalı ağaçlarla yüzdelik tahmin etti | Yöntemimiz (LightGBM yüzdelik modeli + aralık skoru) bu çizgide |
| Basel BCBS piyasa riski çerçevesi (FRTB) | Riskli uçta tek bir yüzdelik (VaR) yerine uçtaki ortalama kayıp (beklenen açık) | Sıradaki iş: "kötü durumda ortalama açık" göstergesi |
| Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği m.9 (RG 04.01.2017, 29938) | Reklamdaki iddiaların doğruluğunu reklam veren ispatlar; karşılaştırmalı iddialar bağımsız kuruluş raporuyla | Ürün için "%X doğruluk" ya da rakiplerle karşılaştırma iddiası gerçek veride bağımsız ölçüm olmadan kullanılmaz |

## 3. Benzer ürünler hataları önlemek için ne yapıyor

| Ürün | Yaklaşım | Not |
|---|---|---|
| HighRadius | Fatura bazında ödeme günü tahmini (karar ağaçları, rastgele orman); müşteri bazında model; tahmin ile gerçekleşen farkından öğrenen kapalı döngü | Bizim fatura bazındaki yaklaşımımız ve çevrimiçi izlememiz aynı mantıkta. Doğruluk ölçüm yöntemi yayımlanmamış |
| Kyriba | Pilotlarda ödeme günü sapmasının 25 günden 5 güne indiği bildirildi | Tanım ve örneklem belirsiz |
| Float, Fathom, Agicap, Pulse | Banka ve muhasebe bağlantılı, sürekli güncellenen 13 haftalık tahmin; Agicap müşterinin kendi tahsil süresini kullanır | İnceleme sitelerindeki "%80–97 doğruluk" iddialarının hiçbiri yöntem göstermiyor |
| Paraşüt | Geçmiş verilere dayanan gelecek dönem tahmini | Yöntem ayrıntısı bulunamadı |
| Logo (Netsis "Görsel Nakit Akış") | Planlanan gelir ve giderlerden tahmini nakit akışı | Olasılık ve belirsizlik yok; ERP düzeyi |
| BizimHesap, Mikro | Cari hesap ve tahsilat takibi | Nakit tahmini özelliği bulunamadı |

Ortak noktalar şunlar: fatura bazında ödeme tahmini, banka ve muhasebe verisiyle sürekli güncelleme, tahmin ile gerçekleşenin karşılaştırılması. **Hiçbiri doğruluğunu ölçüm yöntemiyle birlikte yayımlamıyor.** Bizim farkımız, sonuçlarımızın uluslararası testlerle (Basel, Kupiec, Diebold-Mariano, Spiegelhalter) ve olumsuz bulgularıyla birlikte açık olması. Bu, aynı zamanda reklam mevzuatının istediği kanıt düzeni.

## 4. Hata kaynakları: yön, durumumuz ve yapılacaklar

"Yön" sütunu, hatanın kasayı şişirip şişirmediğini gösteriyor. İyimser hatalar öncelikli.

| # | Hata kaynağı | Yön | Durum (20.10.2026) |
|---|---|---|---|
| 1 | **Banka ekstresinde çıkışların tahsilat sayılması** (işaretli tutarlı ekstrelerde "−15.000" kira ödemesi 15.000 tahsilat oluyordu) | **İyimser, çok tehlikeli** | **Bugün bulundu ve düzeltildi.** Yön, sırasıyla B/A sütunundan, Borç/Alacak sütunlarından, eksi işaretten ve bakiye değişiminden çıkarılıyor; hiçbiri yoksa uyarı veriliyor |
| 2 | **Gider planının eksik olması** (unutulan vergi, SGK, kredi taksidi, tedarikçi) | **İyimser** | **Bugün eklendi.** Son 90 günün gerçek banka çıkışları planla karşılaştırılıyor; plan geçmişin altındaysa fark "plan dışı ödemeler (tahmini)" olarak kasaya ekleniyor (ayardan kapatılabilir) |
| 3 | Giderlerin kendi belirsizliği (bant giderleri kesin sayıyor) | İyimser uç dar | **Açık.** Sıradaki iş: banka geçmişindeki aylık gider dalgalanmasının banda katılması |
| 4 | Henüz kesilmemiş satışlar | Satış düşerse iyimser | Ayrı sütunda, işletmenin kendi geçmiş satış hatalarından belirsizlikle; laboratuvarda kalibre; kapatılabilir. Ek iş: tahsilatın ne kadarının kesilmemiş satıştan geldiğinin üstte gösterilmesi |
| 5 | Geç tahsilat (müşterinin gerçek ödeme alışkanlığı) | İyimser | Fatura ve müşteri bazında model; çek vadesi, taksit, kayıt gecikmesi öğreniliyor; laboratuvarda Basel yeşil |
| 6 | Hiç tahsil edilemeyen alacak, müşteri yoğunlaşması | İyimser | Müşteri bazında temerrüt oranı; "en büyük müşterim geç öderse" senaryosu; tahsili zor alacaklar ayrı |
| 7 | Eski veriyle tahmin | İyimser | Tahsilat kayıt kesimi kayıtlardan tahmin ediliyor ve uyarı veriliyor |
| 8 | Mükerrer fatura | İyimser | Olası mükerrerler gösteriliyor |
| 9 | Kur değişimi | İki yönlü | Kur senaryosu var; kur belirsizliği banda girmiyor (açık) |
| 10 | Ödeme sözleri | Sözler tutulmazsa iyimser | Söz tarihi yeni vade sayılıyor, müşterinin gecikme alışkanlığı üstüne ekleniyor. Ek iş: tutulmayan sözlerin oranının izlenmesi |
| 11 | Karar sayısının seçimi | Orta değere bakılırsa iyimser | **Bugün eklendi:** "güvenle harcanabilir tutar" (%10'luk uçtan); haftalık tabloda kötümser sütun öne alındı |
| 12 | Tek tek işletmede kısa dönem sapması | İyimser olabilir | Çevrimiçi izleme ortalamada standart; pilot raporu her işletmeyi ayrıca Basel ve Kupiec ile sınıyor |
| 13 | Tahmin ile gerçekleşenin kalem bazında karşılaştırılması (AFP) | — | **Açık:** pilotta toplam düzeyde var, kalem bazında yok |
| 14 | Pazarlama iddiaları | Hukuki risk | Kural konuldu: gerçek veride bağımsız ölçüm olmadan doğruluk iddiası yok |

## 5. Bugün yapılanlar

1. **Banka ekstresi okuma hatası düzeltildi** (madde 1). Dört ekstre biçimi için test eklendi.
2. **Gider planı, banka geçmişiyle karşılaştırılıyor.** Eksik plan farkı "plan dışı ödemeler" olarak ekleniyor (madde 2). KVKK m.4/2-ç (ölçülülük) gereği çıkışların yalnızca tarihi ve tutarı saklanıyor; açıklamadaki çalışan ya da tedarikçi adı saklanmıyor. Çıkışlar pilot paketine girmiyor.
3. **"Güvenle harcanabilir" göstergesi eklendi** (madde 11): bugün bundan fazlası harcanırsa, 90 günde kasanın eksiye düşmesi 10 benzer durumun 1'inden sık olur. Haftalık tabloda kötümser sütun orta değerin önünde.
4. **Mevzuat kontrolüne eklendi:** reklam iddialarının ispat yükü (Yönetmelik m.9) ve iki yeni avukat sorusu.

## 6. Sıradaki işler (öncelik sırasıyla)

1. **Gider belirsizliğinin banda katılması** (madde 3). Banka geçmişindeki aylık çıkış dalgalanması, plan dışı ödemelerin belirsizliği olarak simülasyona girecek.
2. **"Kötü durumda ortalama açık" göstergesi** (Basel FRTB'deki beklenen açık mantığı). Eksiye düşme olasılığının yanında, düşülürse ne kadar derin olacağı gösterilecek.
3. **Kalem bazında tahmin–gerçekleşen karşılaştırması** (AFP). Pilot kayıtlarında açık faturalar, yeni satışlar ve giderler ayrı izlenecek.
4. **Tahsilatın kesilmemiş satıştan gelen payının üstte gösterilmesi** ve tutulmayan ödeme sözlerinin oranının izlenmesi.

## 7. Yasal uyum notu

Bugünkü değişikliklerin hiçbiri yeni bir kişisel veri amacı yaratmıyor. Banka çıkışlarından kimlik bilgisi saklanmıyor (KVKK m.4/2-ç). "Güvenle harcanabilir tutar" bir karar destek göstergesi; yatırım ya da finansal danışmanlık sayılmayacak biçimde nasıl ifade edileceği avukata soruldu (MEVZUAT_KONTROLU.md, soru 22). Tanıtımda doğruluk iddiası kullanılmaması kuralı da aynı belgede (soru 21).
