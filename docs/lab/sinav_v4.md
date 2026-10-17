## Senaryo laboratuvarı: sinav kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 63 gün, ulaşılan 64 gün; senaryoların %82'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %9.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 6 / 74 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- Yok.

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %6 | %12 | yeşil | 0.043 | 0.236 | -0.154 | 0.50 | -1.29 ±0.11 | 0.234 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %4 | %15 | yeşil | 0.045 | 0.170 | -0.136 | 0.42 | -0.85 ±0.10 | 0.144 |
| mikro | 84 | %8 | %11 | yeşil | 0.719 | 0.855 | -0.208 | 0.70 | -2.13 ±0.26 | 0.592 |
| orta | 60 | %7 | %12 | yeşil | 0.413 | 0.831 | -0.108 | 0.34 | -0.80 ±0.10 | 0.905 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 78 | %4 | %14 | yeşil | 0.063 | 0.253 | -0.142 | 0.47 | -1.22 ±0.20 | 0.871 |
| 2) 0.10–0.20 | 78 | %10 | %10 | yeşil | 1.000 | 1.000 | -0.126 | 0.51 | -1.46 ±0.22 | 0.386 |
| 3) 0.20–0.30 | 78 | %5 | %13 | yeşil | 0.145 | 0.447 | -0.205 | 0.51 | -1.14 ±0.15 | 0.214 |
| 4) saklı (geliştirme aralığı dışı) | 6 | %0 | %17 | yeşil | 0.646 | 1.000 | -0.026 | 0.43 | -1.83 ±1.07 | 0.569 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 77 | %4 | %14 | yeşil | 0.063 | 0.250 | -0.245 | 0.45 | -1.36 ±0.20 | 0.311 |
| 2) 0.17–0.34 | 77 | %10 | %12 | yeşil | 1.000 | 0.703 | -0.099 | 0.48 | -1.44 ±0.22 | 0.949 |
| 3) 0.34–0.50 | 78 | %4 | %12 | yeşil | 0.063 | 0.704 | -0.129 | 0.56 | -1.08 ±0.16 | 0.156 |
| 4) saklı (geliştirme aralığı dışı) | 8 | %12 | %12 | yeşil | 1.000 | 1.000 | -0.061 | 0.43 | -1.13 ±0.66 | 0.350 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.84 | 77 | %6 | %13 | yeşil | 0.350 | 0.444 | -0.160 | 0.46 | -1.27 ±0.18 | 0.955 |
| 2) 0.84–1.07 | 77 | %6 | %13 | yeşil | 0.350 | 0.444 | -0.215 | 0.52 | -1.12 ±0.17 | 0.053 |
| 3) 1.07–1.30 | 77 | %5 | %13 | yeşil | 0.147 | 0.444 | -0.117 | 0.53 | -1.51 ±0.24 | 0.926 |
| 4) saklı (geliştirme aralığı dışı) | 9 | %11 | %0 | yeşil | 1.000 | 0.440 | 0.090 | 0.33 | -0.95 ±0.26 | 0.749 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 68 | %6 | %10 | yeşil | 0.316 | 1.000 | -0.136 | 0.50 | -1.11 ±0.16 | 0.726 |
| 2) 22–29 | 77 | %6 | %17 | yeşil | 0.350 | 0.085 | -0.230 | 0.56 | -1.27 ±0.21 | 0.967 |
| 3) 29–36 | 80 | %6 | %10 | yeşil | 0.277 | 1.000 | -0.109 | 0.46 | -1.54 ±0.22 | 0.126 |
| 4) saklı (geliştirme aralığı dışı) | 15 | %7 | %13 | yeşil | 0.733 | 1.000 | -0.089 | 0.32 | -0.82 ±0.24 | 0.597 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.41 | 77 | %9 | %6 | yeşil | 0.854 | 0.350 | -0.033 | 0.47 | -1.39 ±0.23 | 0.867 |
| 2) 0.41–0.81 | 77 | %5 | %14 | yeşil | 0.147 | 0.250 | -0.157 | 0.50 | -1.12 ±0.17 | 0.484 |
| 3) 0.81–1.20 | 77 | %5 | %18 | yeşil | 0.147 | 0.033 | -0.252 | 0.53 | -1.34 ±0.19 | 0.414 |
| 4) saklı (geliştirme aralığı dışı) | 9 | %0 | %0 | yeşil | 0.440 | 0.440 | -0.324 | 0.42 | -1.42 ±0.52 | 0.277 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 76 | %7 | %11 | yeşil | 0.351 | 1.000 | -0.091 | 0.44 | -0.98 ±0.15 | 0.750 |
| 2) 0.10–0.20 | 75 | %3 | %15 | yeşil | 0.023 | 0.245 | -0.273 | 0.50 | -1.39 ±0.20 | 0.324 |
| 3) 0.20–0.30 | 76 | %9 | %11 | yeşil | 0.854 | 1.000 | -0.066 | 0.54 | -1.48 ±0.23 | 0.655 |
| 4) saklı (geliştirme aralığı dışı) | 13 | %8 | %23 | yeşil | 1.000 | 0.388 | -0.349 | 0.56 | -1.40 ±0.67 | 0.422 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 79 | %5 | %10 | yeşil | 0.143 | 1.000 | -0.154 | 0.48 | -1.23 ±0.17 | 0.434 |
| 2) 0.20–0.40 | 79 | %6 | %10 | yeşil | 0.280 | 1.000 | -0.164 | 0.52 | -1.34 ±0.23 | 0.162 |
| 3) 0.40–0.60 | 79 | %8 | %16 | yeşil | 0.577 | 0.087 | -0.138 | 0.50 | -1.33 ±0.18 | 0.731 |
| 4) saklı (geliştirme aralığı dışı) | 3 | %0 | %33 | yeşil | 1.000 | 0.271 | -0.318 | 0.44 | -0.46 ±0.31 | 0.151 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–60 | 77 | %5 | %13 | yeşil | 0.147 | 0.444 | -0.084 | 0.54 | -1.39 ±0.17 | 0.776 |
| 2) 60–90 | 77 | %4 | %13 | yeşil | 0.063 | 0.444 | -0.228 | 0.43 | -1.09 ±0.19 | 0.266 |
| 3) 90–120 | 77 | %9 | %10 | yeşil | 0.854 | 1.000 | -0.168 | 0.54 | -1.40 ±0.23 | 0.482 |
| 4) saklı (geliştirme aralığı dışı) | 9 | %11 | %22 | yeşil | 1.000 | 0.613 | -0.003 | 0.32 | -1.11 ±0.42 | 0.046 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 75 | %7 | %15 | yeşil | 0.353 | 0.245 | -0.205 | 0.50 | -1.01 ±0.14 | 0.225 |
| 2) 0.030–0.032 | 74 | %3 | %11 | yeşil | 0.023 | 0.845 | -0.147 | 0.44 | -1.40 ±0.20 | 0.791 |
| 3) 0.032–0.034 | 75 | %11 | %12 | yeşil | 1.000 | 0.701 | -0.070 | 0.52 | -1.40 ±0.24 | 0.614 |
| 4) saklı (geliştirme aralığı dışı) | 16 | %0 | %12 | yeşil | 0.202 | 1.000 | -0.340 | 0.65 | -1.55 ±0.48 | 0.123 |


