## Senaryo laboratuvarı: sinav kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 70 gün, ulaşılan 71 gün; senaryoların %85'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %6.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 3 / 56 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- trend = 4) saklı (geliştirme aralığı dışı) (n=11): Basel sarı
- cheque_bounce = 4) saklı (geliştirme aralığı dışı) (n=13): Basel sarı
- saklı_rejim = cheque_bounce (n=13): Basel sarı
- saklı_rejim = trend (n=11): Basel sarı

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %8 | %6 | yeşil | 0.287 | 0.043 | -0.044 | 0.37 | -0.95 ±0.08 | 0.011 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %6 | %3 | yeşil | 0.240 | 0.014 | 0.001 | 0.31 | -0.87 ±0.11 | 0.032 |
| mikro | 84 | %7 | %7 | yeşil | 0.385 | 0.385 | -0.124 | 0.51 | -1.21 ±0.18 | 0.282 |
| orta | 60 | %12 | %10 | yeşil | 0.831 | 1.000 | -0.003 | 0.29 | -0.73 ±0.09 | 0.253 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 76 | %5 | %7 | yeşil | 0.186 | 0.351 | -0.054 | 0.35 | -0.74 ±0.10 | 0.485 |
| 2) 0.10–0.20 | 76 | %7 | %7 | yeşil | 0.351 | 0.351 | -0.001 | 0.37 | -1.14 ±0.18 | 0.293 |
| 3) 0.20–0.30 | 76 | %12 | %5 | yeşil | 0.702 | 0.186 | -0.064 | 0.40 | -1.03 ±0.14 | 0.042 |
| 4) saklı (geliştirme aralığı dışı) | 12 | %8 | %8 | yeşil | 1.000 | 1.000 | -0.118 | 0.42 | -0.62 ±0.24 | 0.064 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.16 | 76 | %5 | %7 | yeşil | 0.186 | 0.351 | 0.029 | 0.36 | -1.06 ±0.14 | 0.090 |
| 2) 0.16–0.33 | 75 | %8 | %4 | yeşil | 0.582 | 0.066 | -0.052 | 0.35 | -1.00 ±0.12 | 0.372 |
| 3) 0.33–0.50 | 76 | %11 | %9 | yeşil | 1.000 | 0.854 | -0.102 | 0.43 | -0.86 ±0.17 | 0.088 |
| 4) saklı (geliştirme aralığı dışı) | 13 | %8 | %0 | yeşil | 1.000 | 0.288 | -0.077 | 0.31 | -0.66 ±0.20 | 0.517 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.83 | 76 | %7 | %8 | yeşil | 0.351 | 0.579 | -0.094 | 0.38 | -0.86 ±0.12 | 0.090 |
| 2) 0.83–1.07 | 76 | %5 | %5 | yeşil | 0.186 | 0.186 | 0.031 | 0.32 | -1.01 ±0.15 | 0.030 |
| 3) 1.07–1.30 | 77 | %13 | %5 | yeşil | 0.444 | 0.147 | -0.049 | 0.41 | -1.01 ±0.15 | 0.547 |
| 4) saklı (geliştirme aralığı dışı) | 11 | %0 | %9 | yeşil | 0.403 | 1.000 | -0.171 | 0.49 | -0.86 ±0.32 | 0.827 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 70 | %9 | %9 | yeşil | 0.706 | 0.706 | -0.104 | 0.45 | -0.61 ±0.12 | 0.388 |
| 2) 22–29 | 76 | %11 | %3 | yeşil | 1.000 | 0.023 | 0.059 | 0.31 | -1.05 ±0.14 | 0.062 |
| 3) 29–36 | 83 | %6 | %5 | yeşil | 0.220 | 0.108 | -0.050 | 0.34 | -1.21 ±0.15 | 0.000 |
| 4) saklı (geliştirme aralığı dışı) | 11 | %0 | %27 | yeşil | 0.403 | 0.090 | -0.318 | 0.62 | -0.61 ±0.25 | 0.852 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.39 | 76 | %11 | %5 | yeşil | 1.000 | 0.186 | -0.061 | 0.41 | -0.90 ±0.12 | 0.073 |
| 2) 0.39–0.77 | 76 | %3 | %7 | yeşil | 0.023 | 0.351 | -0.043 | 0.34 | -0.84 ±0.11 | 0.106 |
| 3) 0.77–1.20 | 77 | %6 | %6 | yeşil | 0.350 | 0.350 | -0.074 | 0.36 | -1.13 ±0.19 | 0.261 |
| 4) saklı (geliştirme aralığı dışı) | 11 | %36 | %9 | sarı | 0.019 | 1.000 | 0.283 | 0.50 | -0.86 ±0.26 | 0.965 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 74 | %9 | %4 | yeşil | 1.000 | 0.085 | -0.064 | 0.39 | -0.92 ±0.11 | 0.671 |
| 2) 0.10–0.20 | 74 | %9 | %8 | yeşil | 1.000 | 0.701 | -0.035 | 0.38 | -0.92 ±0.14 | 0.017 |
| 3) 0.20–0.30 | 75 | %4 | %7 | yeşil | 0.066 | 0.353 | -0.040 | 0.35 | -1.05 ±0.17 | 0.179 |
| 4) saklı (geliştirme aralığı dışı) | 17 | %12 | %6 | yeşil | 1.000 | 0.720 | -0.006 | 0.42 | -0.81 ±0.25 | 0.365 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 74 | %9 | %3 | yeşil | 1.000 | 0.023 | -0.021 | 0.46 | -1.00 ±0.16 | 0.622 |
| 2) 0.20–0.40 | 74 | %11 | %7 | yeşil | 0.845 | 0.356 | -0.057 | 0.38 | -0.79 ±0.12 | 0.040 |
| 3) 0.40–0.60 | 74 | %4 | %11 | yeşil | 0.085 | 0.845 | -0.064 | 0.32 | -0.95 ±0.13 | 0.041 |
| 4) saklı (geliştirme aralığı dışı) | 18 | %6 | %0 | yeşil | 0.716 | 0.178 | 0.003 | 0.23 | -1.45 ±0.36 | 0.995 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–59 | 75 | %8 | %7 | yeşil | 0.582 | 0.353 | -0.073 | 0.40 | -0.88 ±0.13 | 0.011 |
| 2) 59–89 | 75 | %13 | %5 | yeşil | 0.441 | 0.187 | 0.028 | 0.40 | -1.01 ±0.16 | 0.346 |
| 3) 89–120 | 76 | %4 | %7 | yeşil | 0.065 | 0.351 | -0.079 | 0.36 | -0.96 ±0.14 | 0.483 |
| 4) saklı (geliştirme aralığı dışı) | 14 | %0 | %7 | yeşil | 0.273 | 1.000 | -0.082 | 0.21 | -1.00 ±0.19 | 0.437 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 76 | %8 | %5 | yeşil | 0.579 | 0.186 | -0.028 | 0.36 | -1.14 ±0.18 | 0.136 |
| 2) 0.030–0.032 | 75 | %9 | %5 | yeşil | 0.855 | 0.187 | -0.081 | 0.39 | -1.02 ±0.14 | 0.584 |
| 3) 0.032–0.034 | 76 | %4 | %8 | yeşil | 0.065 | 0.579 | -0.052 | 0.35 | -0.73 ±0.11 | 0.058 |
| 4) saklı (geliştirme aralığı dışı) | 13 | %23 | %8 | sarı | 0.388 | 1.000 | 0.131 | 0.52 | -0.77 ±0.22 | 0.131 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0–56 | 80 | %10 | %12 | yeşil | 1.000 | 0.577 | -0.052 | 0.36 | -0.37 ±0.06 | 0.381 |
| 2) 56–85 | 80 | %9 | %4 | yeşil | 0.722 | 0.048 | -0.019 | 0.33 | -0.65 ±0.07 | 0.114 |
| 3) 85–174 | 80 | %5 | %2 | yeşil | 0.142 | 0.016 | -0.059 | 0.43 | -1.84 ±0.18 | 0.054 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 77 | %6 | %8 | yeşil | 0.350 | 0.578 | -0.119 | 0.51 | -1.21 ±0.19 | 0.314 |
| 2) 14–39 | 82 | %5 | %2 | yeşil | 0.110 | 0.012 | -0.063 | 0.33 | -0.89 ±0.12 | 0.026 |
| 3) 39–119 | 81 | %12 | %9 | yeşil | 0.578 | 0.721 | 0.048 | 0.29 | -0.78 ±0.08 | 0.235 |


