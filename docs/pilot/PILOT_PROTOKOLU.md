# Pilot Protokolü

Sürüm 1.9 — 28 Ekim 2026. 1.9: saha hazırlık değerlendirmesi (28.10.2026) üzerine: B2'deki trafik ışığının Basel ya da BDDK uygunluğu değil, uyarlanmış bir kapsama tanılaması olduğu yazıldı (ölçüt ve eşik değişmedi); pilotun gölge/karar destek niteliği, kapanış kasasında aynı kapsam kuralı, pilot başlatma kapısı (6a), haftalık forma kapsam soruları ve pilot raporuna kapsam tablosu eklendi. Pilot verisi görülmeden yapıldı. Sürüm 1.8 — 22 Ekim 2026. 1.8: hayata geçiş hazırlık raporu (22.10.2026) üzerine birincil karar bütün işletmelerin birleşik analizine bağlandı (işletme başına oy sayımı kaldırıldı); süre uzatma kuralı, ilerleme ölçütleri (devam / değiştir / dur), pilot paketlerinin saklanacağı yer, katılımcı aydınlatma metni, ihlal planı, kullanım eğrisi ve benimseme soruları eklendi. Pilot verisi görülmeden yapıldı. Sürüm 1.7 — 21 Ekim 2026. 1.7: dış inceleme raporu (21.10.2026) üzerine B1 marjlı eşdeğerlik kararına çevrildi (FDA 2016); güç tablosu eklendi; Aşama 0 ileriye dönük kayıtla aynı tanıma getirildi; B2'ye örtüşmeyen alt örneklem eklendi; yayından önce bağımsız yeniden hesaplama şartı kondu. Pilot verisi görülmeden yapıldı. Sürüm 1.6 — 20 Ekim 2026. 1.6: ileriye dönük pilottan önce geriye dönük aşama eklendi (5. bölüm başı); ilk yükleme süresi ve mesaj gönderim oranı betimleyici ölçüt oldu; dondurma ve kabul kuralı yazıldı. Ölçütler ve eşikler değişmedi. Pilot verisi görülmeden yapıldı. Sürüm 1.5 — 18 Ekim 2026. 1.5: çevrimiçi ayarda aşım, o gün gösterilen (ayarlanmış) banda göre ölçülür; kaynağa dayanmayan katsayı sınırları kaldırıldı; tahsilat kaydı ölçüldüğü tanımla (kapanış ve kısmi tahsilatlar) hesaplanır (bkz. 6. bölüm sonu). 1.4 — 17 Ekim 2026. 1.4: Kupiec p değeri kesin binom hesabıyla; pilot sırasında çevrimiçi kantil izleme; pilot sonrası olasılık yeniden ayarı önceden kaydedildi (bkz. 6. bölüm sonu). 1.3 — 16 Ekim 2026. 1.1: Ek A hukuk müşavirliği taslağına göre güncellendi, Ek D eklendi. 1.2: bağımsız derin inceleme (15.10.2026) üzerine ölçüm tanımları kesinleştirildi. **1.3: kendi belirlediğimiz eşikler (B1'de +2 puan tolerans, B2'de %70 bant içi) kaldırıldı; yerlerine uluslararası ve Türkiye'de geçerli standart testler kondu (Basel Komitesi / BDDK geriye dönük test bölgeleri, Kupiec kapsama testi, Diebold-Mariano testi).** Bütün değişiklikler pilot verisi görülmeden yapıldı. Bu belge, ilk gerçek işletme verisi görülmeden yazılmıştır. Başarı ölçütleri pilot sırasında değiştirilmez; değişiklik gerekirse yeni sürüm numarasıyla, gerekçesiyle ve hangi verinin görüldüğü belirtilerek yapılır.

## 1. Amaç

Açık verilerdeki sonuç (docs/DOGRULAMA.md) şudur: tahmin, "vadesinde ödenir" varsayımından her durumda daha isabetli, "müşteri her zamanki kadar geç öder" yöntemiyle ise başa baş. Pilot iki soruya cevap arar:

1. Bu sonuç Türk KOBİ'lerinin verisinde, **tahmin anında kimsenin bilmediği** gelecek tahsilatlarda tekrarlanıyor mu?
2. Yönetici, haftalık kasa ve tahsilat kararlarında aracı gerçekten kullanıyor mu?

Pilot, "aracın tahsilatı artırdığını" göstermeye çalışmaz. Kontrol grubu olmadan bu nedensellik iddiası kurulamaz (bkz. 6).

**Kullanım sınırı: gölge pilot (1.9).** Araç Türk KOBİ verisinde henüz doğrulanmadığı için pilot bir gölge / karar destek pilotudur. İşletme kasa ve tahsilat takibini bugünkü yöntemiyle sürdürür; panel ona ek bir görüş verir. Ödeme, kredi ya da yatırım kararı yalnızca panele dayanarak verilmez. Eksiye düşme olasılığı ihtiyatlı okunur (yüksek riskte gösterilenden yüksek olabilir; DOGRULAMA.md), karar kötümser çizgiye göre verilir. Bu sınır ilk görüşmede katılımcıya anlatılır ve Ek A m.11'deki "yalnızca karar desteği" hükmüyle aynıdır.

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

