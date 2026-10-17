# Senaryo Laboratuvarı

Tarih: 17 Ekim 2026. Kod: `src/radar/lab.py`. Ayrıntılı tablolar: [lab/gelistirme_v1.md](lab/gelistirme_v1.md), [lab/sinav_v1.md](lab/sinav_v1.md). Sınav koşuları kaydı: [lab/sinav_kaydi.csv](lab/sinav_kaydi.csv).

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

Örnekleme Latin hiperküp yöntemiyle yapılır; her boyut kendi aralığında eşit kaplanır.

**Tahsil süresi nasıl oturtulur:** Her senaryoda gecikme ölçeği, işletmenin tahsil süresi hedefe eşit olana kadar ikiye bölme yöntemiyle aranır. Hedefin altında kalan sektörlerde (peşine yakın satış yapanlar) vadeler de aynı oranda kısaltılır. Karşılaştırmada vadesini 180 günden fazla geçmiş açık alacaklar şüpheli alacak sayılıp dışarıda bırakılır. TCMB oranının dayandığı bilanço tutarında da şüpheli alacaklar karşılıkla netleşir (Tekdüzen Hesap Planı 128/129).

**Laboratuvarın ortaya çıkardığı bir üretici kusuru:** Eski sentetik veri, gerçek bir KOBİ'ye göre daha az yoğunlaşmıştı. 40 müşteride Gini 0,56 çıkıyordu; gerçek KOBİ'nin alt örneklemlerinde ise 0,61. Laboratuvar artık gerçek aralığı kapsıyor. Eski çalışmaların varsayılan verisi değişmedi; yeni boyutlar ayrı rastgele sayı akışıyla eklendi.

## Sonuçlar

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

- Kısmi ödemeler ve veri kalitesi sorunları (eksik vade, mükerrer fatura) laboratuvarda yok. Bunlar uygulamada ayrı testlerle sınanıyor.
- Çek ve senet: üretici çek üretmiyor. Karşılıksız çek oranı (TBB) simülasyonda sabit.
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
