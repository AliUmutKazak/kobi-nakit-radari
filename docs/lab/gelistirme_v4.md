## Senaryo laboratuvarı: gelistirme kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 67 gün, ulaşılan 68 gün; senaryoların %83'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %9.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 16 / 49 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- inflation = 2) 0.17–0.33 (n=80): Kupiec alt q=0.012
- dso = 3) 87–181 (n=80): Kupiec alt q=0.012

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %5 | %12 | yeşil | 0.006 | 0.236 | -0.169 | 0.47 | -1.25 ±0.10 | 0.399 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %8 | %15 | yeşil | 0.620 | 0.170 | -0.127 | 0.43 | -1.00 ±0.11 | 0.905 |
| mikro | 84 | %4 | %8 | yeşil | 0.035 | 0.719 | -0.263 | 0.62 | -1.77 ±0.23 | 0.455 |
| orta | 60 | %2 | %15 | yeşil | 0.019 | 0.279 | -0.102 | 0.31 | -0.93 ±0.11 | 0.344 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %5 | %16 | yeşil | 0.142 | 0.089 | -0.187 | 0.48 | -1.09 ±0.17 | 0.818 |
| 2) 0.10–0.20 | 80 | %5 | %8 | yeşil | 0.142 | 0.474 | -0.161 | 0.44 | -1.44 ±0.19 | 0.102 |
| 3) 0.20–0.30 | 80 | %5 | %14 | yeşil | 0.142 | 0.350 | -0.158 | 0.48 | -1.23 ±0.15 | 0.704 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 80 | %6 | %8 | yeşil | 0.277 | 0.474 | -0.007 | 0.35 | -1.55 ±0.19 | 0.081 |
| 2) 0.17–0.33 | 80 | %0 | %16 | yeşil | 0.000 | 0.089 | -0.351 | 0.55 | -1.13 ±0.18 | 0.892 |
| 3) 0.33–0.50 | 80 | %9 | %14 | yeşil | 0.722 | 0.350 | -0.148 | 0.50 | -1.08 ±0.14 | 0.665 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.83 | 80 | %6 | %10 | yeşil | 0.277 | 1.000 | -0.093 | 0.42 | -1.17 ±0.15 | 0.364 |
| 2) 0.83–1.07 | 80 | %6 | %11 | yeşil | 0.277 | 0.853 | -0.111 | 0.41 | -1.41 ±0.18 | 0.402 |
| 3) 1.07–1.30 | 80 | %2 | %16 | yeşil | 0.016 | 0.089 | -0.302 | 0.56 | -1.18 ±0.18 | 0.788 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 74 | %5 | %9 | yeşil | 0.189 | 1.000 | -0.091 | 0.44 | -1.39 ±0.18 | 0.696 |
| 2) 22–29 | 80 | %8 | %12 | yeşil | 0.474 | 0.577 | -0.203 | 0.53 | -1.12 ±0.16 | 0.420 |
| 3) 29–36 | 86 | %2 | %15 | yeşil | 0.008 | 0.146 | -0.203 | 0.43 | -1.26 ±0.17 | 0.791 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.40 | 80 | %4 | %12 | yeşil | 0.048 | 0.577 | -0.176 | 0.42 | -1.29 ±0.17 | 0.440 |
| 2) 0.40–0.80 | 80 | %4 | %15 | yeşil | 0.048 | 0.188 | -0.158 | 0.48 | -1.01 ±0.14 | 0.813 |
| 3) 0.80–1.20 | 80 | %8 | %10 | yeşil | 0.474 | 1.000 | -0.172 | 0.50 | -1.45 ±0.19 | 0.351 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %4 | %16 | yeşil | 0.048 | 0.089 | -0.292 | 0.52 | -1.12 ±0.16 | 0.444 |
| 2) 0.10–0.20 | 80 | %6 | %10 | yeşil | 0.277 | 1.000 | -0.096 | 0.43 | -1.59 ±0.18 | 0.564 |
| 3) 0.20–0.30 | 80 | %5 | %11 | yeşil | 0.142 | 0.853 | -0.118 | 0.44 | -1.05 ±0.17 | 0.909 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 80 | %5 | %12 | yeşil | 0.142 | 0.577 | -0.178 | 0.54 | -0.99 ±0.13 | 0.855 |
| 2) 0.20–0.40 | 80 | %5 | %16 | yeşil | 0.142 | 0.089 | -0.186 | 0.44 | -1.29 ±0.19 | 0.603 |
| 3) 0.40–0.60 | 80 | %5 | %9 | yeşil | 0.142 | 0.722 | -0.142 | 0.43 | -1.47 ±0.19 | 0.253 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–60 | 80 | %4 | %16 | yeşil | 0.048 | 0.089 | -0.167 | 0.47 | -0.90 ±0.15 | 0.456 |
| 2) 60–90 | 80 | %6 | %10 | yeşil | 0.277 | 1.000 | -0.145 | 0.51 | -1.40 ±0.17 | 0.562 |
| 3) 90–120 | 80 | %5 | %11 | yeşil | 0.142 | 0.853 | -0.193 | 0.42 | -1.45 ±0.19 | 0.889 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 80 | %2 | %15 | yeşil | 0.016 | 0.188 | -0.300 | 0.50 | -1.04 ±0.15 | 0.389 |
| 2) 0.030–0.032 | 80 | %8 | %11 | yeşil | 0.474 | 0.853 | -0.089 | 0.47 | -1.46 ±0.19 | 0.965 |
| 3) 0.032–0.034 | 80 | %5 | %11 | yeşil | 0.142 | 0.853 | -0.117 | 0.43 | -1.26 ±0.17 | 0.526 |


