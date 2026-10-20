# Doğrulama: Simülasyon Çalışması

Tarih: 14 Ekim 2026. Yeniden üretmek için: `python run_validation.py 24` (yaklaşık 3 dakika).

## Kur belirsizliği: ECB kurlarıyla geçmişe dönük sınama (20 Ekim 2026)

Dövizli alacağın TL karşılığı, kur sabit sayılınca 2010–2026'da 30–90 günlük dönemlerin %24–36'sında bugünkünden düşük çıktı. Tarihsel benzetimle (yalnızca geçmiş veri; TL'nin ortalama değer kaybı çıkarılmış) kötümser uç %4–7 sıklıkla aşıldı, yani ihtiyatlı. İyimser uç bilinçli olarak dar: %15–27. Ayrıntı: [HATA_AZALTMA_ANALIZI.md](HATA_AZALTMA_ANALIZI.md), bölüm 7. Yeniden üretmek için: `python tools/kur_sinamasi.py`.

## Senaryo laboratuvarı, sürüm 6 ve hata azaltma (20 Ekim 2026)

Analiz: [HATA_AZALTMA_ANALIZI.md](HATA_AZALTMA_ANALIZI.md). İşaretli tutarlı banka ekstrelerinde çıkış hareketlerinin tahsilat sayılması hatası bulundu ve düzeltildi. Gider planı artık işletmenin banka geçmişiyle karşılaştırılıyor; plandan eksik kalan kısım "plan dışı ödemeler" olarak ekleniyor. Giderlerin dalgalanması kasa bandına katıldı. Giderleri dalgalanan 120 işletmede kötümser uç aşımı %13,3'ten %9,2'ye indi. Sınavda (240 işletme) kötümser uç aşımı %7, iyimser %10 çıktı; Basel yeşil, Kupiec iki uçta da geçiyor (p = 0,13 / 1,00), Spiegelhalter p = 0,96.

## Sıralı laboratuvar: pilot çevrimiçi izleme (18 Ekim 2026)

Her sentetik işletme 52 hafta boyunca haftalık pilot tahsilat kaydı üretti. Çevrimiçi izlemede iki kusur bulundu ve düzeltildi. Birincisi, aşım ayarlanmamış banda göre ölçülüyordu; bu yüzden geri besleme kopuktu. İkincisi, tahsilat kaydı ölçüldüğü tanımla hesaplanmıyordu: çekte kapanış günü ve taksitler hesaba katılmıyordu. Ayrıca kaynağa dayanmayan katsayı sınırları kaldırıldı. Sınavda (40 yeni işletme, 1.000 kayıt) kötümser uç aşımı %10,7, iyimser %8,9 çıktı. Basel yeşil, Kupiec iki uçta da geçiyor (p = 0,49 / 0,25). Eski kuralda kötümser uç aşımı %7,8'di (Kupiec p = 0,018). Protokol 1.5. Ayrıntı: [LAB_RAPORU.md](LAB_RAPORU.md).

## Senaryo laboratuvarı, sürüm 5: taksit alışkanlığı (18 Ekim 2026)

Taksit alışkanlığı artık işletmenin kendi tahsilat olaylarından öğreniliyor (banka eşleşmeleri ya da cari hesap dağıtımları). Eşleştirilmiş 120 işletmede taksit kaynaklı kötümser sapma −0,107'den +0,016'ya indi. Sınavda (240 işletme) alt aşım %5, üst %14 çıktı (Basel yeşil, Spiegelhalter p = 0,55). Bileşen analizinde açık faturalar ve yeni satış tutarı kalibre çıktı. Yeni satışların tahsilatında küçük bir kötümserlik var (PIT 0,55). Bandın kötümser ucunun genişliği tasarımdaki ihtiyat ilkesinden geliyor. Üç düzeltme denendi, uçtan uca kazanç göstermedi ve reddedildi: yeni faturalar için ayrı ayar, kalibrasyonu kapatma ve deneysel Bayes büzmesi. Ayrıntı: [LAB_RAPORU.md](LAB_RAPORU.md).

## Senaryo laboratuvarı, sürüm 4: kısmi ödeme ve eksik vade (18 Ekim 2026)

Eşleştirilmiş 120 işletmede, faturaların %30'unda vadenin girilmemiş olması tahmini bozmadı (fark +0,002 ± 0,006). Müşterilerin %40'ının taksitle ödemesi ise tahmini kötümser yaptı (−0,13 ± 0,02 aylık ciro). Hata güvenli yönde; taksit alışkanlığının öğrenilmesi sonraki sürüme planlandı. Sınavda (240 işletme) alt aşım %6, üst %12 çıktı (Basel yeşil, Spiegelhalter p = 0,23); zayıf bölge yok. Ayrıntı: [LAB_RAPORU.md](LAB_RAPORU.md).

## Senaryo laboratuvarı, sürüm 3: geç işlenen tahsilatlar (18 Ekim 2026)

Tahsilat kayıtları bugünden geride kaldığında ödenmiş faturalar açık görünür ve para iki kez sayılır. Kayıtlar yasal süre içinde olsa da günü gününe olmayabilir (VUK m.219) ya da dosya önceden alınmış olabilir. Aynı 120 işletmenin eşleştirilmiş ölçümünde 7–14 günlük gecikme orta tahmini +0,13 aylık ciro iyimser yaptı ve kötümser uç aşımını %4,2'den %8,3'e çıkardı. Tahmin artık tahsilatların işlendiği son güne göre kuruluyor; bu gün kullanıcı girmezse kayıtlardan tahmin ediliyor. Böylece sapma −0,03 ± 0,02'ye, aşım %4,2'ye döndü. Laboratuvarda tahmin günü artık yılın her günü. Satış tahmini nominal büyümeyle (James–Stein büzmeli) ölçekleniyor. Sınavda (240 işletme) alt aşım %6, üst %12 çıktı (Basel yeşil, Spiegelhalter p = 0,90). Kötümser uç gereğinden geniş (Kupiec alt p = 0,025): bu verimsizlik, tehlike değil. Ayrıntı: [LAB_RAPORU.md](LAB_RAPORU.md).

## Senaryo laboratuvarı, sürüm 2: çek (17 Ekim 2026)

Laboratuvar, çekle ödeyen müşterisi olan işletmelerde kasanın olduğundan erken dolu göründüğünü ortaya çıkardı. Cari hesapta fatura çek alınınca kapanır, para ise vadede gelir. Aynı 240 işletmede düzeltmeden önce alt aşım %40'tı (Basel kırmızı, orta tahmin +0,56 aylık ciro iyimser). Çekle ödeme payı ve çek vadesi her işletmenin kendi cari hesabından öğrenilince alt aşım %10'a indi (Basel yeşil, sapma −0,06). Yeni tohumlarla sınavda alt aşım %8, üst aşım %6 çıktı (Basel yeşil); iyimser uç ve olasılık kalibrasyonu ise reddedildi (Kupiec üst p = 0,043, Spiegelhalter p = 0,011). Ayrıntı: [LAB_RAPORU.md](LAB_RAPORU.md).

## Senaryo laboratuvarı (17 Ekim 2026)

Ayrıntı: [LAB_RAPORU.md](LAB_RAPORU.md). Sentetik çalışma 3 boyuttan 9 boyuta genişletildi: ölçek, sektör ve tahsil süresi (TCMB–TÜİK), mevsimsellik (gerçek KOBİ), enflasyon (TÜİK TÜFE), müşteri yoğunlaşması (gerçek KOBİ), geçmiş uzunluğu, kötüleşme ve şok. Geliştirme kümesi ve saklı rejimler içeren ayrı bir sınav kümesi var; sınav kümesi bir kez koşuldu ve kayda yazıldı. Sınavda 240 işletmede alt aşım %10, üst aşım %9 (Basel yeşil, Kupiec p = 1,00 / 0,67), Spiegelhalter p = 0,28. Model her kesitte basit yöntemden iyi (−0,93 ± 0,09 aylık ciro). Saklı rejimlerde iki küçük kesit (17 ve 20 işletme) Basel sarı çıktı; geliştirme tarafında 120'şer yeni işletmeyle incelendiklerinde ikisi de yeşil çıktı (alt aşım %5,8 ve %6,7).

## Türkiye verisi: sektör karşılaştırması ve çek riski (17 Ekim 2026)

- **Sektöre göre tahsil süresi:** TCMB–TÜİK Sektör Bilançoları 2023-2025 (vergi idaresine verilen bilanço ve gelir tablolarından, yaklaşık 1 milyon girişim), ölçek kırılımlı standart oranlar tablosu, Alacak Devir Hızı çeyreklikleri (2025). 308 sektör × ölçek satırı `src/radar/data/sektor_alacak_2025.csv`'ye çıkarıldı (kaynak dosya "Dosya 2", SHA-256 b0e935635f4e1fdddf93ff3b3e875b885ae95cc05fec1427a895a9f65150daa4). Örnek ortanca tahsil süreleri (365 / devir hızı): imalat küçük ölçek 74 gün (50.579 firma; çeyrekler 41–135), toptan ticaret küçük 69 gün, tekstil küçük 80 gün, gıda imalatı küçük 45 gün. Panel, işletmenin sektörü ve ölçeği seçilirse tahsil süresini bu dağılıma yerleştirir. Tahmine girmez; tanımlar yakındır ama aynı değildir (TCMB: yıllık ortalama ticari alacak; panel: bugünkü açık alacak / son 90 günün satışı).
- **Karşılıksız çek oranı:** TBB Risk Merkezi aylık çek raporlarına göre 2026'da tutar bazında %2,8–3,4 (Haziran 2026 %3,2; sistemde Ağustos 2026 değeri %3,4 kullanılır, `simulate.CHEQUE_BOUNCE`).
- **Fatura ve ödeme düzeyinde açık Türk KOBİ verisi bulunamadı;** bu düzeyde doğrulama pilotla yapılacak.

## Gerçek bir KOBİ'nin satış verisiyle yeni satış tahmini (17 Ekim 2026)

**Veri.** UCI Online Retail II (Chen 2012, doi:10.24432/C5CG6D, CC BY 4.0): İngiltere'de kayıtlı, mağazası olmayan küçük bir hediyelik eşya şirketinin 01.12.2009–09.12.2011 arasındaki bütün satışları (1.067.371 satır, 53.628 fatura; müşterilerin çoğu toptancı). Ödeme tarihi yoktur; bu yüzden yalnızca tahminin "yeni satışlar" parçası sınanabilir. Dosya: `data/acik/online_retail/online_retail_II.xlsx`, SHA-256 bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980. İptal faturaları (C ile başlayan) eksi tutarla toplama katılır. Fatura ve ödeme tarihini birlikte içeren açık bir KOBİ verisi bulunamadı (bulunan aday, zaten kullanılan Payment Date verisinin kopyasıydı).

**Bulgu: eski yöntem gerçek KOBİ'de standardı geçemedi.** Eski yöntem son 90 günün faturalarını 90 gün ileri taşıyor, belirsizliği faturaların Poisson yeniden örneklenmesiyle veriyordu. 40 haftalık tahmin tarihinde (Aralık 2010 – Eylül 2011):

| | 30 gün | 90 gün |
|---|---|---|
| Eski yöntem, sapma | %47,9 | %37,4 |
| Son 90 günün hızı, sapma | %35,4 | %37,4 |
| Geçen yılın aynı dönemi (52 hafta önce), sapma | **%10,6** | **%7,2** |
| Eski yöntem, Basel (kötümser uç) | kırmızı (14/40) | kırmızı (13/40) |

Mevsimsellik yok sayılıyor, belirsizlik de satış düzeyindeki dalgalanmayı göremiyordu. Büyüme düzeltmeli mevsimsel yöntem bu şirkette yardımcı olmadı (şirketin 2010 ve 2011 satışları aynı düzeyde).

**Uygulanan.**
1. **Yöntem işletmenin kendi geçmişinde seçilir** (zaman sırasına uygun geri test; Tashman 2000; Hyndman ve Athanasopoulos): geçen yılın aynı dönemi ile son dönemin hızı aynı geçmiş haftalarda 30 günlük satışı tahmin eder; mevsimsel yönteme yalnızca Diebold-Mariano testine göre anlamlı biçimde (%5) daha isabetliyse geçilir. Bir yıldan kısa geçmişte son dönemin hızı kullanılır.
2. **Belirsizlik işletmenin kendi geçmiş satış tahmini hatalarından gelir:** 90 günlük ufuk üç aylık bloğa bölünür; her bloğun düzeyi geçmiş 30 günlük hatalardan yeniden örneklenir, ortalaması 1'e eşitlenir (orta tahmin kaymaz). En az 8 geçmiş hata yoksa daha uzun geçmişli yöntemin hataları, o da yoksa eski yeniden örnekleme kullanılır.

**Sonuç (aynı gerçek veride, ürünün kendi fonksiyonlarıyla, haftalık 66 tahmin tarihi):**

| Durum | Ufuk | Sapma | Kötümser altı | İyimser üstü | Basel | Kupiec (alt / üst / merkezi, kesin) |
|---|---|---|---|---|---|---|
| Bir yıl+ geçmiş (mevsimsel seçildi) | 30 gün | %10,8 | 2 / 36 | 8 / 36 | yeşil | 0,43 / **0,046** / 0,29 |
| Bir yıl+ geçmiş (mevsimsel seçildi) | 90 gün | %7,6 | 0 / 36 | 5 / 36 | yeşil | **0,025** / 0,58 / 0,41 |
| Bir yıldan kısa (son dönemin hızı) | 90 gün | %37,9 | 6 / 30 | 17 / 30 | **sarı** | 0,12 / 0,000 / 0,000 |

Bir yıl ve üzeri geçmişte sapma %37'den %8'e indi ve risk tarafı Basel yeşil; kalan iki Kupiec reddi güvenli yönde (90 günde kötümser uç gereğinden geniş, 30 günde satış zaman zaman iyimser tahmini aştı). Bir yıldan kısa geçmişte mevsimsellik bilinemez: yoğun sezonun ardından tahmin iyimser kalıyor (Basel sarı). Panel bu durumda açıkça uyarır ve kararın kötümser çizgiye göre verilmesini ya da yeni satışların hesaptan çıkarılmasını önerir.

**Sentetik çalışmaya etkisi** (mevsimsellik içermeyen üreteç): hata 0,332 → 0,338, Brier 0,0947 → 0,0950, Basel yeşil (19/192). Seçim kuralı mevsimselliği olmayan şirketleri eski yöntemde tuttu. Denenip bırakılanlar: seçimin anlamlılık testi olmadan yapılması (sentetikte hata 0,377–0,405, Basel sarı) ve hataların ortancaya göre merkezlenmesi (sentetikte hata 0,377).

## Literatürün önerdiği çözümler ve uygulananlar (17 Ekim 2026)

Soru: Kupiec ve Spiegelhalter testlerinde görülen sapmalar için güncel bilimsel literatür ne öneriyor; az veriyle çalışan küçük işletmede hangisi uygulanabilir?

| Sorun | Literatürün önerisi | Kaynak | Uygulandı mı |
|---|---|---|---|
| Kupiec'in ki-kare yaklaşımı küçük örneklemde ve uç kapsama düzeylerinde boyut sapması yapar (fazla ya da az reddeder) | Kesin (binom) p değeri | Kaszyński, Kamiński ve Pankratz; ExactVaRTest (CRAN) | **Evet.** 16 kayıtta hiç aşım yokken ki-kare p = 0,066 (sınırda alarm), kesin p = 0,20. |
| Kapsama testlerinin gücü az gözlemde düşük | Birden çok test birlikte; sonuçlar "kanıt yok" diye okunur, "doğru" diye değil | Christoffersen (2004); Berkowitz vd. (2011) | **Evet** (panel ve raporda yazılı) |
| Zamanla değişen davranış ve işletmeye özgü sapma (gerçek veride iyimser uç dar, sentetikte geniş: tek genel ayar ikisini düzeltemez) | Çevrimiçi uyarlanabilir aralık: her yeni gerçekleşmeyle kapsama hatası kadar düzeltme; veri üretiminden bağımsız uzun dönem kapsama garantisi | Gibbs ve Candès (2021), NeurIPS, "Adaptive conformal inference under distribution shift"; Angelopoulos, Candès ve Tibshirani (2023), NeurIPS, "Conformal PID control for time series prediction" | **Evet.** Her işletmenin ufku dolmuş haftalık kayıtlarıyla iki uç ayrı izlenir (`pilot.online_adjustment`; adım 0,1; kötümser uç başlangıç genişliğinin altına daralmaz). |
| Olasılıkların kalibrasyonunu kararlı ölçmek | CORP: izotonik regresyonla güvenilirlik diyagramı; Brier = MCB − DSC + UNC | Dimitriadis, Gneiting ve Jordan (2021), PNAS | **Evet** (doğrulama raporu) |
| Ortaya sıkışık (az kendinden emin) olasılıkları düzeltmek | Gerçekleşmiş sonuçlarla yeniden ayar: izotonik (PAV) ya da beta dönüşümü | Ranjan ve Gneiting (2010), JRSS-B; Kull vd. (2017); Dimitriadis vd. (2021) | **Hayır, pilot sonrasına önceden kaydedildi.** Sonuç verisi gerektirir; tek işletmenin az sayıdaki olayıyla yapılan yeniden ayarın değişkenliği büyüktür (Van Calster vd.). Sentetik veriyle yapmak üretecin varsayımlarını ürüne gömer. |

**Çevrimiçi kantil izlemenin sınanması.** Kaydedilmiş 16 tarihlik geri testler zaman sırasıyla, her tarihte yalnızca ufku dolmuş kayıtları kullanarak yeniden oynatıldı:

| | IBM 14 | IBM 30 | PD 14 | PD 30 |
|---|---|---|---|---|
| İyimser uç aşımı (önce → sonra) | 2 → 2 | 1 → 1 | 1 → 1 | **5 → 4** |
| Kupiec iyimser uç p, kesin (önce → sonra) | 1,00 → 1,00 | 0,73 → 0,73 | 0,73 → 0,73 | **0,017 → 0,25** (geçer) |
| Basel (kötümser uç) | yeşil | yeşil | yeşil | yeşil |

Sonuç, adım büyüklüğünden bağımsız (0,1 / 0,2 / 0,4 aynı). Yöntem işletmenin kendi kayıtlarıyla çalıştığı için pilotun ilk haftalarında etkisizdir; kayıt biriktikçe devreye girer.

**CORP (sentetik, eksiye düşme olasılığı):** Brier 0,0947 = MCB 0,0129 − DSC 0,1474 + UNC 0,2292. Ayırt etme güçlü; kalibrasyon hatası Brier'in yaklaşık %14'ü: olasılıkların sırası doğru, ölçeği sıkışık. İzotonik yeniden ayar Brier'i yaklaşık 0,082'ye indirebilir; bunu yapmak için gereken gerçek sonuç verisi pilotta toplanır (protokol 1.4).

## Uluslararası standartlarla değerlendirme (16 Ekim 2026)

Kabul ölçütleri projede belirlenmez; şu kaynaklardan alınır (kod: `src/radar/standards.py`, testler Basel Tablo 2'yi birebir üretir):

| Soru | Standart | Kaynak |
|---|---|---|
| Kasa, kötümser tahminin (P10) altına beklenenden sık düşüyor mu? (riskli uç) | Trafik ışığı: doğru modelde "bu kadar ya da daha az aşım" olasılığı ≥ %95 sarı, ≥ %99,99 kırmızı; sınırlar örneklem büyüklüğüne göre binom dağılımından | Basel Bankacılık Denetim Komitesi, BCBS 22 (1996); Türkiye: BDDK, Risk Ölçüm Modelleri ile Piyasa Riskinin Hesaplanmasına ... İlişkin Tebliğ, RG 03.11.2006/26335 (aynı 4 / 5–9 / 10+ sınırları) |
| Aralık doğru genişlikte mi (fazla dar ya da fazla geniş)? | Kupiec olabilirlik oranı testi, iki yönlü, %5 | Kupiec (1995), Journal of Derivatives |
| Tahmin basit yöntemlerden kötü mü? | Diebold-Mariano, Harvey-Leybourne-Newbold düzeltmesiyle, %5 | Diebold ve Mariano (1995), JBES; Harvey vd. (1997), IJF |
| "Eksiye düşme olasılığı" doğru ayarlı mı? | Spiegelhalter z testi ve Brier skoru, %5 | Spiegelhalter (1986), Statistics in Medicine |

**Gerçek açık veri (16 tahmin tarihi, açık faturalardan tahsilat):**

| Veri, ufuk | Sapma (model / en iyi basit) | Diebold-Mariano | Kötümser uç aşımı | Basel | İyimser uç aşımı | Kupiec merkezi p (kesin) | Kupiec iyimser uç p (kesin) |
|---|---|---|---|---|---|---|---|
| IBM 14 gün | %6,98 / %10,57 | eşdeğer (p = 0,06 modelin lehine) | 0 / 16 | yeşil | 2 / 16 | 0,55 | 1,00 |
| IBM 30 gün | %2,96 / %3,65 | eşdeğer | 1 / 16 | yeşil | 1 / 16 | 0,55 | 0,73 |
| Payment Date 14 gün | %3,73 / %4,72 | eşdeğer | 0 / 16 | yeşil | 1 / 16 | 0,22 | 0,73 |
| Payment Date 30 gün | %1,40 / %1,18 | eşdeğer | 1 / 16 | yeşil | **5 / 16** | 0,11 | **0,017** |

Riskli uç dört durumun dördünde Basel yeşil bölgede; merkezi aralık Kupiec testinden dördünde geçiyor; isabet dördünde de basit yöntemlerle istatistiksel olarak eşdeğer (üçünde sayısal olarak daha iyi). Tek kusur: Payment Date 30 günde iyimser uç fazla dar, tahsilat 16 tarihin 5'inde iyimser tahmini aştı (para beklenenden hızlı geldi; kasa açısından güvenli yön).

**Sentetik çalışma (192 tahmin, dönem sonu kasa ve eksiye düşme olasılığı):** Basel yeşil (192'de 20 aşım, beklenen 19); Kupiec (kesin) kötümser uç p = 0,90 (geçer), iyimser uç p = 0,001 ve merkezi p = 0,04 (iyimser uç fazla geniş: %4 aşım, beklenen %10); Spiegelhalter p < 0,001: eksiye düşme olasılıkları ortaya sıkışık (tahmin %6 → gerçekleşen %0; %20 → %13; %80 → %92; %97 → %99). Kırılım: sıkışma bütün senaryolarda var; iyimser ucun fazla genişliği özellikle ortak şokun olmadığı senaryolarda (aşım %1) belirgin.

**Denenip reddedilenler (aynı testlerle):**

| Değişiklik | Sonuç | Karar |
|---|---|---|
| Genişletmesiz (yalnız birleştirme + yeniden ayar) | Sentetikte kötümser uç aşımı 26/192 → Basel **sarı** | Reddedildi: riskli uç standardı bozuluyor |
| İki taraflı konformal ayar (iyimser uç daralabilir) | Payment Date 30 günde iyimser uç daha da daraldı (aşım 6/16, Kupiec p = 0,003); sentetikte iyimser uç daha da genişledi | Reddedildi |
| Yalnız riskli ucu genişletme | Sentetikte Spiegelhalter z −4,46 (mevcut −4,57), güvenilirlik değişmedi | Kazanç yok |

**Yorum ve açık kalan iş.** Kasanın riskli tarafı her veri ve senaryoda uluslararası standarda (Basel/BDDK) uygun. İki taraflı kalibrasyon ise veri setleri arasında **ters yönde** sapıyor: gerçek büyük portföyde iyimser uç fazla dar, sentetik şirketlerde fazla geniş. Tek bir genel ayar ikisini birden düzeltemez; birine göre ayar yapmak öbürünü bozar, gerçek veriye göre ayar yapmak ise o veriyi ezberlemek olur. Doğru ayar, Türk KOBİ pilot verisiyle (protokol B2 ve kapanış kasası hedefi) ölçülecek. O zamana kadar panel, yüksek riskte (≥ %50) gösterilen olasılığın gerçek riskten düşük olabileceğini açıkça uyarır ve kararın kötümser senaryoya göre verilmesini önerir.

## Gerçek açık verilerle doğrulama (14 Ekim 2026)

> **Güncel durum (16 Ekim 2026).** Aşağıdaki ilk tablolar tarihsel kayıttır. Ödeme günü yuvarlama düzeltmesinden (15 Ekim) ve tahmin birleştirme + olasılık yeniden ayarı + toplam düzeyde genişletmeden (16 Ekim) sonra, 16 tahmin tarihiyle: kasa sapması IBM 14 gün %6,98, 30 gün %2,96, Payment Date 14 gün %3,73, 30 gün %1,40; model dört durumun üçünde en iyi basit yöntemi geçiyor, dördüncüsünde 0,2 puan geride. Bant içi oranları %88, %88, %94, %62 (hedef %80). Ayrıntı ve gerekçe: "Düzeltme: tahmin birleştirme..." bölümü.

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

**Düzeltme: tahmin birleştirme, olasılık yeniden ayarı ve toplam düzeyde genişletme (16 Ekim 2026).** Teşhis: (1) IBM'de toplam tahsilat 8 tarihin 7'sinde orta tahminin üstünde kaldı; fatura düzeyinde, vadesi yaklaşan faturaların 14 günde ödenme olasılığı %62 tahmin edilirken gerçekleşen %71'di. Gerçekleşenlerin %35–44'ü koşullu tahmin dağılımının en erken çeyreğine düşüyordu (doğru ayarlı modelde %25); 2012'den 2013'e her dönemde aynı. Tek bir kayma/ölçek sayısı bunu düzeltemiyordu. (2) Payment Date'te (1.056 müşteri) 30 günlük bant toplamın yalnızca %1,5–7'si genişliğindeydi; kaçışlar iki yönlüydü: büyük portföyde ortak belirsizlik küçümseniyordu. Üç değişiklik birlikte uygulandı:

1. **Tahmin birleştirme:** LightGBM ile müşteri medyanı modelinin kantilleri eşit ağırlıkla ortalanır (kantil ortalaması; Lichtendahl vd. 2013). Ağırlık veriden öğrenilmez.
2. **Olasılık yeniden ayarı:** geçmiş tahmin tarihlerindeki koşullu PIT değerlerinin dağılımı Kaplan-Meier ile (ödenmemiş fatura sansürlü) çıkarılır, simülasyonda tekdüze sayı bu dağılımın kantiline çevrilir (Kuleshov vd. 2018). Az gözlemde büzülme sabiti 30; sonuçlara bakılmadan, gruptaki asgari gözlem kuralıyla aynı seçildi. Eski kayma/ölçek düzeltmesinin yerini alır.
3. **Toplam düzeyde konformal genişletme:** aynı geçmiş tarihlerde toplam tahsilat simüle edilir; gerçekleşenin bant yarı genişliğine oranlarının konformal %80 kantili 1'den büyükse bant günlük medyan etrafında o kadar açılır (daraltılmaz, üst sınır 3).

Değerlendirme (geliştirme IBM 8 tarihle yapıldı; karar, ayarlara dokunmadan tarih sayısı 16'ya çıkarılan ölçümle verildi):

| 16 tahmin tarihi | IBM 14 gün | IBM 30 gün | Payment Date 14 gün | Payment Date 30 gün | Ortalama sapma | Aralık skoru toplamı |
|---|---|---|---|---|---|---|
| Önceki | %8,21 (bant içi %88) | %3,52 (%81) | %3,68 (%81) | %1,36 (%62) | %4,19 | 91,6 |
| Yalnız genişletme | %8,21 (%88) | %3,52 (%81) | %3,68 (%94) | %1,36 (%75) | %4,19 | 95,8 |
| **Uygulanan (üçü)** | **%6,98** (%88) | **%2,96** (%88) | %3,73 (%94) | %1,40 (%62) | **%3,77** | **89,5** |
| En iyi basit yöntem | %10,57 (oran) | %3,65 (medyan) | %4,72 (medyan) | %1,18 (medyan) | | |

Fatura düzeyinde ortalama mutlak hata IBM 6,27 → 6,13 gün, Payment Date 3,53 → 3,33 gün (müşteri medyanı 6,03 / 3,23; fark 0,1 güne indi); P10–P90 kapsama %86 → %90 ve %78 → %84. Sentetik çalışmada (24 tohum × 8 rejim): kapsama %83 → %86, bandın altında kalma %12 → **%10** (hedef %10), üstünde %5 → %4, Brier 0,0965 → 0,0947; dönem sonu hatası 0,321 → 0,332 (eşleştirilmiş farkın belirsizliği ±0,04 içinde), aralık skoru 1,456 → 1,589 (bant genişledi).

Seçim gerekçesi: isabet ve kalibrasyonu birlikte ölçen uygun skor (aralık skoru) gerçek veride en iyi bu birleşimde; ortalama sapma %10 azaldı; model dört durumun üçünde en iyi basit yöntemi geçiyor, dördüncüsünde (Payment Date 30 gün) 0,2 puan geride (B1 toleransı içinde). Ayrı ayrı denendiğinde: yalnız birleştirme Payment Date 30 günde bandı daralttı (%25, 8 tarih), yalnız yeniden ayar IBM'de sapmayı azalttı ama bandı genişletmedi, yalnız genişletme isabeti değiştirmedi. **Açık kalan:** Payment Date 30 günde bant içi oranı %62 (16 tarihin 10'u), hedef %80; önceden konan %70 eşiğini bu tek durumda karşılamıyor. Sapmanın kendisi bu durumda çok küçüktür (%1,4); büyük portföyde 30 günlük toplam belirsizlik hâlâ biraz küçümseniyor. Not: aynı yöntemle 8 tarihte %38 ölçülen bant içi oranı 16 tarihte %62 çıktı; 8 tarihlik ölçümler bu düzeyde gürültülüdür.

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