### record_lag (VUK m.219: kayıt en geç 10 gün, fişe dayanan kayıtta 45 gün; aralık varsayım)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0–5 | 72 | %4 | %11 | yeşil | 0.087 | 0.844 | -0.168 | 0.56 | -1.37 ±0.22 | 0.368 |
| 2) 5–9 | 66 | %6 | %11 | yeşil | 0.318 | 1.000 | -0.137 | 0.44 | -1.29 ±0.25 | 0.491 |
| 3) 9–14 | 92 | %8 | %16 | yeşil | 0.495 | 0.080 | -0.180 | 0.49 | -1.19 ±0.15 | 0.034 |
| 4) saklı (geliştirme aralığı dışı) | 10 | %10 | %0 | yeşil | 1.000 | 0.419 | 0.069 | 0.49 | -1.53 ±0.31 | 0.919 |


### partial_share (varsayım: faturalarını iki taksitte kapatan müşteri payı)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.14 | 76 | %8 | %9 | yeşil | 0.579 | 0.854 | -0.058 | 0.52 | -1.33 ±0.22 | 0.802 |
| 2) 0.14–0.27 | 76 | %5 | %16 | yeşil | 0.186 | 0.121 | -0.290 | 0.50 | -1.47 ±0.21 | 0.700 |
| 3) 0.27–0.40 | 76 | %7 | %11 | yeşil | 0.351 | 1.000 | -0.084 | 0.47 | -1.13 ±0.16 | 0.285 |
| 4) saklı (geliştirme aralığı dışı) | 12 | %0 | %25 | yeşil | 0.308 | 0.393 | -0.347 | 0.54 | -0.90 ±0.44 | 0.329 |


