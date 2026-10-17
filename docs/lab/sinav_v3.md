## Senaryo laboratuvarı: sinav kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 74 gün, ulaşılan 73 gün; senaryoların %80'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %10.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 13 / 64 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- shock = 4) saklı (geliştirme aralığı dışı) (n=13): Basel sarı
- saklı_rejim = shock (n=13): Basel sarı

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %6 | %12 | yeşil | 0.025 | 0.451 | -0.148 | 0.46 | -1.42 ±0.11 | 0.900 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %4 | %9 | yeşil | 0.045 | 0.869 | -0.120 | 0.44 | -1.29 ±0.15 | 0.179 |
| mikro | 84 | %8 | %14 | yeşil | 0.719 | 0.275 | -0.216 | 0.59 | -1.84 ±0.25 | 0.078 |
| orta | 60 | %5 | %12 | yeşil | 0.210 | 0.831 | -0.098 | 0.31 | -1.03 ±0.10 | 0.556 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 76 | %4 | %9 | yeşil | 0.065 | 0.854 | -0.132 | 0.40 | -1.78 ±0.25 | 0.117 |
| 2) 0.10–0.20 | 75 | %5 | %11 | yeşil | 0.187 | 1.000 | -0.143 | 0.42 | -1.43 ±0.17 | 0.747 |
| 3) 0.20–0.30 | 76 | %9 | %14 | yeşil | 0.854 | 0.247 | -0.128 | 0.54 | -1.01 ±0.14 | 0.195 |
| 4) saklı (geliştirme aralığı dışı) | 13 | %0 | %15 | yeşil | 0.288 | 0.633 | -0.392 | 0.55 | -1.64 ±0.53 | 0.765 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 75 | %5 | %8 | yeşil | 0.187 | 0.582 | -0.088 | 0.41 | -1.77 ±0.25 | 0.068 |
| 2) 0.17–0.33 | 75 | %4 | %15 | yeşil | 0.066 | 0.245 | -0.195 | 0.41 | -1.11 ±0.17 | 0.503 |
| 3) 0.33–0.50 | 76 | %8 | %13 | yeşil | 0.579 | 0.443 | -0.120 | 0.53 | -1.30 ±0.16 | 0.100 |
| 4) saklı (geliştirme aralığı dışı) | 14 | %7 | %7 | yeşil | 1.000 | 1.000 | -0.370 | 0.61 | -1.82 ±0.42 | 0.186 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.84 | 76 | %7 | %9 | yeşil | 0.351 | 0.854 | -0.213 | 0.46 | -1.39 ±0.19 | 0.971 |
| 2) 0.84–1.06 | 75 | %8 | %12 | yeşil | 0.582 | 0.701 | -0.092 | 0.50 | -1.60 ±0.23 | 0.946 |
| 3) 1.06–1.30 | 76 | %4 | %14 | yeşil | 0.065 | 0.247 | -0.133 | 0.42 | -1.27 ±0.18 | 0.279 |
| 4) saklı (geliştirme aralığı dışı) | 13 | %0 | %8 | yeşil | 0.288 | 1.000 | -0.176 | 0.40 | -1.39 ±0.28 | 0.034 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 70 | %3 | %11 | yeşil | 0.033 | 0.843 | -0.188 | 0.43 | -1.29 ±0.19 | 0.675 |
| 2) 22–29 | 79 | %5 | %13 | yeşil | 0.143 | 0.450 | -0.147 | 0.45 | -1.53 ±0.20 | 0.626 |
| 3) 29–36 | 81 | %10 | %10 | yeşil | 1.000 | 1.000 | -0.081 | 0.49 | -1.52 ±0.19 | 0.467 |
| 4) saklı (geliştirme aralığı dışı) | 10 | %0 | %20 | yeşil | 0.419 | 0.613 | -0.419 | 0.50 | -0.55 ±0.33 | 0.190 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.40 | 77 | %3 | %12 | yeşil | 0.017 | 0.703 | -0.227 | 0.44 | -1.54 ±0.19 | 0.529 |
| 2) 0.40–0.80 | 77 | %9 | %10 | yeşil | 0.854 | 1.000 | -0.042 | 0.49 | -1.42 ±0.19 | 0.573 |
| 3) 0.80–1.20 | 78 | %6 | %14 | yeşil | 0.349 | 0.253 | -0.192 | 0.46 | -1.18 ±0.19 | 0.337 |
| 4) saklı (geliştirme aralığı dışı) | 8 | %0 | %0 | yeşil | 0.469 | 0.469 | 0.026 | 0.31 | -2.55 ±0.70 | 0.301 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 76 | %3 | %13 | yeşil | 0.023 | 0.443 | -0.183 | 0.45 | -1.22 ±0.18 | 0.781 |
| 2) 0.10–0.20 | 75 | %7 | %12 | yeşil | 0.353 | 0.701 | -0.159 | 0.47 | -1.75 ±0.24 | 0.410 |
| 3) 0.20–0.30 | 76 | %4 | %11 | yeşil | 0.065 | 1.000 | -0.128 | 0.41 | -1.30 ±0.17 | 0.112 |
| 4) saklı (geliştirme aralığı dışı) | 13 | %31 | %8 | sarı | 0.034 | 1.000 | 0.006 | 0.72 | -1.30 ±0.38 | 0.052 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.19 | 74 | %7 | %14 | yeşil | 0.356 | 0.441 | -0.083 | 0.55 | -1.15 ±0.17 | 0.131 |
| 2) 0.19–0.39 | 74 | %7 | %9 | yeşil | 0.356 | 1.000 | -0.140 | 0.40 | -1.31 ±0.15 | 0.510 |
| 3) 0.39–0.60 | 74 | %1 | %14 | yeşil | 0.005 | 0.441 | -0.282 | 0.46 | -1.65 ±0.25 | 0.339 |
| 4) saklı (geliştirme aralığı dışı) | 18 | %17 | %6 | yeşil | 0.416 | 0.716 | 0.102 | 0.35 | -2.00 ±0.50 | 0.680 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–59 | 76 | %4 | %12 | yeşil | 0.065 | 0.702 | -0.119 | 0.47 | -1.33 ±0.15 | 0.647 |
| 2) 59–90 | 75 | %7 | %13 | yeşil | 0.353 | 0.441 | -0.228 | 0.49 | -1.25 ±0.19 | 0.633 |
| 3) 90–120 | 76 | %8 | %9 | yeşil | 0.579 | 0.854 | -0.090 | 0.44 | -1.75 ±0.25 | 0.812 |
| 4) saklı (geliştirme aralığı dışı) | 13 | %0 | %15 | yeşil | 0.288 | 0.633 | -0.197 | 0.35 | -0.95 ±0.23 | 0.297 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 78 | %5 | %9 | yeşil | 0.145 | 0.853 | -0.079 | 0.41 | -1.46 ±0.19 | 0.501 |
| 2) 0.030–0.032 | 78 | %3 | %12 | yeşil | 0.017 | 0.704 | -0.180 | 0.43 | -1.56 ±0.20 | 0.590 |
| 3) 0.032–0.034 | 78 | %9 | %14 | yeşil | 0.853 | 0.253 | -0.194 | 0.51 | -1.27 ±0.19 | 0.885 |
| 4) saklı (geliştirme aralığı dışı) | 6 | %17 | %17 | yeşil | 1.000 | 1.000 | -0.032 | 0.79 | -0.87 ±0.80 | 0.390 |


