## Senaryo laboratuvarı: sinav kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 68 gün, ulaşılan 67 gün; senaryoların %80'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %10.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 10 / 74 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- Yok.

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %5 | %14 | yeşil | 0.006 | 0.052 | -0.278 | 0.55 | -1.12 ±0.10 | 0.550 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %6 | %14 | yeşil | 0.240 | 0.305 | -0.146 | 0.44 | -0.91 ±0.12 | 0.393 |
| mikro | 84 | %4 | %18 | yeşil | 0.035 | 0.045 | -0.551 | 0.84 | -1.39 ±0.24 | 0.352 |
| orta | 60 | %5 | %10 | yeşil | 0.210 | 1.000 | -0.109 | 0.32 | -1.07 ±0.13 | 0.315 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 74 | %3 | %14 | yeşil | 0.023 | 0.441 | -0.213 | 0.42 | -1.05 ±0.15 | 0.283 |
| 2) 0.10–0.20 | 74 | %7 | %16 | yeşil | 0.356 | 0.117 | -0.327 | 0.61 | -1.19 ±0.23 | 0.546 |
| 3) 0.20–0.30 | 74 | %4 | %15 | yeşil | 0.085 | 0.244 | -0.353 | 0.67 | -1.10 ±0.17 | 0.721 |
| 4) saklı (geliştirme aralığı dışı) | 18 | %11 | %6 | yeşil | 1.000 | 0.716 | -0.038 | 0.35 | -1.21 ±0.25 | 0.615 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.16 | 77 | %5 | %14 | yeşil | 0.147 | 0.250 | -0.153 | 0.49 | -1.42 ±0.19 | 0.327 |
| 2) 0.16–0.33 | 76 | %5 | %12 | yeşil | 0.186 | 0.702 | -0.381 | 0.63 | -0.88 ±0.17 | 0.442 |
| 3) 0.33–0.50 | 77 | %5 | %16 | yeşil | 0.147 | 0.186 | -0.301 | 0.55 | -1.08 ±0.18 | 0.727 |
| 4) saklı (geliştirme aralığı dışı) | 10 | %0 | %20 | yeşil | 0.419 | 0.613 | -0.286 | 0.40 | -0.98 ±0.39 | 0.337 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.84 | 78 | %1 | %10 | yeşil | 0.003 | 1.000 | -0.236 | 0.43 | -1.22 ±0.17 | 0.106 |
| 2) 0.84–1.07 | 77 | %8 | %16 | yeşil | 0.578 | 0.186 | -0.234 | 0.55 | -1.20 ±0.17 | 0.172 |
| 3) 1.07–1.30 | 78 | %6 | %14 | yeşil | 0.349 | 0.253 | -0.287 | 0.61 | -0.98 ±0.19 | 0.298 |
| 4) saklı (geliştirme aralığı dışı) | 7 | %0 | %43 | yeşil | 0.628 | 0.026 | -1.128 | 1.27 | -0.54 ±0.76 | 0.459 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 74 | %5 | %9 | yeşil | 0.189 | 1.000 | -0.357 | 0.61 | -1.14 ±0.17 | 0.751 |
| 2) 22–29 | 79 | %4 | %16 | yeşil | 0.062 | 0.087 | -0.245 | 0.53 | -1.18 ±0.19 | 0.681 |
| 3) 29–36 | 81 | %6 | %17 | yeşil | 0.276 | 0.062 | -0.268 | 0.53 | -1.09 ±0.18 | 0.152 |
| 4) saklı (geliştirme aralığı dışı) | 6 | %0 | %0 | yeşil | 0.646 | 0.646 | 0.098 | 0.41 | -0.45 ±0.27 | 0.318 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.39 | 76 | %5 | %16 | yeşil | 0.186 | 0.121 | -0.346 | 0.59 | -0.92 ±0.16 | 0.765 |
| 2) 0.39–0.79 | 76 | %1 | %17 | yeşil | 0.004 | 0.085 | -0.357 | 0.55 | -1.04 ±0.19 | 0.357 |
| 3) 0.79–1.20 | 77 | %9 | %10 | yeşil | 0.854 | 1.000 | -0.149 | 0.54 | -1.39 ±0.17 | 0.575 |
| 4) saklı (geliştirme aralığı dışı) | 11 | %0 | %9 | yeşil | 0.403 | 1.000 | -0.174 | 0.36 | -1.18 ±0.71 | 0.706 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 75 | %3 | %12 | yeşil | 0.023 | 0.701 | -0.293 | 0.48 | -1.12 ±0.17 | 0.333 |
| 2) 0.10–0.20 | 74 | %7 | %11 | yeşil | 0.356 | 0.845 | -0.222 | 0.54 | -1.11 ±0.19 | 0.600 |
| 3) 0.20–0.30 | 75 | %4 | %16 | yeşil | 0.066 | 0.119 | -0.318 | 0.60 | -1.11 ±0.18 | 0.097 |
| 4) saklı (geliştirme aralığı dışı) | 16 | %12 | %31 | yeşil | 1.000 | 0.017 | -0.285 | 0.72 | -1.19 ±0.50 | 0.742 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 78 | %6 | %13 | yeşil | 0.349 | 0.447 | -0.438 | 0.71 | -0.73 ±0.15 | 0.103 |
| 2) 0.20–0.40 | 78 | %5 | %12 | yeşil | 0.145 | 0.704 | -0.163 | 0.48 | -1.51 ±0.22 | 0.394 |
| 3) 0.40–0.60 | 79 | %4 | %16 | yeşil | 0.062 | 0.087 | -0.230 | 0.47 | -1.11 ±0.15 | 0.788 |
| 4) saklı (geliştirme aralığı dışı) | 5 | %0 | %40 | yeşil | 0.672 | 0.081 | -0.352 | 0.38 | -1.19 ±0.48 | 0.993 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–60 | 78 | %4 | %10 | yeşil | 0.063 | 1.000 | -0.361 | 0.64 | -0.94 ±0.16 | 0.923 |
| 2) 60–90 | 78 | %4 | %13 | yeşil | 0.063 | 0.447 | -0.290 | 0.52 | -1.14 ±0.16 | 0.334 |
| 3) 90–120 | 79 | %8 | %20 | yeşil | 0.577 | 0.007 | -0.217 | 0.52 | -1.22 ±0.20 | 0.015 |
| 4) saklı (geliştirme aralığı dışı) | 5 | %0 | %0 | yeşil | 0.672 | 0.672 | 0.225 | 0.22 | -2.00 ±1.08 | 0.180 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 76 | %4 | %13 | yeşil | 0.065 | 0.443 | -0.303 | 0.52 | -1.00 ±0.17 | 0.633 |
| 2) 0.030–0.032 | 76 | %8 | %17 | yeşil | 0.579 | 0.085 | -0.342 | 0.67 | -1.25 ±0.20 | 0.592 |
| 3) 0.032–0.034 | 76 | %4 | %14 | yeşil | 0.065 | 0.247 | -0.243 | 0.49 | -1.05 ±0.18 | 0.372 |
| 4) saklı (geliştirme aralığı dışı) | 12 | %0 | %0 | yeşil | 0.308 | 0.308 | 0.058 | 0.32 | -1.51 ±0.45 | 0.777 |


