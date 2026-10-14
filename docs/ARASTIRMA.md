# Yol Haritası Raporunun Denetimi ve Araştırma Bulguları

Tarih: 14 Ekim 2026. İncelenen belge: "KOBİ Nakit Akışı Radarı ve Otonom Tahsilat Ajanı" (5 sayfa).

Raporun ana fikri sağlam: Türkiye'de geç ödeme yaygın, finansman pahalı ve KOBİ'nin elinde olasılıksal bir nakit görünümü yok. Aşağıdaki maddeler fikri değil, raporun dayanaklarını ve kurgusunu düzeltiyor. Her maddede kaynağın ne kadar güvenilir olduğunu belirttim; doğrulayamadığım yerleri açıkça yazdım.

## Kaynak güvenilirliği ve çalışma kuralı

Bu proje gerçek kullanım için geliştiriliyor; bu yüzden her iddia, dayandığı kaynağın düzeyiyle birlikte okunmalı.

| Düzey | Tanım | Bu belgedeki örnekler |
|---|---|---|
| A | Hakemli yayın veya resmî birincil kaynak | Zeng vd. (KDD 2008), Barrot (JF 2016), Jacobson ve von Schedvin (Econometrica 2015), Klapper vd. (RFS 2012), Murfin ve Njoroge (RFS 2015), Hallsworth vd. (JPubE 2017), Makridakis vd. (IJF 2022), Gneiting vd. (JRSS-B 2007), Springer 2024 sağkalım çalışması, Meta geliştirici belgeleri |
| B | Kurumsal araştırma raporu veya üreticinin kendi ürün sayfası | Atradius, Intrum, JPMorgan Chase Institute; Agicap, Upflow, Finrota sayfaları (yalnızca "bu özellik var" bilgisi için; performans iddiaları için değil) |
| C | İkincil kaynak: haber, blog, derleme sitesi, hakemsiz ön baskı | Ticari kredi faizi, karşılıksız çek, temerrüt faizi, 60 gün kuralı, lisans sayısı, ileti yönetmeliği, rakip fiyatları, arXiv ön baskıları |

Kural: ürün ve model kararları yalnızca A düzeyine dayanır. B düzeyi pazarın durumunu anlamak için kullanılır. C düzeyindeki hiçbir rakam ürün metnine, satış sunumuna ya da mesaj şablonuna birincil kaynaktan teyit edilmeden girmez.

Birincil kaynak teyidinin durumu (14 Ekim 2026):