### record_lag (varsayım: tahsilatların deftere işlenme gecikmesi, gün (muhasebe))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0–5 | 75 | %3 | %15 | yeşil | 0.023 | 0.245 | -0.268 | 0.47 | -1.13 ±0.18 | 0.777 |
| 2) 5–9 | 66 | %8 | %12 | yeşil | 0.554 | 0.681 | -0.104 | 0.49 | -1.43 ±0.20 | 0.259 |
| 3) 9–14 | 87 | %7 | %9 | yeşil | 0.379 | 0.862 | -0.067 | 0.41 | -1.65 ±0.20 | 0.390 |
| 4) saklı (geliştirme aralığı dışı) | 12 | %8 | %8 | yeşil | 1.000 | 1.000 | -0.223 | 0.59 | -1.39 ±0.39 | 0.874 |


### ayin_gunu

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 1–11 | 78 | %4 | %17 | yeşil | 0.063 | 0.086 | -0.253 | 0.50 | -1.51 ±0.22 | 0.293 |
| 2) 11–21 | 81 | %9 | %10 | yeşil | 0.721 | 1.000 | -0.109 | 0.43 | -1.17 ±0.15 | 0.858 |
| 3) 21–31 | 81 | %5 | %9 | yeşil | 0.141 | 0.721 | -0.086 | 0.45 | -1.58 ±0.20 | 0.523 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 17–62 | 80 | %6 | %14 | yeşil | 0.277 | 0.350 | -0.165 | 0.46 | -0.63 ±0.10 | 0.406 |
| 2) 62–95 | 80 | %10 | %9 | yeşil | 1.000 | 0.722 | -0.017 | 0.36 | -0.93 ±0.08 | 0.867 |
| 3) 95–181 | 80 | %1 | %12 | yeşil | 0.003 | 0.577 | -0.262 | 0.56 | -2.70 ±0.25 | 0.659 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 74 | %9 | %16 | yeşil | 1.000 | 0.117 | -0.196 | 0.61 | -1.73 ±0.27 | 0.108 |
| 2) 14–38 | 84 | %5 | %10 | yeşil | 0.107 | 1.000 | -0.171 | 0.49 | -1.37 ±0.18 | 0.652 |
| 3) 38–119 | 82 | %4 | %10 | yeşil | 0.046 | 1.000 | -0.081 | 0.30 | -1.19 ±0.10 | 0.197 |


