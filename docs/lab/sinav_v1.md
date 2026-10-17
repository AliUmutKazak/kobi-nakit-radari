## Senaryo laboratuvarı: sinav kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 65 gün, ulaşılan 63 gün; senaryoların %78'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %12.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 1 / 41 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- size_sigma = 4) saklı (geliştirme aralığı dışı) (n=17): Basel sarı
- shock = 4) saklı (geliştirme aralığı dışı) (n=20): Basel sarı
- saklı_rejim = shock (n=20): Basel sarı
- saklı_rejim = size_sigma (n=17): Basel sarı

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %10 | %9 | yeşil | 1.000 | 0.672 | -0.120 | 0.59 | -0.93 ±0.09 | 0.280 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %9 | %9 | yeşil | 0.869 | 0.869 | -0.060 | 0.51 | -0.75 ±0.11 | 0.532 |
| mikro | 84 | %8 | %7 | yeşil | 0.719 | 0.385 | -0.288 | 0.85 | -1.35 ±0.22 | 0.536 |
| orta | 60 | %13 | %12 | yeşil | 0.519 | 0.831 | 0.016 | 0.38 | -0.60 ±0.08 | 0.520 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 73 | %12 | %8 | yeşil | 0.555 | 0.702 | -0.033 | 0.55 | -1.02 ±0.17 | 0.499 |
| 2) 0.10–0.20 | 72 | %11 | %8 | yeşil | 0.844 | 0.703 | 0.020 | 0.56 | -0.95 ±0.15 | 0.217 |
| 3) 0.20–0.30 | 73 | %8 | %11 | yeşil | 0.702 | 0.844 | -0.330 | 0.72 | -0.82 ±0.18 | 0.794 |
| 4) saklı (geliştirme aralığı dışı) | 22 | %5 | %9 | yeşil | 0.511 | 1.000 | -0.175 | 0.43 | -0.89 ±0.26 | 0.540 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 74 | %12 | %8 | yeşil | 0.558 | 0.701 | -0.091 | 0.57 | -0.85 ±0.16 | 0.218 |
| 2) 0.17–0.33 | 73 | %11 | %10 | yeşil | 0.844 | 1.000 | -0.132 | 0.64 | -0.98 ±0.20 | 0.327 |
| 3) 0.33–0.50 | 74 | %8 | %9 | yeşil | 0.701 | 1.000 | -0.103 | 0.57 | -0.92 ±0.14 | 0.049 |
| 4) saklı (geliştirme aralığı dışı) | 19 | %5 | %11 | yeşil | 0.715 | 1.000 | -0.263 | 0.61 | -0.99 ±0.41 | 0.792 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.83 | 74 | %9 | %11 | yeşil | 1.000 | 0.845 | -0.117 | 0.56 | -0.96 ±0.18 | 0.650 |
| 2) 0.83–1.07 | 74 | %7 | %7 | yeşil | 0.356 | 0.356 | -0.022 | 0.50 | -1.01 ±0.15 | 0.148 |
| 3) 1.07–1.30 | 75 | %11 | %11 | yeşil | 1.000 | 1.000 | -0.109 | 0.61 | -0.95 ±0.17 | 0.873 |
| 4) saklı (geliştirme aralığı dışı) | 17 | %24 | %6 | sarı | 0.249 | 0.720 | -0.613 | 1.12 | -0.31 ±0.38 | 0.687 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 65 | %14 | %11 | yeşil | 0.408 | 1.000 | -0.168 | 0.66 | -0.85 ±0.17 | 0.356 |
| 2) 22–29 | 72 | %10 | %4 | yeşil | 1.000 | 0.087 | 0.041 | 0.56 | -0.83 ±0.12 | 0.093 |
| 3) 29–36 | 77 | %8 | %13 | yeşil | 0.578 | 0.444 | -0.258 | 0.63 | -1.14 ±0.22 | 0.589 |
| 4) saklı (geliştirme aralığı dışı) | 26 | %8 | %8 | yeşil | 0.770 | 0.770 | -0.041 | 0.43 | -0.75 ±0.16 | 0.297 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.41 | 75 | %4 | %13 | yeşil | 0.066 | 0.441 | -0.181 | 0.59 | -0.96 ±0.18 | 0.823 |
| 2) 0.41–0.80 | 74 | %14 | %7 | yeşil | 0.441 | 0.356 | -0.088 | 0.54 | -0.98 ±0.17 | 0.136 |
| 3) 0.80–1.20 | 75 | %13 | %8 | yeşil | 0.441 | 0.582 | -0.139 | 0.70 | -0.80 ±0.15 | 0.494 |
| 4) saklı (geliştirme aralığı dışı) | 16 | %6 | %6 | yeşil | 0.725 | 0.725 | 0.099 | 0.40 | -1.12 ±0.29 | 0.922 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 73 | %11 | %5 | yeşil | 0.844 | 0.192 | -0.096 | 0.60 | -0.77 ±0.15 | 0.583 |
| 2) 0.10–0.20 | 73 | %10 | %12 | yeşil | 1.000 | 0.555 | -0.274 | 0.64 | -0.75 ±0.17 | 0.292 |
| 3) 0.20–0.30 | 74 | %7 | %9 | yeşil | 0.356 | 1.000 | -0.068 | 0.53 | -1.10 ±0.16 | 0.141 |
| 4) saklı (geliştirme aralığı dışı) | 20 | %20 | %10 | sarı | 0.255 | 1.000 | 0.155 | 0.66 | -1.48 ±0.42 | 0.927 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–50 | 80 | %15 | %18 | yeşil | 0.188 | 0.062 | -0.188 | 0.68 | -0.21 ±0.07 | 0.245 |
| 2) 50–82 | 80 | %11 | %6 | yeşil | 0.853 | 0.277 | 0.022 | 0.43 | -0.56 ±0.07 | 0.487 |
| 3) 82–193 | 80 | %4 | %4 | yeşil | 0.048 | 0.048 | -0.195 | 0.68 | -2.01 ±0.21 | 0.030 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 73 | %10 | %8 | yeşil | 1.000 | 0.702 | -0.354 | 0.90 | -1.32 ±0.23 | 0.313 |
| 2) 14–39 | 86 | %9 | %9 | yeşil | 0.862 | 0.862 | 0.006 | 0.53 | -0.77 ±0.13 | 0.918 |
| 3) 39–118 | 81 | %11 | %10 | yeşil | 0.853 | 1.000 | -0.044 | 0.39 | -0.74 ±0.10 | 0.437 |


### saklı_rejim

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| geliştirme aralığı içi | 120 | %9 | %10 | yeşil | 0.768 | 1.000 | -0.111 | 0.60 | -0.93 ±0.13 | 0.561 |
| history | 26 | %8 | %8 | yeşil | 0.770 | 0.770 | -0.041 | 0.43 | -0.75 ±0.16 | 0.297 |
| inflation | 19 | %5 | %11 | yeşil | 0.715 | 1.000 | -0.263 | 0.61 | -0.99 ±0.41 | 0.792 |
| season_amp | 22 | %5 | %9 | yeşil | 0.511 | 1.000 | -0.175 | 0.43 | -0.89 ±0.26 | 0.540 |
| shock | 20 | %20 | %10 | sarı | 0.255 | 1.000 | 0.155 | 0.66 | -1.48 ±0.42 | 0.927 |
| size_sigma | 17 | %24 | %6 | sarı | 0.249 | 0.720 | -0.613 | 1.12 | -0.31 ±0.38 | 0.687 |
| trend | 16 | %6 | %6 | yeşil | 0.725 | 0.725 | 0.099 | 0.40 | -1.12 ±0.29 | 0.922 |


