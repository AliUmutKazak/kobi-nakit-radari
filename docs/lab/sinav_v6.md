## Senaryo laboratuvarı: sinav kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 69 gün, ulaşılan 68 gün; senaryoların %81'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %10.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 5 / 79 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- inflation = 4) saklı (geliştirme aralığı dışı) (n=12): Basel sarı
- record_lag = 3) 10–14 (n=77): Basel sarı
- saklı_rejim = inflation (n=12): Basel sarı

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %7 | %10 | yeşil | 0.134 | 1.000 | -0.119 | 0.56 | -1.13 ±0.09 | 0.958 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %7 | %12 | yeşil | 0.406 | 0.495 | -0.032 | 0.53 | -0.98 ±0.12 | 0.647 |
| mikro | 84 | %6 | %10 | yeşil | 0.218 | 1.000 | -0.305 | 0.70 | -1.41 ±0.18 | 0.524 |
| orta | 60 | %8 | %7 | yeşil | 0.686 | 0.413 | 0.003 | 0.42 | -0.98 ±0.14 | 0.927 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 77 | %12 | %12 | yeşil | 0.703 | 0.703 | -0.023 | 0.56 | -1.14 ±0.16 | 0.174 |
| 2) 0.10–0.20 | 77 | %4 | %8 | yeşil | 0.063 | 0.578 | -0.156 | 0.53 | -1.13 ±0.14 | 0.476 |
| 3) 0.20–0.30 | 78 | %6 | %8 | yeşil | 0.349 | 0.577 | -0.109 | 0.57 | -1.17 ±0.17 | 0.042 |
| 4) saklı (geliştirme aralığı dışı) | 8 | %0 | %38 | yeşil | 0.469 | 0.038 | -0.787 | 0.79 | -0.60 ±0.46 | 0.889 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 76 | %7 | %11 | yeşil | 0.351 | 1.000 | -0.076 | 0.52 | -1.11 ±0.16 | 0.200 |
| 2) 0.17–0.33 | 76 | %3 | %12 | yeşil | 0.023 | 0.702 | -0.295 | 0.57 | -0.98 ±0.16 | 0.127 |
| 3) 0.33–0.50 | 76 | %9 | %8 | yeşil | 0.854 | 0.579 | -0.005 | 0.59 | -1.21 ±0.15 | 0.958 |
| 4) saklı (geliştirme aralığı dışı) | 12 | %25 | %8 | sarı | 0.393 | 1.000 | 0.000 | 0.65 | -1.61 ±0.40 | 0.751 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.83 | 77 | %8 | %13 | yeşil | 0.578 | 0.444 | -0.136 | 0.58 | -1.27 ±0.18 | 0.659 |
| 2) 0.83–1.07 | 76 | %8 | %4 | yeşil | 0.579 | 0.065 | -0.044 | 0.42 | -1.14 ±0.14 | 0.586 |
| 3) 1.07–1.29 | 77 | %6 | %10 | yeşil | 0.350 | 1.000 | -0.100 | 0.60 | -1.07 ±0.14 | 0.313 |
| 4) saklı (geliştirme aralığı dışı) | 10 | %0 | %30 | yeşil | 0.419 | 0.070 | -0.701 | 1.13 | -0.38 ±0.48 | 0.872 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 69 | %3 | %14 | yeşil | 0.034 | 0.316 | -0.310 | 0.63 | -0.90 ±0.18 | 0.682 |
| 2) 22–29 | 77 | %6 | %8 | yeşil | 0.350 | 0.578 | 0.030 | 0.55 | -1.29 ±0.16 | 0.896 |
| 3) 29–36 | 81 | %11 | %9 | yeşil | 0.853 | 0.721 | -0.125 | 0.55 | -1.21 ±0.15 | 0.928 |
| 4) saklı (geliştirme aralığı dışı) | 13 | %8 | %8 | yeşil | 1.000 | 1.000 | 0.051 | 0.38 | -0.80 ±0.30 | 0.191 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.41 | 76 | %9 | %13 | yeşil | 0.854 | 0.443 | -0.120 | 0.53 | -1.08 ±0.15 | 0.457 |
| 2) 0.41–0.79 | 76 | %9 | %9 | yeşil | 0.854 | 0.854 | 0.021 | 0.61 | -1.45 ±0.15 | 0.381 |
| 3) 0.79–1.20 | 77 | %3 | %8 | yeşil | 0.017 | 0.578 | -0.261 | 0.54 | -0.89 ±0.17 | 0.633 |
| 4) saklı (geliştirme aralığı dışı) | 11 | %9 | %9 | yeşil | 1.000 | 1.000 | -0.078 | 0.51 | -0.96 ±0.29 | 0.255 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 78 | %5 | %6 | yeşil | 0.145 | 0.349 | -0.144 | 0.52 | -1.19 ±0.18 | 0.482 |
| 2) 0.10–0.20 | 78 | %8 | %13 | yeşil | 0.577 | 0.447 | -0.136 | 0.60 | -1.00 ±0.13 | 0.039 |
| 3) 0.20–0.30 | 78 | %8 | %10 | yeşil | 0.577 | 1.000 | -0.065 | 0.55 | -1.18 ±0.16 | 0.147 |
| 4) saklı (geliştirme aralığı dışı) | 6 | %17 | %17 | yeşil | 1.000 | 1.000 | -0.268 | 0.80 | -1.29 ±0.62 | 0.455 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 78 | %5 | %9 | yeşil | 0.145 | 0.853 | -0.090 | 0.56 | -1.12 ±0.15 | 0.804 |
| 2) 0.20–0.40 | 78 | %8 | %13 | yeşil | 0.577 | 0.447 | -0.279 | 0.67 | -1.14 ±0.18 | 0.687 |
| 3) 0.40–0.60 | 79 | %9 | %9 | yeşil | 0.853 | 0.853 | 0.001 | 0.48 | -1.09 ±0.13 | 0.837 |
| 4) saklı (geliştirme aralığı dışı) | 5 | %0 | %0 | yeşil | 0.672 | 0.672 | 0.043 | 0.31 | -1.69 ±0.71 | 0.271 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–60 | 79 | %9 | %8 | yeşil | 0.853 | 0.577 | -0.031 | 0.59 | -1.24 ±0.16 | 0.915 |
| 2) 60–90 | 78 | %10 | %12 | yeşil | 1.000 | 0.704 | -0.081 | 0.57 | -1.10 ±0.14 | 0.635 |
| 3) 90–120 | 79 | %3 | %11 | yeşil | 0.016 | 0.706 | -0.224 | 0.53 | -1.06 ±0.16 | 0.429 |
| 4) saklı (geliştirme aralığı dışı) | 4 | %0 | %0 | yeşil | 0.708 | 0.708 | -0.515 | 0.51 | -0.81 ±0.61 | 0.159 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 78 | %9 | %8 | yeşil | 0.853 | 0.577 | -0.152 | 0.57 | -1.05 ±0.15 | 0.566 |
| 2) 0.030–0.032 | 78 | %5 | %14 | yeşil | 0.145 | 0.253 | -0.118 | 0.58 | -1.09 ±0.16 | 0.584 |
| 3) 0.032–0.034 | 78 | %6 | %9 | yeşil | 0.349 | 0.853 | -0.123 | 0.53 | -1.23 ±0.15 | 0.982 |
| 4) saklı (geliştirme aralığı dışı) | 6 | %17 | %0 | yeşil | 1.000 | 0.646 | 0.363 | 0.57 | -1.34 ±0.65 | 0.733 |