### saklı_rejim

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| cheque_bounce | 6 | %17 | %17 | yeşil | 1.000 | 1.000 | -0.032 | 0.79 | -0.87 ±0.80 | 0.390 |
| cheque_share | 18 | %17 | %6 | yeşil | 0.416 | 0.716 | 0.102 | 0.35 | -2.00 ±0.50 | 0.680 |
| cheque_term | 13 | %0 | %15 | yeşil | 0.288 | 0.633 | -0.197 | 0.35 | -0.95 ±0.23 | 0.297 |
| geliştirme aralığı içi | 120 | %3 | %13 | yeşil | 0.007 | 0.285 | -0.129 | 0.41 | -1.35 ±0.17 | 0.202 |
| history | 10 | %0 | %20 | yeşil | 0.419 | 0.613 | -0.419 | 0.50 | -0.55 ±0.33 | 0.190 |
| inflation | 14 | %7 | %7 | yeşil | 1.000 | 1.000 | -0.370 | 0.61 | -1.82 ±0.42 | 0.186 |
| record_lag | 12 | %8 | %8 | yeşil | 1.000 | 1.000 | -0.223 | 0.59 | -1.39 ±0.39 | 0.874 |
| season_amp | 13 | %0 | %15 | yeşil | 0.288 | 0.633 | -0.392 | 0.55 | -1.64 ±0.53 | 0.765 |
| shock | 13 | %31 | %8 | sarı | 0.034 | 1.000 | 0.006 | 0.72 | -1.30 ±0.38 | 0.052 |
| size_sigma | 13 | %0 | %8 | yeşil | 0.288 | 1.000 | -0.176 | 0.40 | -1.39 ±0.28 | 0.034 |
| trend | 8 | %0 | %0 | yeşil | 0.469 | 0.469 | 0.026 | 0.31 | -2.55 ±0.70 | 0.301 |