**Aşama 0: geriye dönük test (1.6).** İleriye dönük kayıtlar başlamadan önce her işletmenin son 12–24 aylık verisiyle geriye dönük test yapılır ("Tahmin doğruluğu" sekmesi, "Aşama 0 testini çalıştır"). Tanım ileriye dönük kayıtlarla aynıdır, yalnızca geçmişe uygulanır. Bu kayan başlangıç noktalı değerlendirmedir (rolling origin; Tashman 2000, International Journal of Forecasting 16):
- son 52 haftanın her biri bir tahmin günüdür;
- her tahmin günü yalnızca o güne kadarki veriyi kullanır ve öncesinde en az 180 günlük geçmiş ister;
- o gün açık faturalardan 14 ve 30 günde gelecek tahsilat tahmin edilir;
- B1 (Diebold-Mariano, üst üste binen ufuklar hesaba katılarak) ve B2 (Basel, Kupiec) aynı kodla hesaplanır (`pilot.retrospective`).

Sonuç kaydedilir, pilot raporuna girer ve işletmeyle ilk görüşmede konuşulur. En az 4 haftalık tahmin günü kurulamıyorsa (yaklaşık 8 aydan kısa veri) Aşama 0 yapılmaz.
- Aşama 0 sonucu B1/B2 kararının yerine geçmez. Geri testte geçmiş veriye sonradan bakma riski vardır (ör. sonradan düzeltilmiş kayıtlar). Bu yüzden ayrıca raporlanır.
- Aşama 0'da bir işletmede model bir ufukta "geride" çıkarsa, o ufkun tahsilatı için o işletmenin geçmişinde en isabetli çıkan basit yöntemin sayısı panelin üstünde gösterilir ve karar için esas alınır (`pilot.simple_replacements`). Basit yöntemlerin belirsizlik bandı olmadığı için kasa bandı, kötümser çizgi ve "güvenle harcanabilir tutar" modelden gelmeye devam eder; panel bunu açıkça yazar. Model yine kaydedilir ve B1'de ölçülür. Ürün genelinde varsayılanın değişmesi pilot sonundaki karar kuralına bağlıdır.
- Aşama 0'da hiçbir parametre değiştirilmez.

**Aşama 0 ile ileriye dönük kaydın tanımı (1.7).** 1.6'daki uygulama Aşama 0'ı farklı bir tanımla hesaplıyordu: çek ayarı açıktı, tahsilat olayları ve kayıt kesimi kullanılmıyordu, gerçekleşen faturanın kapanış tutarıydı. Çekle ödeyen müşterisi çok olan işletmede model tahsilatı çek vadesine kaydırıyor, gerçekleşen ise kapanışta sayılıyordu. Sentetik bir işletmede (müşterilerin yarısı çekle ödüyor, 12 hafta) modelin 30 günlük sapması %37'den %16'ya indi ve sonuç "eşdeğer"den "üstün"e döndü. Artık Aşama 0'da çekle kapanan fatura kapanış gününde sayılıyor (çek ayarı kapalı). Tahmin günü açık tutar ve taksit alışkanlığı o güne kadarki tahsilat olaylarından geliyor. Gerçekleşen, tahmin gününden sonraki tahsilat olaylarının toplamı. Böylece tanım ileriye dönük kayıt ve puanlamayla aynı (`pilot.cash_backtest`, `same_as_forward`).

