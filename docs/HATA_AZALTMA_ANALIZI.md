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
| 3 | Giderlerin kendi belirsizliği (bant giderleri kesin sayıyordu) | **İyimser** (kötümser çizgi güvensiz) | **Yapıldı (20.10).** Banka geçmişindeki 30 günlük gider toplamlarının dalgalanması banda katılıyor. Giderleri dalgalanan 120 işletmede kötümser uç aşımı %13,3'ten %9,2'ye, iyimser uç %16,7'den %10,8'e indi; Kupiec iki uçta da geçiyor |
| 4 | Henüz kesilmemiş satışlar | Satış düşerse iyimser | Ayrı sütunda, işletmenin kendi geçmiş satış hatalarından gelen belirsizlikle; laboratuvarda kalibre; kapatılabilir. **Yapıldı (20.10):** beklenen tahsilatın ne kadarının kesilmemiş satıştan geldiği açıkça yazılıyor |
| 5 | Geç tahsilat (müşterinin gerçek ödeme alışkanlığı) | İyimser | Fatura ve müşteri bazında model; çek vadesi, taksit, kayıt gecikmesi öğreniliyor; laboratuvarda Basel yeşil |
| 6 | Hiç tahsil edilemeyen alacak, müşteri yoğunlaşması | İyimser | Müşteri bazında temerrüt oranı; "en büyük müşterim geç öderse" senaryosu; tahsili zor alacaklar ayrı |
| 7 | Eski veriyle tahmin | İyimser | Tahsilat kayıt kesimi kayıtlardan tahmin ediliyor ve uyarı veriliyor |
| 8 | Mükerrer fatura | İyimser | Olası mükerrerler gösteriliyor |
| 9 | Kur değişimi (dövizli alacak bugünkü kurla TL'ye çevriliyordu; dövizli borç hiç okunmuyordu) | Alacakta TL değer kazanırsa, borçta TL değer kaybederse **iyimser** | **Yapıldı (20.10):** kur belirsizliği ECB kur geçmişinden banda katıldı; borç dosyasında döviz sütunu okunuyor. Her dövizde kasa aleyhine olan taraf esas alınıyor. Ayrıntı bölüm 7'de |
| 10 | Ödeme sözleri | Sözler tutulmazsa iyimser | Söz tarihi yeni vade sayılıyor, müşterinin gecikme alışkanlığı üstüne ekleniyor. **Yapıldı (20.10):** geçmiş sözlerin tutulma oranı ve en çok söz tutmayan müşteriler gösteriliyor |
| 11 | Karar sayısının seçimi | Orta değere bakılırsa iyimser | **Bugün eklendi:** "güvenle harcanabilir tutar" (%10'luk uçtan); haftalık tabloda kötümser sütun öne alındı |
| 12 | Tek tek işletmede kısa dönem sapması | İyimser olabilir | Çevrimiçi izleme ortalamada standart; pilot raporu her işletmeyi ayrıca Basel ve Kupiec ile sınıyor |
| 13 | Tahmin ile gerçekleşenin kalem bazında karşılaştırılması (AFP) | — | **Yapıldı (20.10):** her kasa kaydında açık faturalardan, yeni satışlardan beklenen tahsilat ve planlanan giderler ayrı saklanıyor; ufuk dolunca gerçekleşenle kalem kalem karşılaştırılıyor |
| 14 | Pazarlama iddiaları | Hukuki risk | Kural konuldu: gerçek veride bağımsız ölçüm olmadan doğruluk iddiası yok |
| 15 | Vergi ödeme gününün tatile denk gelmesi (panel yalnızca hafta sonunu biliyordu) | Tarih kayması (tutar değişmez) | **Yapıldı (20.10):** resmî tatiller eklendi (VUK m.18/4; Diyanet 2026–2027 listeleri) |
| 16 | Eski kasa tutarı (tahmin girilen tutardan başlar; eski tutar bütün çizgiyi kaydırır) | Kasa sonradan azaldıysa **iyimser** | **Yapıldı (20.10):** kasa tutarı tahmin gününden önce girildiyse ya da ekstre daha yeniyse uyarı; ekstredeki son bakiye girilen tutarın yanında gösteriliyor |
| 17 | Kasa tutarına kredi limiti (KMH, kredi kartı) ya da elde tutulan çeklerin yazılması | **İyimser** | **Yapıldı (20.10):** alanın açıklaması ve kılavuz, limitin, blokeli tutarın ve çeklerin dahil olmadığını yazıyor; çekler portföy dosyasından ayrıca sayıldığı için kasaya da eklenirse iki kez sayılır |

## 5. Bugün yapılanlar

1. **Banka ekstresi okuma hatası düzeltildi** (madde 1). Dört ekstre biçimi için test eklendi.
2. **Gider planı, banka geçmişiyle karşılaştırılıyor.** Eksik plan farkı "plan dışı ödemeler" olarak ekleniyor (madde 2). KVKK m.4/2-ç (ölçülülük) gereği çıkışların yalnızca tarihi ve tutarı saklanıyor; açıklamadaki çalışan ya da tedarikçi adı saklanmıyor. Çıkışlar pilot paketine girmiyor.
3. **"Güvenle harcanabilir" göstergesi eklendi** (madde 11): bugün bundan fazlası harcanırsa, 90 günde kasanın eksiye düşmesi 10 benzer durumun 1'inden sık olur. Haftalık tabloda kötümser sütun orta değerin önünde.
4. **Mevzuat kontrolüne eklendi:** reklam iddialarının ispat yükü (Yönetmelik m.9) ve iki yeni avukat sorusu.

## 6. 20 Ekim'in ikinci yarısında yapılanlar

1. **Gider belirsizliği** (madde 3). 30 günlük blok oranları, işletmenin kendi banka çıkışlarından öğreniliyor (en az 90 günlük geçmiş gerekir). Ortalama gider değişmez; yalnızca belirsizliği banda girer. Laboratuvara "aylık gider dalgalanması" boyutu eklendi (sürüm 6).
2. **Kötü durumda ortalama açık** (Basel FRTB'deki beklenen açık mantığı). En kötü 10 senaryonun ortalamasında kasanın ne kadar eksiye düştüğü, hazır tutulması gereken ek kaynağın bir ölçüsü olarak gösteriliyor.
3. **Yeni satış payı, ödeme sözü güvenilirliği, kalem bazında tahmin–gerçekleşen** (madde 4, 10, 13).

4. **Resmî tatiller** (madde 15). Muhtasar, KDV ve SGK ödeme günleri hafta sonuna ya da resmî tatile denk gelirse izleyen ilk iş gününe kayıyor. Dini bayram tarihleri her yıl Diyanet listesinden eklenmeli (MEVZUAT_KONTROLU.md, bölüm 5).
5. **Eski kasa tutarı uyarısı ve ekstre bakiyesi** (madde 16). Ekstrede bakiye sütunu varsa son bakiye ve tarihi, kasa tutarı alanının altında gösteriliyor. Kasadaki nakit ve başka bankalardaki hesaplar o tutara dahil olmadığından iki tutar otomatik eşitlenmiyor; karar kullanıcıda.

6. **Kur belirsizliği** (madde 9). Aşağıda.

## 7. Kur belirsizliği (20 Ekim 2026)

**Sorun.** İki eksik vardı:
- Dövizli fatura, kullanıcının girdiği bugünkü kurla TL'ye çevriliyordu; para hangi gün gelirse gelsin o kur sayılıyordu.
- Borç dosyasındaki döviz bilgisi okunmuyordu: 10.000 USD'lik tedarikçi faturası 10.000 TL sayılıyordu. Kasa çok dolu görünür.

**Ölçüm.** Veri: Avrupa Merkez Bankası (ECB) euro referans kurları, 2005–2026; USD/TRY çapraz kurdan türetildi. Her tahmin günü için yalnızca o güne kadarki kurlarla %10 ve %90 uçları kuruldu. Gerçekleşen kurun uçların dışına düşme sıklığı sayıldı. Tahmin günleri 2010'dan itibaren örtüşmeyen dönemler. Alt uç dövizli alacak için, üst uç dövizli borç için kötümser uçtur. Tam tablo, iki yarı ayrı ayrı: [lab/kur_sinamasi.md](lab/kur_sinamasi.md).

| Döviz, ufuk (2010–2026) | Kur sabit: TL karşılığı bugünkünden düşük | Sürüklenmesiz, bütün geçmiş: alt / üst aşım | Sürüklenmeli, son 3 yıl: alt / üst aşım |
|---|---|---|---|
| USD, 30 gün (204 dönem) | %29 | %5,4 / %14,7 | %6,4 / %10,8 |
| USD, 60 gün (102) | %26 | %3,9 / %23,5 | %8,8 / %12,7 |
| USD, 90 gün (68) | %24 | %4,4 / %23,5 | %7,4 / %11,8 |
| EUR, 30 gün (204) | %36 | %4,9 / %17,2 | %7,4 / %11,3 |
| EUR, 60 gün (102) | %25 | %3,9 / %23,5 | %6,9 / %14,7 |
| EUR, 90 gün (68) | %25 | %7,4 / %26,5 | %10,3 / %13,2 |

**Bulgular:**
- Kur sabit sayılınca dövizli alacağın TL karşılığı, dönemlerin dörtte biri ile üçte birinde bugünkünden düşük çıkıyor. Bu, kötümser çizgide hiç yoktu.
- İlk denenen yöntem ("sürüklenmesiz"), TL'nin geçmişteki ortalama değer kaybını çıkarıyordu. Alacak için ihtiyatlı: alt uç %4–7 aşılıyor. Borç için iyimser: üst uç %15–27 aşılıyor. Senaryoların çoğunda TL değer kazanıyor ve dövizli borç küçülüyor. Bu, dövizli borcu olan işletmeye hayal satmak olurdu; test bunu yakaladı.
- Borç tarafı için dört seçenek denendi. En iyisi "son 3 yılın kur hareketleri, değer kaybıyla birlikte": üst uç %11–15 aşılıyor. Seçim aynı veride yapıldığı için 2010–2017 ve 2018–2026 yarılarında ayrı ayrı bakıldı; iki yarıda da en iyi ya da en iyiyle eşit (%9–16).
- Hiçbir seçenek borç tarafında %10'u tam tutturmuyor. Kur sıçramaları (2018, 2021) geçmişten tam öğrenilemiyor. Kötümser çizgi borç ağırlıklı dövizde hâlâ hafif iyimser olabilir; panel bunu yazıyor.

**İkinci adım: borç tarafındaki fazlalığın giderilmesi.** İki yöntem önceden belirlenen bir kuralla sınandı. Seçim 2010–2017 verisiyle yapıldı; 2018–2026 sınav dönemine yalnızca bir kez bakıldı.
1. *Oynaklığa göre ölçekleme* (Hull ve White 1998; oynaklık RiskMetrics 1996, λ = 0,94). Seçim döneminde borç tarafında en kötü aşım %24,5 çıktı, mevcut yöntemde %16,3. Reddedildi. TL'deki risk oynaklığın kümelenmesinden çok ani sıçramalardan geliyor.
2. *Konformal genişletme* (Vovk, Gammerman ve Shafer 2005; ana kasa modelindeki `aggregate_widen` ile aynı mantık). Her tahmin gününde, 2007'den beri sonucu belli olmuş geçmiş tahminlerin aşım oranı hesaplanıyor. Bant, bu oran %10'u geçmeyecek kadar açılıyor. Yalnızca geçmiş veri kullanılıyor.

Konformal genişletmenin sınav dönemi (2018–2026) sonucu:

| Döviz, ufuk | Dönem | Borç tarafı aşımı, önce | Sonra | Ortalama katsayı |
|---|---|---|---|---|
| USD, 30 gün | 107 | %10,3 | %9,3 | 1,13 |
| USD, 60 gün | 53 | %13,2 | %7,5 | 1,13 |
| USD, 90 gün | 35 | %11,4 | %11,4 | 1,10 |
| EUR, 30 gün | 107 | %11,2 | %10,3 | 1,21 |
| EUR, 60 gün | 53 | %13,2 | %9,4 | 1,09 |
| EUR, 90 gün | 35 | %11,4 | %8,6 | 1,25 |
| **Toplam** | **390** | **%12,1** | **%9,5** | |

Alacak tarafı değişmedi (%2,9–5,7). Seçim döneminde katsayı ≈1 çıktı, çünkü 2007–2016'da aşımlar zaten %10'un altındaydı. Yöntem, risk arttığında kendini açıyor. Hiçbir ayar sınav verisine bakılarak yapılmadı. Yeniden üretmek için: `python tools/kur_konformal_sinamasi.py sinav`.

**Neden %0 değil, neden tam %10 değil?** Kötümser çizgi tanım gereği "10 durumun 1'inde altına inilen" çizgidir; %0 aşım, bandın gereksiz geniş, yani işe yaramaz olduğu anlamına gelir. 35 dönemde 4 aşım (%11,4), gerçek oran %10 olsa da sık görülür; bu sonucun %10'dan farklı olma olasılığı istatistiksel olarak anlamlı değil (tek yönlü binom testi p ≈ 0,47). Bu oranlar yalnızca kur bileşenine aittir: kasa tahmininin yüzde hatası değildir.

**Uygulanan kural** (`radar/fx.py`, `pipeline.fx_args`): her dövizde ufuktaki dövizli alacak ve borç karşılaştırılıyor; kasa aleyhine olan taraf esas alınıyor.
- **Alacak ağırlıklı:** sürüklenmesiz, bütün geçmiş. Kur farkının kasayı büyüteceğine güvenilmez.
- **Borç ağırlıklı:** sürüklenmeli, son 3 yıl. TL'nin değer kaybının sürdüğü varsayılır; borç büyür.

Uygulamanın ayrıntıları:
- Her senaryo için geçmişten bir başlangıç günü seçiliyor. Paranın geldiği ya da ödendiği günün kur oranı TL tutarla çarpılıyor.
- Aynı gruptaki dövizler için aynı gün seçiliyor, böylece dövizler arasındaki ilişki korunuyor.
- ECB tablosunda olmayan bir döviz kur sabit sayılarak kalıyor; panel uyarıyor.
- Borç dosyasında kuru girilmemiş döviz dışarıda bırakılmıyor (alacakta bırakılır, çünkü bırakmak ihtiyatlıdır). Tutar TL sayılıyor ve "DİKKAT" notu çıkıyor.
- Aynı kural gider dosyasındaki dövizli kalemlere ve döviz çeklerine de uygulanıyor. Kuru girilmemiş dövizli gider TL sayılıp uyarılıyor; kuru girilmemiş döviz çeki, bir giriş olduğu için tahmine katılmıyor. Net durum hesabında döviz çekleri alacak tarafında sayılıyor.
- Laboratuvar verisinde döviz olmadığı için laboratuvar sonuçları değişmiyor.
- **Kurların internetten güncellenmesi.** Panelde "Kurları ECB'den güncelle" düğmesi var. Yalnızca kullanıcı basınca çalışıyor ve yalnızca ECB'nin resmî adresine gidiyor; işletme verisi gönderilmiyor. İndirilen dosya kullanılmadan önce denetleniyor: biçim, uzunluk, pozitif değerler, tarih sırası, %40'tan büyük günlük sıçrama yok, paketteki tablodan eski değil. Sorun varsa paketteki kurlarla devam ediliyor.
- **Eski kur uyarısı.** Girilen kur ECB'nin son kurundan, son 3 yılda kurun bir ayda gösterdiği olağan hareketten (%90'lık değişim, bugün yaklaşık %2,7) fazla farklıysa panel uyarıyor. "ECB kurlarını alana yaz" düğmesi son kurları alana yazıyor; kullanıcı bankasının kuruyla değiştirebiliyor.

**Kullanım koşulu.** ECB internet sitesindeki Copyright bölümüne göre bilgiler, ECB kaynak gösterilerek serbestçe kullanılabilir. Değişiklik yapıldıysa bu belirtilmeli; ücretli bir belgede alıcıya verinin ECB sitesinden ücretsiz edinilebileceği bildirilmeli. Panel bu notu gösteriyor. ECB, kurların yalnızca bilgi amaçlı olduğunu ve işlemlerde kullanılmamasını yazıyor. Burada kurlar dönüşüm için değil, yalnızca geçmiş dalgalanmayı ölçmek için kullanılıyor; dönüşümde kullanıcının girdiği kur geçerli.

## 8. Kalan açık konular

1. Tek işletmede kısa dönem sapması (madde 12). Pilot raporu her işletmeyi ayrıca sınıyor; gerçek veriyle izlenecek.
2. Gerçek Türk KOBİ verisi. Bütün bu sonuçlar sentetik ya da yabancı açık veriyle; son hakem pilot.
3. Kur: borç tarafı konformal genişletmeden sonra sınav döneminde %9,5 (bölüm 7). ECB'nin yayımlamadığı dövizler (ör. AED, SAR, RUB) için kur geçmişi yok; bunlar sabit kurla sayılıyor ve panel uyarıyor. TCMB'nin günlük kurları resmî kur olarak daha uygun olurdu, ama ticari kullanım TCMB'nin yazılı iznine bağlı; izin alınırsa eklenebilir.

## 9. Yasal uyum notu

Bugünkü değişikliklerin hiçbiri yeni bir kişisel veri amacı yaratmıyor. Banka çıkışlarından kimlik bilgisi saklanmıyor (KVKK m.4/2-ç). "Güvenle harcanabilir tutar" bir karar destek göstergesi; yatırım ya da finansal danışmanlık sayılmayacak biçimde nasıl ifade edileceği avukata soruldu (MEVZUAT_KONTROLU.md, soru 22). Tanıtımda doğruluk iddiası kullanılmaması kuralı da aynı belgede (soru 21). ECB kur verisinin kullanım koşulları MEVZUAT_KONTROLU.md'ye ve LISANSLAR.md'ye işlendi.
