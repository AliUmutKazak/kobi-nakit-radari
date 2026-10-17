## Senaryo laboratuvarı: gelistirme kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 68 gün, ulaşılan 69 gün; senaryoların %83'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %8.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 3 / 28 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- Yok.

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %7 | %6 | yeşil | 0.134 | 0.025 | 0.005 | 0.49 | -1.04 ±0.09 | 0.004 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %5 | %6 | yeşil | 0.127 | 0.240 | -0.025 | 0.42 | -0.76 ±0.10 | 0.013 |
| mikro | 84 | %11 | %6 | yeşil | 0.855 | 0.218 | 0.079 | 0.69 | -1.56 ±0.20 | 0.518 |
| orta | 60 | %5 | %5 | yeşil | 0.210 | 0.210 | -0.051 | 0.32 | -0.77 ±0.14 | 0.074 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %2 | %6 | yeşil | 0.016 | 0.277 | -0.027 | 0.43 | -1.15 ±0.17 | 0.031 |
| 2) 0.10–0.20 | 80 | %11 | %4 | yeşil | 0.853 | 0.048 | 0.105 | 0.48 | -1.12 ±0.14 | 0.035 |
| 3) 0.20–0.30 | 80 | %8 | %8 | yeşil | 0.474 | 0.474 | -0.062 | 0.57 | -0.86 ±0.16 | 0.492 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 80 | %8 | %4 | yeşil | 0.474 | 0.048 | 0.048 | 0.49 | -1.33 ±0.16 | 0.288 |
| 2) 0.17–0.33 | 80 | %9 | %5 | yeşil | 0.722 | 0.142 | 0.030 | 0.50 | -1.02 ±0.14 | 0.088 |
| 3) 0.33–0.50 | 80 | %5 | %9 | yeşil | 0.142 | 0.722 | -0.063 | 0.48 | -0.78 ±0.16 | 0.029 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.83 | 80 | %6 | %5 | yeşil | 0.277 | 0.142 | 0.009 | 0.46 | -1.16 ±0.16 | 0.004 |
| 2) 0.83–1.07 | 80 | %8 | %2 | yeşil | 0.474 | 0.016 | 0.035 | 0.46 | -0.97 ±0.14 | 0.291 |
| 3) 1.07–1.30 | 80 | %8 | %10 | yeşil | 0.474 | 1.000 | -0.029 | 0.55 | -1.00 ±0.17 | 0.320 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 74 | %8 | %4 | yeşil | 0.701 | 0.085 | 0.010 | 0.52 | -0.83 ±0.14 | 0.455 |
| 2) 22–29 | 81 | %6 | %7 | yeşil | 0.276 | 0.472 | -0.004 | 0.53 | -0.99 ±0.17 | 0.230 |
| 3) 29–36 | 85 | %7 | %6 | yeşil | 0.382 | 0.216 | 0.009 | 0.44 | -1.28 ±0.15 | 0.003 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.40 | 80 | %9 | %2 | yeşil | 0.722 | 0.016 | 0.098 | 0.44 | -0.93 ±0.13 | 0.201 |
| 2) 0.40–0.80 | 80 | %2 | %11 | yeşil | 0.016 | 0.853 | -0.210 | 0.58 | -0.90 ±0.14 | 0.187 |
| 3) 0.80–1.20 | 80 | %10 | %4 | yeşil | 1.000 | 0.048 | 0.127 | 0.46 | -1.30 ±0.19 | 0.019 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %6 | %5 | yeşil | 0.277 | 0.142 | -0.003 | 0.42 | -1.05 ±0.17 | 0.038 |
| 2) 0.10–0.20 | 80 | %6 | %6 | yeşil | 0.277 | 0.277 | -0.072 | 0.48 | -1.01 ±0.15 | 0.255 |
| 3) 0.20–0.30 | 80 | %9 | %6 | yeşil | 0.722 | 0.277 | 0.090 | 0.58 | -1.06 ±0.15 | 0.080 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 13–53 | 80 | %9 | %10 | yeşil | 0.722 | 1.000 | -0.084 | 0.51 | -0.26 ±0.07 | 0.549 |
| 2) 53–89 | 80 | %6 | %6 | yeşil | 0.277 | 0.277 | -0.007 | 0.40 | -0.63 ±0.10 | 0.157 |
| 3) 89–297 | 80 | %6 | %1 | yeşil | 0.277 | 0.003 | 0.105 | 0.57 | -2.23 ±0.18 | 0.004 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–15 | 79 | %11 | %6 | yeşil | 0.706 | 0.280 | 0.059 | 0.71 | -1.58 ±0.21 | 0.602 |
| 2) 15–39 | 81 | %4 | %7 | yeşil | 0.047 | 0.472 | -0.064 | 0.43 | -0.78 ±0.11 | 0.056 |
| 3) 39–119 | 80 | %6 | %4 | yeşil | 0.277 | 0.048 | 0.021 | 0.34 | -0.78 ±0.11 | 0.013 |