**Dondurma ve kabul kuralı (1.6).** Pilot bitene kadar modele, senaryo laboratuvarına ve istatistik çerçevesine yeni sürüm ya da test eklenmez. Pilot başlayana kadar yeni özellik de eklenmez; yalnızca hata ve güvenlik düzeltmeleri ile pilot işletmesinin ya da mali müşavirin açıkça istediği şeyler yapılır. İstisna, sonucu yalnızca daha ihtiyatlı yapan güvenlik düzeltmeleridir. Bir uç Basel yeşil bölgesinde ve Kupiec testi geçiyorsa (p ≥ 0,05) o sonuç kabul edilir ve ayar yapılmaz. Yeşil bölgenin sınırı gözlem sayısına bağlıdır: 100 gözlemde 14 aşıma (%14), 240 gözlemde 31 aşıma (%12,9) kadar.

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
| **B1** (birincil) | Tahsilat isabeti, 14 ve 30 gün, işletme başına | **Marjlı eşdeğerlik (1.7).** Model eksi en iyi güçlü basit yöntem (müşteri medyanı ya da tahsilat oranı) sapma farkı için blok bootstrap ile iki yönlü %95 güven aralığı kurulur. Üst sınır 0'ın altındaysa "üstün", M2'nin altındaysa "eşdeğer (marj içinde)": ikisinde de geçer. Alt sınır M2'nin üstündeyse "geride", diğer durumlarda "kanıtlanamadı": ikisinde de geçmez. Model "vadesinde öder"den anlamlı biçimde kötüyse (Diebold-Mariano, %5) de geçmez. **Marj:** M1, o işletmenin Aşama 0'ında en iyi güçlü basit yöntemin "vadesinde öder"e üstünlüğünün %95 güven aralığının alt sınırıdır. M2 = M1'in %50'si. M1 ≤ 0 ise marj belirlenemez; B1 yalnızca üstünlükle geçer. Marj ilk ileriye dönük kayıt alınınca dondurulur. Diebold-Mariano sonucu betimleyici olarak ayrıca raporlanır. | FDA (2016), "Non-Inferiority Clinical Trials to Establish Effectiveness": M1 kontrolün geçmişte gösterilmiş etkisinden ihtiyatlı biçimde, M2 bunun bir oranı olarak önceden belirlenir; "M2'yi M1'in %50'si seçmek" kardiyovasküler sonuç çalışmalarında yerleşik uygulamadır; karar iki yönlü %95 güven aralığının üst sınırıyla verilir. CONSORT eşdeğerlik uzantısı (Piaggio vd., JAMA 2012). Burada plasebonun karşılığı "vadesinde öder" (KOBİ'nin fiilen yaptığı varsayım), kontrolün karşılığı en iyi basit yöntemdir. 1.3'te kaldırılan +2 puanlık tolerans bir kuruma dayanmıyordu; bu marj ise kuralı kurumdan, büyüklüğü işletmenin kendi verisinden alır. Kodda: pilot.b1_margin, pilot.b1_decision, pilot.score |
| **B2** | Bant kalibrasyonu (P10–P90) | (a) Kötümser uç (gerçekleşen < P10) aşım sayısı **Basel tipi trafik ışığına** göre **yeşil bölgede** olmalı (Basel Komitesinin %99 günlük VaR ve 250 bağımsız gözlem için kurduğu bölge kuralının %10 kuyruğa ve küçük örnekleme uyarlanmış hâli; Basel ya da BDDK uygunluğu anlamına gelmez, 1.9): doğru modelde "bu kadar ya da daha az aşım" olasılığı %95'in altında (BCBS 1996; Türkiye'de BDDK, Risk Ölçüm Modelleri ile Piyasa Riskinin Hesaplanmasına... İlişkin Tebliğ, RG 03.11.2006/26335, aynı bölge sınırları). (b) **Kupiec (1995) kapsama testi** %5 anlamlılıkta ne merkezi %80 aralık ne alt ne üst uç (%10) için reddetmemeli: bant fazla dar da fazla geniş de olmamalı. | Bölge sınırları gözlem sayısına göre binom dağılımından hesaplanır (Basel belgesinin öngördüğü gibi); küçük işletmenin az sayıdaki haftalık kaydına da uygulanır. Kodda: standards.basel_zone, standards.kupiec_pof, standards.passes |
| **B3** | Kullanım | 13 haftanın en az 10'unda rapor alınmış; tahsilat listesinden en az 10 işlem kaydı (arama, mesaj, söz) | Kullanılmayan araç, isabetli olsa da değer üretmez |
| **B4** | Karar desteği (nitel) | Haftalık formda "Bu hafta bir kasa ya da tahsilat kararında rapora baktım" cevabı en az 6 hafta "evet" | Ürünün iddiası tahmin değil, karar desteğidir |

**B1'in gücü (1.7).** 1.6'daki kural ("geride değilse geçer") marjsızdı: az kayıtla anlamlı fark bulunamaması "fark yok" sayılıyordu. Projenin kendi testiyle (`standards.diebold_mariano`) yapılan benzetimde, model gerçekten kötüyken Diebold-Mariano testinin bunu yakalama olasılığı şöyle çıktı. Kurgu: üst üste binen haftalık kayıtlar, iki yöntemin hataları arasında 0,7 korelasyon, 4.000 tekrar; `tools/b1_guc_tablosu.py`.

| Kayıt | Ufuk | Model eşit (yanlış alarm) | %20 kötü | %50 kötü | 2 kat kötü |
|---|---|---|---|---|---|
| 13 | 14 gün | %8 | %18 | %40 | %72 |
| 13 | 30 gün | %10 | %18 | %32 | %51 |
| 52 | 14 gün | %5 | %39 | %91 | %100 |
| 52 | 30 gün | %7 | %27 | %65 | %94 |

Okuma: 13 haftalık ileriye dönük pilotta, en iyi basit yöntemden %50 kötü bir model üç işletmeden yaklaşık ikisinde eski kuralla "geçerdi". Bu nedenle 1.7'de "geçti" yalnızca kanıt varken verilir; kanıt yoksa sonuç "kanıtlanamadı"dır. 13 kayıtta 30 günlük ufukta yöntemler eşitken yanlış alarm oranı %10'dur (nominal %5); küçük örneklem düzeltmesi bunu tam tutturamıyor. Bu bilgi sonuç yorumlanırken belirtilir.

**B2 ve üst üste binen ufuklar (1.7).** Basel trafik ışığı ve Kupiec testi aşımların bağımsız olduğunu varsayar (Christoffersen 1998). Haftalık kayıtlarda 30 günlük ufuklar dört beş hafta üst üste bindiği için aşımlar kümelenir. B2 kararı değişmeden, aşımlar örtüşmeyen alt örneklemle de raporlanır (her ufuk süresinde bir kayıt). Christoffersen'in koşullu kapsama testi pilot sonrası analize bırakıldı.

**Bağımsız yeniden hesaplama (1.7).** Pilot sonuçları yayımlanmadan ya da tanıtımda kullanılmadan önce, modeli geliştirmemiş bir kişi kayıtları ve kodu bağımsız olarak yeniden hesaplar. Bu kişi bir üniversitenin istatistik ya da işletme bölümünden ya da bir bankanın model doğrulama biriminden olur. Dayanak: ABD Merkez Bankası model riski kılavuzu SR 11-7 ("etkin itiraz"; doğrulayan, modeli kuran ya da kullanan taraftan olmamalı) ve Ticari Reklam Yönetmeliği m.9 (doğruluk iddiasının bağımsız kanıtı).