### record_lag (VUK m.219: kayıt en geç 10 gün, fişe dayanan kayıtta 45 gün; aralık varsayım)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0–5 | 72 | %3 | %18 | yeşil | 0.032 | 0.046 | -0.405 | 0.60 | -1.04 ±0.19 | 0.924 |
| 2) 5–9 | 67 | %4 | %16 | yeşil | 0.120 | 0.155 | -0.264 | 0.55 | -1.00 ±0.17 | 0.353 |
| 3) 9–14 | 86 | %7 | %10 | yeşil | 0.380 | 1.000 | -0.184 | 0.52 | -1.13 ±0.17 | 0.127 |
| 4) saklı (geliştirme aralığı dışı) | 15 | %7 | %7 | yeşil | 0.733 | 0.733 | -0.271 | 0.51 | -2.00 ±0.45 | 0.468 |


### partial_share (varsayım: faturalarını iki taksitte kapatan müşteri payı)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.14 | 78 | %5 | %18 | yeşil | 0.145 | 0.034 | -0.342 | 0.56 | -0.95 ±0.19 | 0.901 |
| 2) 0.14–0.27 | 78 | %4 | %14 | yeşil | 0.063 | 0.253 | -0.321 | 0.58 | -1.18 ±0.18 | 0.581 |
| 3) 0.27–0.40 | 79 | %5 | %10 | yeşil | 0.143 | 1.000 | -0.173 | 0.52 | -1.16 ±0.16 | 0.712 |
| 4) saklı (geliştirme aralığı dışı) | 5 | %20 | %20 | yeşil | 1.000 | 1.000 | -0.268 | 0.49 | -2.02 ±0.60 | 0.989 |