### record_lag (VUK m.219: kayıt en geç 10 gün, fişe dayanan kayıtta 45 gün; aralık varsayım)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0–5 | 71 | %1 | %4 | yeşil | 0.007 | 0.089 | -0.147 | 0.43 | -1.24 ±0.18 | 0.842 |
| 2) 5–10 | 81 | %5 | %11 | yeşil | 0.141 | 0.853 | -0.235 | 0.62 | -0.98 ±0.14 | 0.427 |
| 3) 10–14 | 77 | %16 | %13 | sarı | 0.186 | 0.444 | -0.003 | 0.63 | -1.19 ±0.16 | 0.491 |
| 4) saklı (geliştirme aralığı dışı) | 11 | %0 | %18 | yeşil | 0.403 | 0.616 | 0.104 | 0.55 | -1.04 ±0.26 | 0.503 |


### partial_share (varsayım: faturalarını iki taksitte kapatan müşteri payı)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.14 | 76 | %11 | %12 | yeşil | 1.000 | 0.702 | -0.108 | 0.55 | -1.11 ±0.15 | 0.038 |
| 2) 0.14–0.27 | 76 | %4 | %8 | yeşil | 0.065 | 0.579 | -0.071 | 0.45 | -1.36 ±0.17 | 0.084 |
| 3) 0.27–0.40 | 77 | %8 | %9 | yeşil | 0.578 | 0.854 | -0.104 | 0.65 | -1.01 ±0.15 | 0.722 |
| 4) saklı (geliştirme aralığı dışı) | 11 | %0 | %18 | yeşil | 0.403 | 0.616 | -0.626 | 0.75 | -0.47 ±0.41 | 0.697 |


### missing_due (veri kalitesi: vadesi girilmemiş fatura payı (TTK m.1530/4-a: 30 gün))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 76 | %9 | %16 | yeşil | 0.854 | 0.121 | -0.038 | 0.50 | -1.01 ±0.14 | 0.258 |
| 2) 0.10–0.20 | 76 | %7 | %5 | yeşil | 0.351 | 0.186 | -0.147 | 0.50 | -1.39 ±0.16 | 0.507 |
| 3) 0.20–0.30 | 77 | %6 | %9 | yeşil | 0.350 | 0.854 | -0.197 | 0.66 | -1.01 ±0.16 | 0.457 |
| 4) saklı (geliştirme aralığı dışı) | 11 | %0 | %9 | yeşil | 0.403 | 1.000 | 0.064 | 0.66 | -0.98 ±0.46 | 0.622 |