### saklı_rejim

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| cheque_bounce | 13 | %23 | %8 | sarı | 0.388 | 1.000 | 0.131 | 0.52 | -0.77 ±0.22 | 0.131 |
| cheque_share | 18 | %6 | %0 | yeşil | 0.716 | 0.178 | 0.003 | 0.23 | -1.45 ±0.36 | 0.995 |
| cheque_term | 14 | %0 | %7 | yeşil | 0.273 | 1.000 | -0.082 | 0.21 | -1.00 ±0.19 | 0.437 |
| geliştirme aralığı içi | 120 | %6 | %5 | yeşil | 0.131 | 0.054 | -0.052 | 0.35 | -1.03 ±0.13 | 0.093 |
| history | 11 | %0 | %27 | yeşil | 0.403 | 0.090 | -0.318 | 0.62 | -0.61 ±0.25 | 0.852 |
| inflation | 13 | %8 | %0 | yeşil | 1.000 | 0.288 | -0.077 | 0.31 | -0.66 ±0.20 | 0.517 |
| season_amp | 12 | %8 | %8 | yeşil | 1.000 | 1.000 | -0.118 | 0.42 | -0.62 ±0.24 | 0.064 |
| shock | 17 | %12 | %6 | yeşil | 1.000 | 0.720 | -0.006 | 0.42 | -0.81 ±0.25 | 0.365 |
| size_sigma | 11 | %0 | %9 | yeşil | 0.403 | 1.000 | -0.171 | 0.49 | -0.86 ±0.32 | 0.827 |
| trend | 11 | %36 | %9 | sarı | 0.019 | 1.000 | 0.283 | 0.50 | -0.86 ±0.26 | 0.965 |