| Bilgi | Durum | Birincil kaynak |
|---|---|---|
| 2026 temerrüt faizi %43,00 ve asgari giderim 2.020,00 TL | Teyit edildi | [TCMB, TTK Md. 1530 tablosu](https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Istatistikler/Piyasa+Verileri/TTK+Md.+1530); tebliğ 2 Ocak 2026 tarihli Resmî Gazete'de |
| 60 gün vade sınırı | Teyit edildi, ifade düzeltildi | [6102 sayılı TTK m.1530/5](https://www.mevzuat.gov.tr/mevzuatmetin/1.5.6102.pdf): alacaklı KOBİ veya tarımsal/hayvansal üretici ise **ya da** borçlu büyük ölçekli işletme ise vade 60 günü aşamaz. İlk notumdaki "alacaklı KOBİ ve borçlu büyük" ifadesi kanundan dardı. |
| Vade yazmıyorsa temerrüt | Yeni bulgu | Aynı madde: ödeme günü belirtilmemişse borçlu, faturanın alınmasından 30 gün sonra ihtarsız temerrüde düşer. Vadesi olmayan faturada 30 gün varsayımı buna dayanıyor. |
| Borç hatırlatma mesajında onay istisnası | Teyit edildi | [Ticaret Bakanlığı](https://ticaret.gov.tr/ic-ticaret/ticari-elektronik-iletiler/genel-bilgiler) ve [yönetmelik metni](https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=20914&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5), m.6/2: tahsilat ve borç hatırlatma bildirimlerinde önceden onay aranmaz, tanıtım yapılamaz. Yürürlükteki son hâli avukatla teyit edilmeli. |
| Karşılıksız çek tutarı ve oranı | Kısmen | [TBB Risk Merkezi](https://www.riskmerkezi.org/istatistiki-raporlar/2544) Ağustos 2026 bültenini yayımlamış; rakamları bültenden doğrudan okuyamadım, haber aktarımına dayanıyor. |
| Açık bankacılık lisans sayısı | Kısmen | [TCMB ödeme kuruluşları listesi](https://www.tcmb.gov.tr/wps/wcm/connect/tr/tcmb+tr/main+menu/temel+faaliyetler/odeme+hizmetleri/odeme+kuruluslari) mevcut; (f) ve (g) bendi sayımını yapamadım. Lisans gerektiği kesin, sayı kesin değil. |
| TL ticari kredi faizi (%49,23) | Teyit edilmedi | TCMB EVDS haftalık kredi faiz serisi |
| Aralıkların dar kalması bulgusu | Teyit edilmedi | Hyndman, Koehler, Snyder, Grose (IJF 2002) makalesinin tam metni; elimdeki kaynak yazarın kendi blogu |
| Rakip fiyatları | Teyit edilmedi | Üreticiden teklif |

Koddaki %3,4 çek karşılıksızlık oranı bu yüzden hâlâ "varsayılan" bir parametredir. %43 ve 2.020 TL birincil kaynaktan teyitlidir ve her 1 Ocak'ta güncellenmelidir.

## 1. Raporda düzeltilmesi gereken iddialar

| Rapordaki iddia | Bulgu | Sonuç |
|---|---|---|
| "Açık bankacılık sayesinde sıfır regülasyon engeli" | Hesap bilgisi hizmeti 6493 sayılı Kanun m.12/1-g kapsamında TCMB iznine tabi. Ocak 2025 itibarıyla lisanslı kuruluş sayısı 17; ÖHVPS altyapısında 53 katılımcı var. | Banka verisini kendimiz çekemeyiz. MVP'de CSV/Excel doğru karar; sonrası için lisanslı bir sağlayıcıyla ortaklık gerekir. |
| "Agicap: tahsilat otomasyonu yok" | Agicap'in CashCollect modülü e-posta, mektup ve telefon içeren tahsilat planları, müşteri risk analizi ve hatırlatma e-postası yazan bir yapay zekâ ajanı sunuyor. | Yanlış. |
| "Upflow: statik vade dilimleri" | Upflow AI "Next Best Action" önerileri ve riskli müşteri tespiti sunuyor. Fatura bazında ödeme tarihi tahmini yaptığını doğrulayamadım. | Kısmen yanlış. |
| Yerli rakip olarak yalnızca Figopara | Finrota üç ürünle aynı alanda: Netekstre (açık bankacılık, hesap konsolidasyonu), NAP360 (nakit akış tahmini, senaryo), Netahsilat (online tahsilat). Paraşüt, Mikro ve Fiscus AI da tahsilat ve nakit takibi sunuyor. | En yakın yerli rakip matriste yok. |
| "Mevcut araçlar pasif, bizimki eyleme geçiyor" | Globalde otonom tahsilat ajanları artık ayrı bir kategori (Monk, Kolleno, Chaser, HighRadius). | Fark "ajan olması" değil; aşağıda 4. bölüme bakın. |
| "-%34 DSO azalımı" | Raporda kaynağı yok; bağımsız bir kaynak bulamadım. Agicap'in kendi beyanı %10 DSO azalması. | Hedef değil, pilotta ölçülecek hipotez olarak yazılmalı. |
| "Microsoft Research ve IEEE (2020–2024)" | Doğrulanabilen temel çalışmalar: Zeng vd. 2008 (IBM, KDD), arXiv 1912.10828 (en fazla %77 doğruluk) ve arXiv 2008.07363. 1912.10828'in Microsoft'a ait olduğunu doğrulayamadım. | Atıf düzeltilmeli. |
| "%45+ ticari kredi faizi" | TCMB haftalık akım verisi, 2 Ekim 2026 haftası: TL ticari kredilerde %49,23 (yeni kullandırımlar; KMH ve kurumsal kart hariç). | Yön doğru; rakam ve seri adı belirtilmeli. |
| "MAE < 4,5 gün" başarı ölçütü | Sentetik veride bu sayı, veriyi üreten parametrelerin sonucudur; gerçek performans hakkında bir şey söylemez. | Ölçüt "basit tahmine göre iyileşme ve bandın isabeti" olmalı. |

## 2. Modelleme kurgusundaki eksikler

**Gaussyen gürültü varsayımı.** Ödeme gecikmeleri sağa çarpıktır: çoğu fatura vadeye yakın ödenir, bir kısmı çok geç ödenir. Simetrik gürültü kuyruğu olduğundan dar gösterir. Hyndman'ın bulgusu bu riski somutlaştırıyor: zaman serisi modellerinde nominal %95'lik aralıklar pratikte %71–87 kapsama sağlıyor, çünkü yalnızca rastgele hata hesaba katılıyor. Gneiting, Balabdaoui ve Raftery'nin (2007) ilkesi: önce kalibrasyon, sonra keskinlik.

**Bağımsızlık varsayımı.** Rapordaki kurgu her faturayı ayrı ayrı sallıyor. Oysa aynı müşterinin faturaları birlikte gecikir ve sıkışık dönemde herkes aynı anda geç öder. Jacobson ve von Schedvin (Econometrica, 2015) müşteri iflaslarının tedarikçilere yayıldığını ve bunun toplam iflas sıklığının önemli bir parçası olduğunu gösteriyor. Bağımsız çekilen 1000 senaryo, kötü senaryonun derinliğini küçümser.

**Açık faturanın yaşı.** Vadesi 40 gün geçmiş bir fatura için "vade + tahmini gecikme" geçmişte bir tarih verebilir. Dağılımın "bugüne kadar ödenmedi" koşuluna göre kırpılması gerekir. Raporda bu yok.

**Sansürlü veri.** Yeni faturaların yalnızca hızlı ödenenleri "ödendi" olarak görünür. Hepsini eğitime katmak modeli iyimser yapar. Literatür bu problemi büyük ölçüde sağkalım analiziyle ele alıyor (2024 tarihli ayrık zamanlı sağkalım çalışması, terim bazlı tahminlerden ve sınıflandırma modellerinden daha isabetli sonuç bildiriyor).

**Soğuk başlangıç.** KOBİ'de müşteri başına üç beş fatura olur. Müşteri bazlı ortalama ve varyans bu kadar veriyle güvenilmezdir; piyasa ortalamasına doğru büzme gerekir.

**Kesilmemiş faturalar.** 90 günlük kasa tahmini yalnızca bugünkü açık faturalara bakarsa ufkun ikinci yarısında girişler yapay biçimde düşer ve yanlış alarm üretir.

**Yöntem seçimi.** M5 belirsizlik yarışmasında (Makridakis vd., 2022) katılımcılar dokuz kantil tahmin etti ve gradyan artırmalı ağaçlar öne çıktı; LightGBM en yaygın kullanılan araçtı. Yani LightGBM doğru araç, ama nokta tahmin + gürültü yerine doğrudan kantil hedefiyle kullanılmalı.

## 3. Türkiye'ye özgü, raporda hiç geçmeyen konular

**Çek ve senet.** 2026'nın ilk sekiz ayında bankalara ibraz edilen çeklerin tutarı 7,48 trilyon TL. Aynı dönemde 223.912 çek karşılıksız çıktı; tutarı 233 milyar TL, yıllık artış %56 (TBB Risk Merkezi verisi, haber kaynağı üzerinden). Türkiye'de alacağın önemli kısmı havaleyle değil vadeli çekle kapanıyor; rapor yalnızca fatura ve banka ekstresi görüyor. Çek portföyü (vade, keşideci, ciro) ayrı bir nakit giriş kaynağı olarak modellenmeli.

**Cari hesap çalışma biçimi.** Ödemeler çoğunlukla fatura bazında değil "cari hesaba mahsuben" ve kısmi gelir. Raporun "VKN ve tutar eşleşmesi" kurgusu bu durumda çalışmaz; ayrıca banka açıklamalarında VKN çoğu zaman bulunmaz.

**E-faturada vade tarihi.** UBL-TR'de ödeme vadesi alanlarının genel e-faturada zorunlu olduğunu doğrulayamadım; bulduğum zorunluluk kuralları yalnızca kamuya kesilen faturalara ait. Ayrıştırıcı, vade alanı boş faturayı beklenen durum saymalı. Faturalara erişim de GİB'den değil, özel entegratörlerin API'leri üzerinden olur.

**Geç ödeme hukuku (TTK m.1530).** 2026 için TCMB'nin ilan ettiği gecikme faizi yıllık %43, asgari tahsil gideri 2.020 TL. Alacaklı KOBİ ise ya da borçlu büyük ölçekli işletmeyse vade 60 günü aşamaz; vade yazmıyorsa borçlu faturanın alınmasından 30 gün sonra ihtarsız temerrüde düşer. Bu, mesajlarda kullanılabilecek gerçek bir dayanak. Buna karşılık rapordaki "sevkiyatın askıya alınacağını belirten Hukuki Ön İhtar" şablonunun otomatik üretilmesi risklidir; resmî dildeki mesajlar hukukçu kontrolünden geçmeli.

**İleti mevzuatı.** Ticari elektronik ileti yönetmeliğine göre borç hatırlatma ve tahsilat bildirimleri için önceden onay aranmıyor, ancak mesaj tanıtım içeremez. Tacir alıcıların ret hakkı var. Kişisel e-posta adresine giden mesaj bireysel alıcı sayılabilir. Bulduğum yönetmelik metni 2015 tarihli; güncel hâli teyit edilmeli. KVKK tarafında hukuki dayanak ayrıca değerlendirilmeli.

**WhatsApp.** Otomatik gönderim için WhatsApp Business Platform (API), bir çözüm sağlayıcı ve Meta onaylı şablon gerekir. Ödeme hatırlatması Meta'nın hazır "utility" şablonları arasında var. Hukuki yaptırım tehdidi içeren metinlerin onaydan geçip geçmeyeceğini doğrulayamadım.

## 4. Pazar ve akademik dayanak

**Sorunun büyüklüğü.** Atradius 2025 Türkiye özeti: B2B faturaların %65'i vadesinde ödenmiyor, faturaların ortalama %10'u şüpheli alacağa dönüyor. Atradius 2026 (haber aktarımı): satışların %41'i vadeli, şirketlerin %86'sı geç ödeme alıyor. Intrum 2026: Avrupa'da işletmelerin %62'si, müşterisi geç ödediği için kendi tedarikçisine geç ödüyor.

**Geç ödemenin KOBİ'ye etkisi (nedensel kanıt).**
- Barrot (Journal of Finance, 2016): Fransa'da nakliyecilerin verdiği vadeyi kısıtlayan reformdan sonra temerrüt olasılığı %25 düştü; etki likiditesi kısıtlı firmalarda yoğunlaştı.
- Murfin ve Njoroge (RFS, 2015): büyük perakendeciler ödemeyi yavaşlattığında küçük tedarikçilerin yatırımı düşüyor; etki kredi koşulları sıkıyken daha sert.
- Klapper, Laeven ve Rajan (RFS, 2012): yaklaşık 30.000 sözleşmede en uzun vadeleri en büyük ve en kredibil alıcılar alıyor; erken ödeme iskontosu daha riskli alıcılara sunuluyor.
- Petersen ve Rajan (1997) ile Meltzer (1960): raporun dayandığı ikame hipotezi; atıflar doğru.

**Nakit tamponu.** JPMorgan Chase Institute (2016): medyan küçük işletmenin 27 günlük nakit tamponu var; dörtte birinde 13 gün veya daha az. ABD verisidir, Türkiye için karşılığını bulamadım.

**Kullanılmaması gereken istatistik.** "Küçük işletmelerin %82'si nakit akışı yüzünden batıyor" iddiasının özgün çalışmasına ulaşılamıyor; atıflar birbirini tekrar ediyor.

**Tahsilat mesajı tasarımı.** Hallsworth, List, Metcalfe ve Vlaev (Journal of Public Economics, 2017): 200.000'den fazla mükellefle yapılan saha deneyinde hatırlatma mektubuna "çoğunluk zamanında ödüyor" türü betimleyici norm cümlesi eklemek ödemeyi hızlandırdı; kayıp çerçevesi kazanç çerçevesinden daha etkili çıkmadı. Bu bulgu vergi borcuna dair; B2B alacakta aynı etkinin görüleceği ayrıca sınanmalı.

**Rakiplerde durum.**
- Xero ve QuickBooks 30–90 günlük kısa vadeli nakit tahmini ve fatura ödeme tahmini sunuyor; bant değil tek çizgi gösteriyorlar ve Türkiye'de yoklar.
- Kolleno kullanıcı başına aylık yaklaşık 650 £'dan, Chaser aylık 199 £'dan başlıyor (derleme sitelerinden; teyit edilmeli). KOBİ fiyatında otonom ajan sunan az.
- Bulabildiğim hiçbir üründe "kasanın eksiye düşme olasılığı" ile "bu açığı kapatacak faturalar" tek akışta birleşmiyor. Savunulabilir fark burada: olasılıksal kasa görünümü, Türkiye'nin ödeme araçları (çek, cari hesap, WhatsApp) ve KOBİ fiyatı.

**Uzman görüşü konusunda sınır.** Türkiye'den bu konuda adıyla anılabilecek bir akademisyenin güncel ve doğrudan görüşünü bulamadım; basındaki değerlendirmeler köşe yazısı ve sektör haberi düzeyinde. Bu boşluk gerçek uzman görüşmesiyle kapatılmalı (mali müşavir, bir bankanın nakit yönetimi ekibi, ticaret hukuku avukatı).

## 5. Projeye yansıyan kararlar

| Rapor | Uygulanan |
|---|---|
| Nokta tahmin + Gaussyen gürültü | LightGBM kantil regresyonu (P10–P90) ve ayrılmış veriyle aralık kalibrasyonu |
| Bağımsız 1000 senaryo | Piyasa ve müşteri ortak faktörlü 2000 senaryo |
| Vade + gecikme | Açık faturanın yaşına göre kırpılmış dağılım; tahsil edilememe olasılığı |
| Tüm ödenmiş faturalarla eğitim | Yalnızca vadesi 60+ gün önce dolmuş faturalar |
| Yalnızca açık faturalar | Son dönemin satış ritmi ileri taşınarak kesilmemiş faturalar eklenir |
| VKN + tutar eşleşmesi | Birebir tutar, bulunamazsa cari hesap mantığıyla FIFO ve kısmi ödeme |
| MAE < 4,5 gün | Müşteri medyanına göre MAE, P10–P90 kapsama, geçmiş tarihlerde tahsilat geri testi |
| Otomatik hukuki ihtar | Tüm mesajlar onay bekleyen taslak; resmî ton hukukçu notu taşır |
| Çok gecikmiş faturada model tahmini | Modelin P90'ını aşmış faturalarda geçmişten ölçülen yaşlandırma eğrisi (Kaplan-Meier) |
| Çek/senet yok | Portföydeki çekler vade gününde giriş sayılır, karşılıksızlık olasılığıyla |
| Yalnızca sentetik veri | CSV / Excel / UBL-TR yükleme; az veride basit modele otomatik geçiş |

## 6. Hâlâ açık olan konular

1. Gerçek veri yok. Sentetik verideki sonuçlar yalnızca kodun doğru çalıştığını gösterir.
2. Borç (ödenecek fatura) tarafı ve döviz henüz modelde değil; giderler kullanıcının yüklediği plandan gelir. Çeklerde keşideci bazlı risk yok, tek bir karşılıksızlık oranı kullanılıyor.
3. KOBİ kredi büyüme sınırına dair bulduğum haber tarihsizdi; rapordaki ifade TCMB duyurusundan teyit edilmeli.
4. Konkordato verileri çelişkili (bir kaynak ilk yarıda artış, diğeri sekiz ayda %29 düşüş bildiriyor); pazarlama metninde kullanılmamalı.
5. Hukuki konular (KVKK, ileti mevzuatı, TTK 1530 metni) bir avukata teyit ettirilmeli.

## Kaynaklar

Akademik
- [Zeng vd. 2008, IBM Research](https://research.ibm.com/publications/using-predictive-analysis-to-improve-invoice-to-cash-collection)
- [Optimize Cash Collection, arXiv 1912.10828](https://arxiv.org/pdf/1912.10828)
- [Predicting Account Receivables with Machine Learning, arXiv 2008.07363](https://arxiv.org/pdf/2008.07363)
- [Ayrık zamanlı sağkalım ile ödeme süresi tahmini, Springer 2024](https://link.springer.com/article/10.1007/s44257-024-00013-2)
- [Barrot 2016, MIT DSpace](https://dspace.mit.edu/handle/1721.1/108627)
- [Jacobson ve von Schedvin 2015, Econometrica](https://econometricsociety.org/publications/econometrica/2015/07/01/Trade-Credit-and-the-Propagation-of-Corporate-Failure:-An-Empirical-Analysis)
- [Klapper, Laeven, Rajan, NBER w17146](https://www.nber.org/papers/w17146)
- [Murfin ve Njoroge 2015, RePEc](https://ideas.repec.org/a/oup/rfinst/v28y2015i1p112-145..html)
- [Hallsworth vd., NBER w20007](https://www.nber.org/papers/w20007.pdf)
- [M5 belirsizlik yarışması, RePEc](https://ideas.repec.org/a/eee/intfor/v38y2022i4p1365-1385.html)
- [Hyndman, "Prediction intervals too narrow"](https://www.r-bloggers.com/2014/10/prediction-intervals-too-narrow/)
- [Gneiting, Balabdaoui, Raftery 2007](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jrssb.pdf)

Raporlar ve veriler
- [Atradius, Türkiye B2B ödeme uygulamaları 2025](https://atradiuscollections.com/hk/出版物/報告/b2b-payment-practices-trends-türkiye-2025)
- [Atradius, Türkiye 2026 (PDF)](https://atradius.de/dam/jcr:b1f513aa-5b1e-4ed0-bb09-b1d3fe4eece2/payment-practices-barometer-central-and-eastern-europe-2026-turkiye-en.pdf)
- [Türkiye Gazetesi, Atradius 2026 aktarımı](https://www.turkiyegazetesi.com.tr/ekonomi/ticarette-tahsilat-alarmi-vadeler-uzadikca-uzuyor-1822310)
- [Intrum European Payment Report](https://intrum.com/epr2025)
- [JPMorgan Chase Institute, Cash is King](https://www.jpmorganchase.com/institute/all-topics/business-growth-and-entrepreneurship/report-cash-flows-balances-and-buffer-days)
- [TL ticari kredi faizi, 2 Ekim 2026 haftası](https://www.ticarigm360.com/tl-ticari-kredi-faizi-yeniden-yukari-dondu-yeni-kullandirimlarda-ortalama-yuzde-4923/)
- [Karşılıksız çek, Ocak–Ağustos 2026](https://www.alomaliye.com/2026/09/18/2026nin-ilk-sekiz-ayinda-karsiliksiz-cek-tutari-yuzde-56-artti/)
- [Konkordato: Forbes](https://www.forbes.com.tr/ekonomi/ilk-alti-ayda-konkordato-ve-iflas-basvurularinda-artis), [Dünya](https://www.dunya.com/sektorler/konkordatoda-toplam-basvuru-yuzde-29-dustu-tekstil-toparladi-risk-tarim-ve-nakliyeye-kaydi-haberi-839693)

Mevzuat
- [2026 temerrüt faizi ve tahsil gideri, Bloomberg HT](https://www.bloomberght.com/tcmb-temerrut-faiz-oranini-indirdi-3765181)
- [TTK 1530 ve 60 gün kuralı, Paraşüt](https://www.parasut.com/blog/vade-farki-nedir)
- [Açık bankacılık lisansları, Forbes Türkiye](https://www.forbes.com.tr/fintek/tcmb-den-hepsipay-ve-param-a-acik-bankacilik-izni)
- [ÖHVPS 2.0, Bloomberg HT](https://www.bloomberght.com/tcmb-acik-bankacilikta-yeni-ozellikleri-kullanima-acti-3772072)
- [Ticari elektronik iletiler yönetmeliği](https://alomaliye.com/2015/07/15/ticari-iletisim-ve-ticari-elektronik-iletiler-hakkinda-yonetmelik/)
- [WhatsApp şablon kütüphanesi, Meta](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-library)

Rakipler
- [Agicap alacak yönetimi](https://agicap.com/en/products/account-receivable/), [Agicap yapay zekâ](https://agicap.com/en/features/ai-cash-flow-management/)
- [Upflow AI](https://upflow.io/features/upflow-ai)
- [Finrota NAP360](https://www.finrota.com/ozel-cozumler/cash-flow-management-nap360-finrota), [Netekstre KOBİ](https://finrota.com/en/products/netekstre-kobi)
- [Paraşüt karşılaştırma yazısı](https://www.parasut.com/blog/en-iyi-gelir-gider-takip-yazilimlari), [Mikro tahsilat](https://www.mikro.com.tr/Tahsilat-programi/)
- [Kolleno fiyat](https://pricingsaas.com/companies/kolleno), [Chaser ve Kolleno karşılaştırması](https://erpresearch.com/erp-add-ons/ar-collections/chaser-vs-kolleno)
- [Monk](https://www.automate.org/ai/news/monk-brings-ai-powered-ar-automation-to-automate-2026-surpasses-1b-in-receivables-under-management-monk)
- [Xero Analytics Plus](https://www.xero.com/media-releases/xero-unveils-new-product-features-xerocon/), [QuickBooks Cash Flow Planner](https://insightfulaccountant.com/accounting-tech/general-ledger/quickbooks-cash-flow-planner-enhancements/)

## Ek: Kullanıcının saha ve mevzuat raporunun değerlendirmesi (14 Ekim 2026)

İncelenen belge: "KOBİ Tahsilat ve Nakit Akışı Otomasyonu İçin Altı Kritik Alanın Teknik, Saha ve Hukuki İnceleme Raporu" (12 sayfa).

### Güvenilirlik

- **Saha profilleri (bölüm 3.1) gerçek görüşme değil.** Metin, sekiz profili "saha verilerini temsil eden" profiller olarak tanımlıyor; kişi, tarih ya da görüşme kaydı yok. Ürün kararında kanıt değil, sınanacak hipotez sayıldı. Gerçek görüşme ihtiyacı sürüyor.
- **Kaynaksız rakamlar:** SMMM bürolarının %70'inin Luca kullandığı, müşterilerin ortalama +12–25 gün geç ödediği ve ödeme istekliliği aralıkları birincil kaynağa bağlanmıyor. Kullanılmadı.
- **Örnek fatura numaraları hatalı biçimde.** Raporun örnekleri (ör. GIB202600000142) 15 karakter; GİB fatura numarası 16 karakterdir (3 harf + 4 haneli yıl + 9 haneli sıra). Kodda 16 karakterlik kural kullanıldı.
- **Mevzuat maddesi numaraları yanlış.** Rapor borç hatırlatma istisnasını "m.6/1-b", tacir istisnasını "m.6/2" olarak veriyor. Ticaret Bakanlığı'nın yayımladığı metinde madde 6 bentsiz dört fıkradan oluşuyor; borç hatırlatma 2. fıkra, tacir/esnaf 3. fıkra. İçerik doğru, atıf yanlış.
- **Vergi takvimi kısmen yanlış.** Rapor "ayın 26'sındaki Muhtasar/KDV ödemeleri" diyor. GİB vergi takvimine göre muhtasar ve prim hizmet beyannamesi ayın 26'sında, KDV ise 28'inde ödenir.
- **TTK 1530/5'in dar okunması.** Rapor "alacaklı KOBİ ve borçlu büyük ölçekli" diyor; kanun metni "veya" der (bkz. yukarıdaki teyit tablosu).

### Doğrulanan ya da kendi içinde tutarlı olanlar

- TTK m.1530'da ihtarsız temerrüt, vade yazmıyorsa 30 gün kuralı, 2026 için %43 ve 2.020 TL: TCMB ve kanun metniyle uyumlu.
- TTK m.18/3: tacirler arasında temerrüde düşürme ihtarının noter, taahhütlü mektup, telgraf ya da KEP ile yapılması gerektiği; düz e-posta ve WhatsApp bu şekli karşılamaz. Panel metni buna göre değiştirildi.
- KVKK: tüzel kişi verisinin kişisel veri olmadığı, şahıs şirketi sahibinin telefon ve e-postasının kişisel veri olduğu, borç takibinin sözleşmenin ifası ve meşru menfaate dayanabileceği, yazılımın "veri işleyen" olarak sözleşme gerektirdiği. Kanunun genel yapısıyla tutarlı; ürün çok kullanıcılı hâle gelmeden önce avukatla teyit edilmeli.
- Entegratörlerde "alındı" işaretinin değiştirilmemesi gerektiği: kaynak olarak bir entegrasyon belgesinden alıntı var ve mantıken zorunlu. Otomatik bağlantı yapılırken uyulacak tasarım kuralı olarak kaydedildi.

### Koda geçenler

| Rapordaki bulgu | Uygulanan |
|---|---|
| Banka ve muhasebe dosyalarında tablo birkaç bilgi satırından sonra başlar | Başlık satırı otomatik bulunur |
| Ekstrelerde tek tutar + B/A sütunu ya da ayrı Borç/Alacak sütunları | Yalnızca "A" (giriş) satırları alınır |
| Açıklamada fatura no, VKN/TCKN, IBAN geçer; banka önekleri gürültüdür | Önce fatura numarası, sonra VKN/TCKN, sonra öneksiz unvan; iki müşteri aynı puanı alırsa tahmin edilmez |
| Mikro'da fatura no seri + sıra iki sütundadır | Birleştirilir |
| Programların başlık adları | Eşanlamlı sözlüğe eklendi (ör. Düzenleme Tarihi, Kalan Meblağ, Cari İsmi, Hesap Adı); sonundaki "(TL)" yok sayılır |
| Cirolanan çek kasaya girmez | Çek dosyasında durum sütunu varsa ciro, iskonto, faktoring ve sonuçlanmış evrak tahmine katılmaz |
| Cuma ödeme listeleri | Haftanın sabit günü alışkanlığı tespit edilir, iletişim tarihi ona göre önerilir |
| Birincil kanal WhatsApp | Taslak, müşterinin cep telefonuyla kullanıcının kendi WhatsApp'ında yazılmış hâlde açılır (API gerekmez) |
| Resmî bildirimde yanıltıcı başlık, teslim ve kısmi ödeme riski | Konu "Vade aşımı ve TTK m.1530 kapsamında ödeme bildirimi"; metin teslime ve kısmi ödemede hakların saklılığına atıf yapar; panel bunun ihtarname olmadığını ve KEP/noter gerektiğini söyler |
| En çok unutulan kalemler vergi ve SGK | Dosyası olmayan için aylık sabit gider şablonu: GİB takvimine göre muhtasar 26, KDV 28, SGK ay sonu; hafta sonu ilk iş gününe kayar |

Rapor sayesinde bir hata da bulundu: "200.000" gibi binlik ayraçlı ama ondalıksız Türkçe tutarlar 200 okunuyordu. Düzeltildi ve teste bağlandı.

Kaynak: [GİB vergi takvimi](https://gib.gov.tr/vergi-takvimi), [beyanname verme ve ödeme süreleri](https://cdn.gib.gov.tr/api/gibportal-file/file/getFileResources?objectKey=arsiv%2Fyardim-kaynaklar%2Fyararli-bilgiler%2FBeyannameVermeveOdemeSureleri.pdf), [Ticaret Bakanlığı yönetmelik metni](https://kayseri.ticaret.gov.tr/yayinlar/tuketici/ticari-iletisim-ve-ticari-elektronik-iletiler-hakkinda-yonetmelik).