### outflow_sigma (varsayım: aylık giderlerin dalgalanması (log ölçekte sapma))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 76 | %7 | %13 | yeşil | 0.351 | 0.443 | -0.177 | 0.57 | -1.13 ±0.17 | 0.510 |
| 2) 0.10–0.20 | 76 | %7 | %12 | yeşil | 0.351 | 0.702 | -0.170 | 0.54 | -1.18 ±0.16 | 0.345 |
| 3) 0.20–0.30 | 76 | %7 | %7 | yeşil | 0.351 | 0.351 | -0.085 | 0.54 | -1.09 ±0.15 | 0.522 |
| 4) saklı (geliştirme aralığı dışı) | 12 | %17 | %0 | yeşil | 0.623 | 0.308 | 0.355 | 0.78 | -1.02 ±0.32 | 0.214 |


### ayin_gunu

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 1–10 | 73 | %7 | %7 | yeşil | 0.441 | 0.441 | -0.083 | 0.59 | -1.37 ±0.18 | 0.653 |
| 2) 10–20 | 82 | %5 | %10 | yeşil | 0.110 | 1.000 | -0.124 | 0.47 | -0.88 ±0.11 | 0.814 |
| 3) 20–31 | 85 | %9 | %13 | yeşil | 0.863 | 0.470 | -0.144 | 0.63 | -1.15 ±0.16 | 0.459 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 16–54 | 80 | %8 | %11 | yeşil | 0.474 | 0.853 | -0.099 | 0.50 | -0.42 ±0.08 | 0.059 |
| 2) 54–89 | 80 | %8 | %11 | yeşil | 0.474 | 0.853 | -0.059 | 0.52 | -0.78 ±0.10 | 0.226 |
| 3) 89–188 | 80 | %6 | %8 | yeşil | 0.277 | 0.474 | -0.199 | 0.66 | -2.18 ±0.18 | 0.480 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 75 | %5 | %9 | yeşil | 0.187 | 0.855 | -0.290 | 0.71 | -1.45 ±0.19 | 0.332 |
| 2) 14–41 | 84 | %6 | %12 | yeşil | 0.218 | 0.583 | -0.078 | 0.55 | -1.00 ±0.14 | 0.549 |
| 3) 41–118 | 81 | %10 | %9 | yeşil | 1.000 | 0.721 | -0.003 | 0.43 | -0.97 ±0.12 | 0.781 |


### saklı_rejim

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| cheque_bounce | 6 | %17 | %0 | yeşil | 1.000 | 0.646 | 0.363 | 0.57 | -1.34 ±0.65 | 0.733 |
| cheque_share | 5 | %0 | %0 | yeşil | 0.672 | 0.672 | 0.043 | 0.31 | -1.69 ±0.71 | 0.271 |
| cheque_term | 4 | %0 | %0 | yeşil | 0.708 | 0.708 | -0.515 | 0.51 | -0.81 ±0.61 | 0.159 |
| geliştirme aralığı içi | 120 | %7 | %8 | yeşil | 0.231 | 0.373 | -0.108 | 0.47 | -1.29 ±0.13 | 0.272 |
| history | 13 | %8 | %8 | yeşil | 1.000 | 1.000 | 0.051 | 0.38 | -0.80 ±0.30 | 0.191 |
| inflation | 12 | %25 | %8 | sarı | 0.393 | 1.000 | 0.000 | 0.65 | -1.61 ±0.40 | 0.751 |
| missing_due | 11 | %0 | %9 | yeşil | 0.403 | 1.000 | 0.064 | 0.66 | -0.98 ±0.46 | 0.622 |
| outflow_sigma | 12 | %17 | %0 | yeşil | 0.623 | 0.308 | 0.355 | 0.78 | -1.02 ±0.32 | 0.214 |
| partial_share | 11 | %0 | %18 | yeşil | 0.403 | 0.616 | -0.626 | 0.75 | -0.47 ±0.41 | 0.697 |
| record_lag | 11 | %0 | %18 | yeşil | 0.403 | 0.616 | 0.104 | 0.55 | -1.04 ±0.26 | 0.503 |
| season_amp | 8 | %0 | %38 | yeşil | 0.469 | 0.038 | -0.787 | 0.79 | -0.60 ±0.46 | 0.889 |
| shock | 6 | %17 | %17 | yeşil | 1.000 | 1.000 | -0.268 | 0.80 | -1.29 ±0.62 | 0.455 |
| size_sigma | 10 | %0 | %30 | yeşil | 0.419 | 0.070 | -0.701 | 1.13 | -0.38 ±0.48 | 0.872 |
| trend | 11 | %9 | %9 | yeşil | 1.000 | 1.000 | -0.078 | 0.51 | -0.96 ±0.29 | 0.255 |