### record_lag (VUK m.219: kayıt en geç 10 gün, fişe dayanan kayıtta 45 gün; aralık varsayım)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0–5 | 77 | %5 | %9 | yeşil | 0.147 | 0.854 | -0.098 | 0.45 | -0.91 ±0.13 | 0.803 |
| 2) 5–9 | 69 | %6 | %17 | yeşil | 0.248 | 0.066 | -0.234 | 0.47 | -1.31 ±0.20 | 0.512 |
| 3) 9–14 | 94 | %4 | %12 | yeşil | 0.060 | 0.604 | -0.178 | 0.48 | -1.49 ±0.18 | 0.576 |


### partial_share (varsayım: faturalarını iki taksitte kapatan müşteri payı)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.13 | 80 | %4 | %14 | yeşil | 0.048 | 0.350 | -0.200 | 0.47 | -1.58 ±0.21 | 0.519 |
| 2) 0.13–0.27 | 80 | %4 | %15 | yeşil | 0.048 | 0.188 | -0.164 | 0.58 | -1.05 ±0.15 | 0.140 |
| 3) 0.27–0.40 | 80 | %8 | %9 | yeşil | 0.474 | 0.722 | -0.141 | 0.35 | -1.13 ±0.14 | 0.481 |


### missing_due (veri kalitesi: vadesi girilmemiş fatura payı (TTK m.1530/4-a: 30 gün))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %5 | %11 | yeşil | 0.142 | 0.853 | -0.149 | 0.44 | -1.28 ±0.17 | 0.308 |
| 2) 0.10–0.20 | 80 | %4 | %20 | yeşil | 0.048 | 0.007 | -0.308 | 0.57 | -1.23 ±0.19 | 0.571 |
| 3) 0.20–0.30 | 80 | %6 | %6 | yeşil | 0.277 | 0.277 | -0.049 | 0.39 | -1.25 ±0.16 | 0.306 |


### ayin_gunu

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 1–11 | 79 | %5 | %16 | yeşil | 0.143 | 0.087 | -0.165 | 0.46 | -1.30 ±0.17 | 0.200 |
| 2) 11–21 | 78 | %4 | %9 | yeşil | 0.063 | 0.853 | -0.144 | 0.43 | -1.28 ±0.19 | 0.912 |
| 3) 21–31 | 83 | %6 | %12 | yeşil | 0.220 | 0.581 | -0.196 | 0.51 | -1.18 ±0.16 | 0.935 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 11–52 | 80 | %8 | %19 | yeşil | 0.474 | 0.023 | -0.214 | 0.56 | -0.44 ±0.08 | 0.175 |
| 2) 52–87 | 80 | %8 | %14 | yeşil | 0.474 | 0.350 | -0.152 | 0.43 | -0.83 ±0.11 | 0.722 |
| 3) 87–181 | 80 | %0 | %5 | yeşil | 0.000 | 0.142 | -0.139 | 0.40 | -2.49 ±0.20 | 0.017 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 75 | %4 | %9 | yeşil | 0.066 | 0.855 | -0.289 | 0.65 | -1.75 ±0.25 | 0.646 |
| 2) 14–39 | 81 | %9 | %14 | yeşil | 0.721 | 0.352 | -0.134 | 0.47 | -1.10 ±0.15 | 0.979 |
| 3) 39–119 | 84 | %2 | %14 | yeşil | 0.011 | 0.275 | -0.094 | 0.30 | -0.96 ±0.09 | 0.331 |