### missing_due (veri kalitesi: vadesi girilmemiş fatura payı (TTK m.1530/4-a: 30 gün))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 77 | %3 | %12 | yeşil | 0.017 | 0.703 | -0.131 | 0.42 | -1.37 ±0.19 | 0.297 |
| 2) 0.10–0.20 | 76 | %8 | %13 | yeşil | 0.579 | 0.443 | -0.162 | 0.49 | -1.25 ±0.23 | 0.336 |
| 3) 0.20–0.30 | 77 | %8 | %13 | yeşil | 0.578 | 0.444 | -0.158 | 0.57 | -1.22 ±0.18 | 0.992 |
| 4) saklı (geliştirme aralığı dışı) | 10 | %10 | %10 | yeşil | 1.000 | 1.000 | -0.243 | 0.61 | -1.45 ±0.44 | 0.765 |


### ayin_gunu

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 1–11 | 80 | %9 | %10 | yeşil | 0.722 | 1.000 | -0.115 | 0.48 | -1.42 ±0.24 | 0.986 |
| 2) 11–20 | 73 | %3 | %14 | yeşil | 0.024 | 0.325 | -0.212 | 0.52 | -1.43 ±0.19 | 0.713 |
| 3) 20–31 | 87 | %7 | %14 | yeşil | 0.379 | 0.280 | -0.141 | 0.49 | -1.04 ±0.15 | 0.020 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 18–53 | 80 | %9 | %16 | yeşil | 0.722 | 0.089 | -0.126 | 0.50 | -0.53 ±0.07 | 0.012 |
| 2) 53–85 | 80 | %5 | %14 | yeşil | 0.142 | 0.350 | -0.112 | 0.41 | -0.72 ±0.10 | 0.399 |
| 3) 85–202 | 80 | %5 | %8 | yeşil | 0.142 | 0.474 | -0.224 | 0.58 | -2.61 ±0.25 | 0.723 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 72 | %7 | %11 | yeşil | 0.442 | 0.844 | -0.203 | 0.72 | -2.22 ±0.29 | 0.817 |
| 2) 14–39 | 88 | %7 | %12 | yeşil | 0.378 | 0.474 | -0.151 | 0.46 | -1.02 ±0.14 | 0.169 |
| 3) 39–117 | 80 | %5 | %14 | yeşil | 0.142 | 0.350 | -0.114 | 0.33 | -0.74 ±0.08 | 0.692 |


### saklı_rejim

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| cheque_bounce | 16 | %0 | %12 | yeşil | 0.202 | 1.000 | -0.340 | 0.65 | -1.55 ±0.48 | 0.123 |
| cheque_share | 3 | %0 | %33 | yeşil | 1.000 | 0.271 | -0.318 | 0.44 | -0.46 ±0.31 | 0.151 |
| cheque_term | 9 | %11 | %22 | yeşil | 1.000 | 0.613 | -0.003 | 0.32 | -1.11 ±0.42 | 0.046 |
| geliştirme aralığı içi | 120 | %7 | %12 | yeşil | 0.231 | 0.649 | -0.134 | 0.52 | -1.34 ±0.17 | 0.499 |
| history | 15 | %7 | %13 | yeşil | 0.733 | 1.000 | -0.089 | 0.32 | -0.82 ±0.24 | 0.597 |
| inflation | 8 | %12 | %12 | yeşil | 1.000 | 1.000 | -0.061 | 0.43 | -1.13 ±0.66 | 0.350 |
| missing_due | 10 | %10 | %10 | yeşil | 1.000 | 1.000 | -0.243 | 0.61 | -1.45 ±0.44 | 0.765 |
| partial_share | 12 | %0 | %25 | yeşil | 0.308 | 0.393 | -0.347 | 0.54 | -0.90 ±0.44 | 0.329 |
| record_lag | 10 | %10 | %0 | yeşil | 1.000 | 0.419 | 0.069 | 0.49 | -1.53 ±0.31 | 0.919 |
| season_amp | 6 | %0 | %17 | yeşil | 0.646 | 1.000 | -0.026 | 0.43 | -1.83 ±1.07 | 0.569 |
| shock | 13 | %8 | %23 | yeşil | 1.000 | 0.388 | -0.349 | 0.56 | -1.40 ±0.67 | 0.422 |
| size_sigma | 9 | %11 | %0 | yeşil | 1.000 | 0.440 | 0.090 | 0.33 | -0.95 ±0.26 | 0.749 |
| trend | 9 | %0 | %0 | yeşil | 0.440 | 0.440 | -0.324 | 0.42 | -1.42 ±0.52 | 0.277 |