**Birincil karar: birleşik analiz (1.8).** 1.7'deki karar işletme başına B1 sonuçlarının "çoğunluğuna" bakıyordu. Bu, istatistiksel anlamlılığa dayalı oy sayımıdır. Cochrane El Kitabı (bölüm 12.2.2.1) bu yöntemi "ciddi sınırlılıkları olan ve yanlış sonuca götürebilen" ve kabul edilemez bir yöntem sayar: gücü düşük çalışmalar, önemli bir etkiyi dışlayamadıkları hâlde "fayda göstermedi" diye sayılır. 13 haftalık kayıtla işletmelerin çoğu tek başına "kanıtlanamadı" çıkacağı için 1.7'deki kural modeli, gerçek kalitesinden bağımsız olarak kapatabilirdi.

1.8'de B1 kararı şöyle verilir:
- Her işletmenin ileriye dönük pilottan gelen fark tahmini (model eksi en iyi güçlü basit yöntem, sapma puanı) ve standart hatası (blok bootstrap) rastgele etkiler meta-analiziyle birleştirilir. Yöntem: DerSimonian-Laird heterojenlik, Hartung-Knapp-Sidik-Jonkman güven aralığı (Cochrane El Kitabı 10.10.4), ölçek katsayısı en az 1 (Röver, Knapp ve Friede 2015, BMC Medical Research Methodology 15:99).
- Marj aynı mantıkla birleşik düzeyde kurulur. İşletmelerin Aşama 0'daki M1 tahminleri birleştirilir; birleşik M2, birleşik M1'in %95 alt sınırının yarısıdır (1.7, FDA 2016).
- Karar 1.7'deki kurallarla verilir (`pilot.b1_decision`): üstün, eşdeğer (marj içinde), kanıtlanamadı, geride. Hesap `pilot.pooled_b1` ve `tools/pilot_birlesik.py` ile yapılır.
- İşletme başına B1 sonuçları betimleyici olarak raporlanır; karar onlardan çıkarılmaz.
- İşletmenin fark tahmininin standart hatası için en az iki bağımsız blok gerekir (30 günlük ufukta 10, 14 günlük ufukta 4 haftalık kayıt). Daha az kaydı olan işletme o ufukta birleşik analize girmez; sayısı tabloda "yetersiz kayıtlı işletme" olarak raporlanır, sessizce düşmez (25.10.2026, zincir provasında bulundu).
- Takma adlı pilot paketi Aşama 0 özetini (`asama0.csv`, yalnızca toplu sayılar) ve dondurulmuş marjı (`b1_marj.json`) da taşır. Proje tarafında açılmış paketlerin bulunduğu klasörle `python tools/pilot_birlesik.py <klasör>` çalıştırılır; işletme satırları ve birleşik karar paneldeki puanlamayla aynı kodla hesaplanır. Zincir, sentetik üç işletmeyle uçtan uca sınandı (tests/test_pilot_validation.py).
- Az işletmeyle birleşik analizin gücü de sınırlıdır. Örnek: beş işletmenin her birinde fark tahmininin standart hatası 3 puan, M1 10 puansa, eşit bir model bile "kanıtlanamadı" çıkabilir. Bu yüzden aşağıdaki uzatma kuralı önceden yazılmıştır.

**Süre uzatma kuralı (1.8).** 13 haftanın sonunda birleşik B1 "kanıtlanamadı" çıkarsa ve ilerleme ölçütleri yeşilse, ileriye dönük dönem bir kez 26 haftaya uzatılır. Karar 26. haftadaki birleşik analizle verilir. Uzatma yalnızca bir kez yapılır ve 13. haftadaki sonuçla ilan edilmez. Ara bakış nedeniyle iki karar noktasında da %95 aralık kullanılır; bu, birinci tip hatayı az da olsa artırır ve sonuç raporunda belirtilir.

**İlerleme ölçütleri: devam / değiştir / dur (1.8).** Pilot bir fizibilite çalışmasıdır. CONSORT'un pilot ve fizibilite uzantısı (Eldridge vd., BMJ 2016) büyük çalışmaya geçme kararının önceden yazılmış ölçütlere bağlanmasını ister. Bu ölçütler çoğunlukla işe alım, protokole uyum ve sonuç verisi üzerine kurulur (Avery vd., BMJ Open 2017; trafik ışığı biçimi). Yeşil sınırlar protokolün kendi hedeflerinden gelir. Sarı ve kırmızı sınırlar bir standarda değil yönetim kararına dayanır; ilk imzadan önce proje sahibi tarafından doldurulur ve sonra değiştirilmez.