### missing_due (veri kalitesi: vadesi girilmemiş fatura payı (TTK m.1530/4-a: 30 gün))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 77 | %5 | %10 | yeşil | 0.147 | 1.000 | -0.175 | 0.48 | -1.18 ±0.16 | 0.475 |
| 2) 0.10–0.20 | 76 | %5 | %18 | yeşil | 0.186 | 0.033 | -0.396 | 0.64 | -1.12 ±0.18 | 0.924 |
| 3) 0.20–0.30 | 77 | %5 | %12 | yeşil | 0.147 | 0.703 | -0.258 | 0.54 | -1.04 ±0.19 | 0.679 |
| 4) saklı (geliştirme aralığı dışı) | 10 | %0 | %30 | yeşil | 0.419 | 0.070 | -0.335 | 0.49 | -1.25 ±0.69 | 0.958 |


### ayin_gunu

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 1–10 | 73 | %3 | %18 | yeşil | 0.024 | 0.047 | -0.326 | 0.54 | -1.12 ±0.20 | 0.198 |
| 2) 10–20 | 77 | %8 | %12 | yeşil | 0.578 | 0.703 | -0.207 | 0.57 | -1.15 ±0.19 | 0.638 |
| 3) 20–31 | 90 | %4 | %13 | yeşil | 0.063 | 0.379 | -0.301 | 0.55 | -1.09 ±0.15 | 0.790 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–55 | 80 | %10 | %14 | yeşil | 1.000 | 0.350 | -0.282 | 0.65 | -0.35 ±0.10 | 0.903 |
| 2) 55–89 | 80 | %4 | %19 | yeşil | 0.048 | 0.023 | -0.322 | 0.50 | -0.84 ±0.15 | 0.609 |
| 3) 89–224 | 80 | %1 | %10 | yeşil | 0.003 | 1.000 | -0.230 | 0.51 | -2.16 ±0.20 | 0.692 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 74 | %4 | %19 | yeşil | 0.085 | 0.032 | -0.578 | 0.90 | -1.19 ±0.24 | 0.418 |
| 2) 14–38 | 84 | %5 | %13 | yeşil | 0.107 | 0.469 | -0.173 | 0.45 | -1.15 ±0.17 | 0.603 |
| 3) 38–120 | 82 | %6 | %11 | yeşil | 0.275 | 0.853 | -0.116 | 0.34 | -1.03 ±0.11 | 0.779 |


### saklı_rejim

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| cheque_bounce | 12 | %0 | %0 | yeşil | 0.308 | 0.308 | 0.058 | 0.32 | -1.51 ±0.45 | 0.777 |
| cheque_share | 5 | %0 | %40 | yeşil | 0.672 | 0.081 | -0.352 | 0.38 | -1.19 ±0.48 | 0.993 |
| cheque_term | 5 | %0 | %0 | yeşil | 0.672 | 0.672 | 0.225 | 0.22 | -2.00 ±1.08 | 0.180 |
| geliştirme aralığı içi | 120 | %5 | %12 | yeşil | 0.054 | 0.447 | -0.340 | 0.61 | -0.93 ±0.13 | 0.274 |
| history | 6 | %0 | %0 | yeşil | 0.646 | 0.646 | 0.098 | 0.41 | -0.45 ±0.27 | 0.318 |
| inflation | 10 | %0 | %20 | yeşil | 0.419 | 0.613 | -0.286 | 0.40 | -0.98 ±0.39 | 0.337 |
| missing_due | 10 | %0 | %30 | yeşil | 0.419 | 0.070 | -0.335 | 0.49 | -1.25 ±0.69 | 0.958 |
| partial_share | 5 | %20 | %20 | yeşil | 1.000 | 1.000 | -0.268 | 0.49 | -2.02 ±0.60 | 0.989 |
| record_lag | 15 | %7 | %7 | yeşil | 0.733 | 0.733 | -0.271 | 0.51 | -2.00 ±0.45 | 0.468 |
| season_amp | 18 | %11 | %6 | yeşil | 1.000 | 0.716 | -0.038 | 0.35 | -1.21 ±0.25 | 0.615 |
| shock | 16 | %12 | %31 | yeşil | 1.000 | 0.017 | -0.285 | 0.72 | -1.19 ±0.50 | 0.742 |
| size_sigma | 7 | %0 | %43 | yeşil | 0.628 | 0.026 | -1.128 | 1.27 | -0.54 ±0.76 | 0.459 |
| trend | 11 | %0 | %9 | yeşil | 0.403 | 1.000 | -0.174 | 0.36 | -1.18 ±0.71 | 0.706 |