| Alan | Ölçüt | Yeşil (devam) | Sarı (değiştir) | Kırmızı (dur ya da yeniden tasarla) |
|---|---|---|---|---|
| İşe alım | İlk görüşmeden sonraki 6 hafta içinde Ek A'yı imzalayan işletme | En az 5 (2. bölüm hedefi) | [ ] | [ ] |
| Veri hazırlığı | İlk yüklemeyi ilk kasa bandına kadar yardımsız tamamlayan işletme oranı | [ ] | [ ] | [ ] |
| Veri tamlığı | Kayıt alınan hafta, işletme başına | 13 haftanın en az 10'u (B3) | [ ] | [ ] |
| Kalıcılık | Pilotu tamamlayan işletme oranı | [ ] | [ ] | [ ] |

İlerleme ölçütleri tahmin ölçütlerinden (B1, B2) ayrı raporlanır. Kırmızı bir alan pilotu otomatik olarak durdurmaz; nedeni araştırılır ve yazılır.

**Kullanım eğrisi ve bırakma (1.8).** Dijital araçlarda kullanım hızla düşer ve iki tür kayıp vardır: çalışmadan ayrılma ve çalışmada kalıp aracı kullanmayı bırakma (Eysenbach 2005, "The Law of Attrition", JMIR 7(1):e11). Her işletme için haftalık kullanım (panel açıldı mı, kayıt alındı mı) çizilir. Bırakan ya da üç hafta üst üste kayıt vermeyen işletmeyle kısa bir çıkış görüşmesi yapılır ve neden yazılır.

**Karar kuralı.**
- Karar birleşik analizle verilir (1.8). B2 de birleşik düzeyde değerlendirilir: işletmelerin aşım sayıları toplanır, Basel ve Kupiec toplam üzerinde uygulanır. İşletme başına sonuçlar betimleyicidir.
- Birleşik B1 ve B2 sağlanırsa: mevcut yöntem korunur.
- Birleşik B1 "geride" çıkarsa: ürün varsayılan olarak en iyi basit yönteme geçer ve öğrenen model yalnızca kendi geri testinde açıkça önde olan işletmelerde açılır. Bu durum belgede ve tanıtımda açıkça yazılır.
- Birleşik B1 "kanıtlanamadı" çıkarsa: önce süre uzatma kuralı uygulanır. 26. haftada da "kanıtlanamadı" ise model kapatılmaz, ama tanıtımda modelin basit yöntemlerden iyi ya da eşdeğer olduğu söylenmez; panel kararı en iyi basit yöntemle birlikte gösterir.
- B1, "vadesinde öder" karşısında da sağlanmazsa: kasa tahmini özelliği yeniden tasarlanana kadar "deneysel" etiketi taşır.
- B2 sağlanmazsa: kötümser uç sarı/kırmızı bölgedeyse (risk küçümseniyor) kasa grafiğinde uyarı gösterilir ve bant kalibrasyonu pilot verisiyle değil, yeni bir geri test tasarımıyla yeniden ele alınır; pilot verisine göre ayar yapılıp aynı veriyle başarı ilan edilmez. Yalnızca bant gereğinden genişse (Kupiec, az aşım) güvenlik açısından acil değildir; sonraki sürümde düzeltilir.
- B3 veya B4 sağlanmazsa: sorun teknik değil kullanım sorunudur; görüşmelerle nedeni araştırılır (bkz. ikincil ölçütler).

**Raporlama.** Bütün işletmelerin bütün kayıtları raporlanır; işletme çıkarılacaksa (örneğin veri gönderimi kesildi) nedeni yazılır. Toplu sonucun yanında en iyi ve en kötü işletme ayrıca verilir. Başarısız sonuçlar, reddedilen yöntemler gibi DOGRULAMA.md'de kalır. 5–10 işletmede "çoğunluk" bir fizibilite sonucudur; pazar ya da genel geçerlilik kanıtı olarak sunulmaz. Sonuçlar üç ayrı başlıkta raporlanır: fizibilite (veri hazırlanabildi mi), tahmin kanıtı (B1, B2), ürün kullanımı (B3, B4).

## 6. İkincil ölçütler (yalnızca betimleyici)

- Vadesi geçmiş alacağın toplam alacağa oranı ve ortalama tahsilat süresi (DSO), pilot öncesi 13 hafta ile pilot dönemi arasında.
- Gönderilen mesajlardan sonra 14 gün içinde ödenme oranı (panel bunu "Gönderilen mesajların sonucu" bölümünde hesaplar).
- Eşleşmeyen banka tahsilatı oranı (veri kalitesi).
- **Hedef B, kapanış kasası:** her kayıtta açılış kasasından başlayıp bilinen giderler, borçlar, çekler, açık faturalar ve (açıksa) yeni satışlarla 7, 14 ve 28 gün sonraki kasa (P10/P50/P90) yazılır. Gerçekleşen, ufkun sonuna ±3 gün içindeki kayıtta kullanıcının o gün girdiği kasa ve banka toplamıdır (yalnızca o gün güncellenmiş bakiyeler kullanılır). Karşılaştırma: "kasa değişmez". Hedef A'dan ayrı raporlanır; toplam nakit isabeti tahsilat isabetiyle karıştırılmaz. Kapsam dışı kaynaklar (ör. gider dosyası yok) kayıt künyesinde yazılıdır.
  **Aynı kapsam kuralı (1.9).** Gerçekleşen bakiye, açılış bakiyesiyle aynı banka hesaplarını ve aynı kasa tanımını kullanır; ilk kayıtta hangi hesapların dahil olduğu yazılır ve pilot boyunca değiştirilmez. Ufuk içinde yeni kredi kullanımı ya da kapanması, hesaplar ya da ortaklarla para transferi, dövizli bakiyede büyük kur hareketi ve plan dışı büyük ödeme Ek B'de tutar ve tarihiyle not edilir. Bu kayıtlar çıkarılmaz; hedef B sonuçları hem bütün kayıtlarla hem de bu notları taşımayan kayıtlarla ayrıca raporlanır. Hedef B betimleyici olduğu için bu ayrım bir karar eşiğini değiştirmez.
- Pilot sonu görüşmesi: en çok ve en az işe yarayan bölüm, güvenilmeyen sayı, eksik özellik.
- **Benimseme soruları (1.8):** pilot sonu görüşmesine UTAUT'un dört etkenini soran kısa bir bölüm eklenir (Venkatesh, Morris, Davis ve Davis 2003, MIS Quarterly 27(3)): performans beklentisi (işime yarıyor mu), çaba beklentisi (kullanmak kolay mı), sosyal etki (müşavirim ya da çevrem kullanıyor mu) ve kolaylaştırıcı koşullar (kurulum ve destek yeterli mi). B3 ya da B4 sağlanmazsa nedenin hangisi olduğu böylece ayrıştırılır.
- **Karar kartı (1.8, müşavirle denenecek):** panelin var olan sayılarından türetilen tek cümlelik haftalık özet ("Bu hafta güvenle harcayabileceğiniz tutar X TL; önce şu üç faturayı arayın") pilotta müşavirle denenir. Basit pratik kuralların karmaşık eğitimden daha etkili olduğu randomize deneyle gösterilmiştir (Drexler, Fischer ve Schoar 2014, AEJ: Applied 6(2)). Müşavir isterse panele eklenir; yeni hesap gerektirmez.
- **Fizibilite (1.6):** ilk yüklemeden ilk kasa bandına kadar geçen süre ve bu sırada yardım gerekip gerekmediği; dosyaların hangi muhasebe programından ve kim tarafından (işletme ya da mali müşavir) çıkarıldığı. Bu bilgi hazır şablonların hangi programlar için yapılacağını belirler.
- **Aksiyon (1.6):** önerilen tahsilat taslaklarından gönderilenlerin oranı ve kanalı (WhatsApp, e-posta, telefon).

**Pilot sırasında çevrimiçi ayar (önceden kayıtlı algoritma).** Her işletmenin bandı, ufku dolmuş kendi haftalık tahsilat kayıtlarıyla iki uçta ayrı ayrı güncellenir: katsayı ← katsayı + 0,1 × (aşım − 0,10) (Gibbs ve Candès 2021, uyarlanabilir konformal çıkarım; Angelopoulos, Candès ve Tibshirani 2023). Aşım, gerçekleşenin o gün gösterilen, yani o günkü katsayılarla ayarlanmış bandın dışında kalmasıdır. Katsayıların tek sınırı sıfırdır (bant ters dönmez). Bu bir el ayarı değil, önceden tanımlı bir algoritmadır; pilot verisine bakılarak değiştirilmez. Uygulanan katsayılar kayıt künyesine yazılır.

> **1.5 değişikliği (pilot verisi görülmeden, 18.10.2026).** (a) 1.4'teki uygulama gerçekleşeni ayarlanmamış banda göre değerlendiriyordu; bu durumda katsayı dengeye gelmez. Yöntemin yayımlanmış hâline göre düzeltildi. (b) 1.4'teki sınırlar (kötümser ≥ 1, iyimser ≥ 0,5) bir kurum ya da yayına dayanmıyordu. Sentetik işletmelerde 52 haftalık sıralı laboratuvarda kötümser ucu gereğinden geniş tuttular (1.000 kayıtta aşım %6,3, Kupiec p < 0,001); kaldırıldıklarında aşım %9,7 oldu (Kupiec p = 0,75, Basel yeşil). Adım büyüklüğü 0,1 değiştirilmedi. (c) Tahsilat kaydı, gerçekleşenin ölçüldüğü tanımla hesaplanır: çekle kapanan faturada kapanış günü, kısmi tahsilatlar olaylarından öğrenilen taksit alışkanlığıyla. Ayrıntı: docs/LAB_RAPORU.md.

**Pilot sonrası analiz (önceden kayıtlı).** (1) Eksiye düşme olasılıkları ve kapanış kasası bantları için CORP güvenilirlik analizi ve Brier ayrıştırması (Dimitriadis vd. 2021). (2) Kalibrasyon hatası anlamlıysa (Spiegelhalter, %5), bütün pilot işletmelerinin birleşik verisiyle izotonik yeniden ayar kurulur ve işletme dışarıda bırakılarak (leave-one-firm-out) sınanır; yalnızca dışarıda bırakılan işletmelerde Brier'i düşürüyorsa ürüne alınır.

Bu ölçütlerde değişim görülse bile araca bağlanamaz: mevsim, faiz ortamı ve müşteri karışımı aynı dönemde değişir. Nedensel bir etki iddiası ancak rastgele seçilmiş karşılaştırma grubuyla (örneğin müşterilerin yarısına öncelik listesi uygulanır, yarısına uygulanmaz) kurulabilir; bu, pilotun ikinci aşamasına bırakılmıştır.

## 6a. Pilot öncesi hazırlık (1.8)

- **Problem görüşmeleri.** Pilot daveti gönderilmeden önce 5 mali müşavir ve 5–10 işletme sahibiyle 30 dakikalık görüşme yapılır. Ürün anlatılmaz; son nakit sıkışıklığı, o gün ne yapıldığı, bugün hangi araçla takip edildiği sorulur. Hipotezler görüşmelerden önce yazılır (pilot hazırlık kiti). Dayanak: Camuffo, Cordova, Gambardella ve Spina (2020, Management Science 66(2)); kararlarını sınanabilir hipotezlere dayandıran girişimciler daha isabetli yön değiştirdi.
- **Fazla alım.** 5 işletme hedefleniyorsa en az 8–10 işletmeyle görüşmeye başlanır. İşe alım müşavir ağı ve birebir telefonla yürütülür; her işletmenin tek bir muhatabı olur. KOBİ'lerle yapılan deneylerde katılım ve son anket yanıtı düşük kalmıştır (Innovation Growth Lab).
- **Katılımcıya yazılı fayda.** Aşama 0 raporu, 13 hafta (uzarsa 26 hafta) ücretsiz kullanım ve pilot sonunda işletmenin kendi sonuçları davet metninde yazılı olarak sunulur. Davet ve tanıtım metinlerinde doğruluk iddiası kullanılmaz (Ticari Reklam Yönetmeliği m.9).
- **Kurulum denemesi.** Paket, hiç kullanılmamış bir Windows 11 bilgisayarında ya da sanal makinede, standart (yönetici olmayan) kullanıcı hesabıyla, Defender açıkken kurulur ve her ekran kaydedilir. İlk pilot kurulumları yerinde ya da ekran paylaşımıyla birlikte yapılır. Uzaktan destek aracı kullanılırsa ekranda müşteri verisi görüneceği katılımcı aydınlatma metninde yazılıdır.
- **Kullanılabilirlik testi.** Pilottan önce 5 kişi (müşavir ve ön muhasebe çalışanı) kendi dosyalarıyla, yardım almadan kurulum ve ilk yüklemeyi dener. Küçük ve tekrarlanan testler sorunların büyük kısmını ortaya çıkarır (Nielsen ve Landauer 1993; Nielsen Norman Group). Bulunan takılmalar hata düzeltmesi olarak giderilir.
- **Pilot paketlerinin saklandığı yer.** Proje, pilot paketlerini yalnızca OneDrive ve benzeri eşitlenen klasörlerin dışında, disk şifrelemesi (BitLocker ya da Windows Cihaz şifrelemesi) açık bir diskte, tek bir klasörde saklar: `C:\KobiRadarPilot\`. Tarayıcının indirme klasörü eşitlenen bir klasöre yönlendirilmiş olabileceği için gelen paket hemen bu klasöre taşınır. Proje kod klasörü OneDrive'dadır; içinde gerçek işletme verisi bulunmaz. Ek A m.5'teki "bulut depolama kullanılmaz" taahhüdü bu kuralla sağlanır. Geliştirici bilgisayarında disk şifrelemesinin açık olduğu ilk paket gelmeden önce doğrulanır.
- **Katılımcı aydınlatma metni.** Proje, işletme sahibinin ve müşavirin adı, iletişim bilgisi, haftalık form cevapları ve görüşme notları için kendi başına veri sorumlusudur. Bunlar için KVKK m.10 aydınlatma metni ayrı bir iç belgede hazırlandı (avukat onayı gerekir). Görüşme ses ya da görüntü olarak kaydedilecekse ayrıca açık rıza alınır.
- **Veri ihlali.** Müdahale planı ayrı bir iç belgede hazırlandı (avukat onayı gerekir).
- **Etik kurul.** Sonuçlar akademik bir dergide yayımlanacaksa, anket, görüşme ya da gözlemle veri toplanan araştırmalar için etik kurul izni pilot başlamadan alınır; geriye dönük izin genellikle mümkün değildir. Bağımsız yeniden hesaplamayı yapacak akademisyenin kurumu bu süreçte yardımcı olabilir.
- **Tahmin kapsamının görünürlüğü (1.9).** Her pilot raporu "Tahminin kapsamı" tablosunu taşır: kasa ve banka tutarının girildiği gün, tahsilatların işlendiği son gün, tahmine dahil kaynaklar, yüklenmediği için dahil olmayanlar ve hiçbir durumda dahil olmayanlar (yeni kredi, hesaplar ya da ortaklarla transfer, bilinmeyen yeni yükümlülükler). Dayanak: AFP, "10 Best Practices in Cash Forecasting" (varsayımlar ve kaynaklar görünür tutulur, sapmalar gerçekleşenle karşılaştırılır).
- **Proje'nin hukuki kimliği.** Ek A'daki "Proje" tarafının kim olduğu (şahıs ya da şirket), sözleşmeyi kimin imzalayacağı ve ileride fatura kesilip kesilmeyeceği ilk imzadan önce kararlaştırılır. Destek programlarına başvuru şartları şirket kuruluşunu etkileyebileceği için bu karar mali müşavirle birlikte verilir.

**Pilot başlatma kapısı (1.9).** İlk gerçek işletme verisi alınmadan önce aşağıdaki kapıların hepsi kapanmış ve kanıtı saklanmış olmalıdır. Bir kapı açıksa o işletmeyle gerçek veri işlenmez; kapı kapanınca başlanır.

| Kapı | Başlamadan önce kanıt | Açıksa |
|---|---|---|
| Hukuk ve veri | Avukat onaylı ve imzalı Ek A; katılımcı aydınlatma metni; saklama-imha süreleri ve ihlal planı sorumluları yazılı | Veri paylaşımına başlanmaz |
| Cihaz ve saklama | Geliştirici bilgisayarında ve katılımcı bilgisayarında disk şifrelemesi açık; veriler ve pilot paketleri eşitlenmeyen klasörde (panel, veritabanı eşitlenen klasördeyse uyarır) | Gerçek müşteri verisi kullanılmaz |
| Kurulum | Temiz Windows bilgisayarında açılış, internetsiz çalışma, şifreli yedek alma ve geri yükleme, sürüm güncellemesi denendi ve kaydedildi (pilot hazırlık kiti, kurulum formu) | Katılımcı kurulumuna geçilmez |
| Ölçüm | İlerleme ölçütleri tablosundaki boş sınırlar dolduruldu; protokol sürümü ve paket özeti (SHA-256) kayda geçti | Pilot sonucu yorumlanamaz; başlanmaz |
| Kullanım sınırı | Katılımcıya gölge pilot niteliği, belirsizlik bandı ve eksik veri uyarıları anlatıldı | Başlanmaz |

Dayanak: CONSORT pilot ve fizibilite uzantısı (Eldridge vd., BMJ 2016) ve SR 11-7 (model kullanımına geçmeden önce sınırların belgelenmesi). Bu kapılar ölçüt değil, ön koşuldur; pilot verisine bakılarak değiştirilmez.

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
| Kasa ve banka tutarı bugün panele girildi mi? İlk kayıttaki hesapların aynısı mı? (1.9) | Evet / Hayır; değiştiyse hangi hesap |
| Geçen haftadan bu yana yeni kredi kullanımı ya da kapanması, hesaplar ya da ortaklarla transfer, büyük kur hareketi (1.9) | Tutar ve tarih |
| Panelde "Kapsam dışı" görünen kaynak var mı? (1.9) | Hangisi |

Plan dışı kalemler not edilir çünkü kasa tahmininin değil, tahsilat tahmininin puanlandığı B1'i etkilemezler; ama yöneticinin rapora güvenini etkilerler. Kredi, transfer ve kur notları hedef B'nin aynı kapsam kuralında kullanılır (6. bölüm, hedef B).

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
- Bilgisayarda disk şifrelemesi açık olmalı (Ayarlar → Gizlilik ve güvenlik → Cihaz şifrelemesi ya da BitLocker). Kapalıysa pilot verisi yüklenmez.
- Uygulamayı kendi bilgisayarınızda açın; "Kendi verim" → "İşletme ekle" ile işletmeyi ekleyin; dosyaları yükleyin (fatura listesi ya da cari ekstre, banka ekstresi; varsa giderler, ödenecekler, çekler). Veriler bilgisayarınızdan çıkmaz.
- Sol menü → "5. Pilot: takma adlı veri paketi" → "Pilota katılıyorum" kutusunu işaretleyin; sonra "Takma adlı paketi hazırla".
- Zip'i açıp kontrol edin:
  - [ ] Müşteri unvanları ve VKN/TCKN'ler "Müşteri XXXXXX" biçiminde takma adlara dönüşmüş.
  - [ ] Fatura numaraları "ANO" ile başlayan takma numaralar.
  - [ ] Telefon, e-posta, çek keşideci adları ve banka açıklamalarındaki serbest metin yok.
  - [ ] BENİ_OKU.txt'deki fatura ve müşteri sayıları beklediğiniz gibi.
- Paketi 7-Zip (AES-256) ile parolalayın ya da uçtan uca şifreli bir kanaldan gönderin; parolayı başka bir kanaldan (telefon, SMS) iletin. Şifresiz e-posta eki kullanmayın.
- %LOCALAPPDATA%\KobiRadar\anonim_anahtar.txt dosyasını paylaşmayın ve silmeyin: sonraki aylarda aynı müşterinin aynı takma adı alması bu dosyaya bağlıdır. Bilgisayar değişecekse dosyayı güvenli biçimde taşıyın.

**3. İlk gün: geriye dönük test (Aşama 0).** Dosyalar en az 12, mümkünse 24 aylık geçmişi kapsamalı. Yüklemeden sonra "Tahmin doğruluğu" sekmesinde "Aşama 0 testini çalıştır" düğmesine basın (birkaç dakika sürer), sonra pilot raporunu indirin; sonuç işletmeyle ilk görüşmede konuşulur. Şunları not edin: dosyaların hangi programdan alındığı, ilk yüklemeden ilk kasa grafiğine kadar geçen süre, sütun eşleştirmesi ya da başka bir yardım gerekip gerekmediği.

**4. Her hafta (13 hafta).** Pazartesi güncel fatura ve banka dosyalarını yükleyin ve tahmin tarihini bugün bırakarak paneli açın; haftalık kayıt kendiliğinden alınır. "Tahmin doğruluğu" sekmesinden pilot raporunu indirip saklayın; Ek B'deki iki soruyu cevaplayın.
