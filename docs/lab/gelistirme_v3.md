## Senaryo laboratuvarı: gelistirme kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 66 gün, ulaşılan 69 gün; senaryoların %75'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %11.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 8 / 43 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- Yok.

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %6 | %10 | yeşil | 0.025 | 1.000 | -0.121 | 0.43 | -1.44 ±0.11 | 0.571 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %5 | %11 | yeşil | 0.127 | 0.734 | -0.140 | 0.42 | -1.24 ±0.15 | 0.140 |
| mikro | 84 | %8 | %7 | yeşil | 0.719 | 0.385 | -0.105 | 0.51 | -2.15 ±0.23 | 0.346 |
| orta | 60 | %3 | %12 | yeşil | 0.068 | 0.831 | -0.111 | 0.33 | -0.75 ±0.11 | 0.061 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %5 | %5 | yeşil | 0.142 | 0.142 | 0.013 | 0.39 | -1.82 ±0.19 | 0.486 |
| 2) 0.10–0.20 | 80 | %5 | %10 | yeşil | 0.142 | 1.000 | -0.193 | 0.44 | -0.96 ±0.16 | 0.606 |
| 3) 0.20–0.30 | 80 | %8 | %15 | yeşil | 0.474 | 0.188 | -0.181 | 0.46 | -1.53 ±0.21 | 0.245 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 80 | %6 | %8 | yeşil | 0.277 | 0.474 | -0.050 | 0.38 | -1.78 ±0.20 | 0.897 |
| 2) 0.17–0.33 | 80 | %6 | %9 | yeşil | 0.277 | 0.722 | -0.133 | 0.46 | -1.34 ±0.17 | 0.789 |
| 3) 0.33–0.50 | 80 | %5 | %14 | yeşil | 0.142 | 0.350 | -0.179 | 0.46 | -1.20 ±0.19 | 0.560 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.83 | 80 | %8 | %8 | yeşil | 0.474 | 0.474 | -0.080 | 0.42 | -1.59 ±0.18 | 0.917 |
| 2) 0.83–1.07 | 80 | %6 | %12 | yeşil | 0.277 | 0.577 | -0.118 | 0.44 | -1.26 ±0.18 | 0.893 |
| 3) 1.07–1.30 | 80 | %4 | %10 | yeşil | 0.048 | 1.000 | -0.164 | 0.44 | -1.47 ±0.20 | 0.220 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 74 | %4 | %14 | yeşil | 0.085 | 0.441 | -0.241 | 0.49 | -0.98 ±0.17 | 0.209 |
| 2) 22–29 | 81 | %6 | %9 | yeşil | 0.276 | 0.721 | -0.096 | 0.41 | -1.52 ±0.20 | 0.774 |
| 3) 29–36 | 85 | %7 | %8 | yeşil | 0.382 | 0.603 | -0.039 | 0.41 | -1.76 ±0.18 | 0.970 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.40 | 80 | %4 | %18 | yeşil | 0.048 | 0.062 | -0.191 | 0.47 | -1.34 ±0.18 | 0.933 |
| 2) 0.40–0.80 | 80 | %8 | %6 | yeşil | 0.474 | 0.277 | -0.092 | 0.43 | -1.45 ±0.19 | 0.389 |
| 3) 0.80–1.20 | 80 | %6 | %6 | yeşil | 0.277 | 0.277 | -0.079 | 0.40 | -1.52 ±0.20 | 0.853 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %10 | %11 | yeşil | 1.000 | 0.853 | -0.133 | 0.43 | -1.30 ±0.16 | 0.900 |
| 2) 0.10–0.20 | 80 | %2 | %11 | yeşil | 0.016 | 0.853 | -0.173 | 0.47 | -1.54 ±0.22 | 0.727 |
| 3) 0.20–0.30 | 80 | %5 | %8 | yeşil | 0.142 | 0.474 | -0.056 | 0.40 | -1.48 ±0.18 | 0.442 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 80 | %8 | %11 | yeşil | 0.474 | 0.853 | -0.207 | 0.50 | -1.47 ±0.22 | 0.261 |
| 2) 0.20–0.40 | 80 | %4 | %12 | yeşil | 0.048 | 0.577 | -0.124 | 0.45 | -1.37 ±0.16 | 0.720 |
| 3) 0.40–0.60 | 80 | %6 | %6 | yeşil | 0.277 | 0.277 | -0.030 | 0.34 | -1.46 ±0.19 | 0.629 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–60 | 80 | %6 | %9 | yeşil | 0.277 | 0.722 | -0.058 | 0.43 | -1.40 ±0.18 | 0.658 |
| 2) 60–90 | 80 | %5 | %6 | yeşil | 0.142 | 0.277 | -0.155 | 0.43 | -1.48 ±0.19 | 0.312 |
| 3) 90–120 | 80 | %6 | %15 | yeşil | 0.277 | 0.188 | -0.149 | 0.43 | -1.44 ±0.19 | 0.118 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 80 | %1 | %18 | yeşil | 0.003 | 0.062 | -0.178 | 0.45 | -1.34 ±0.18 | 0.557 |
| 2) 0.030–0.032 | 80 | %8 | %6 | yeşil | 0.474 | 0.277 | -0.050 | 0.38 | -1.68 ±0.21 | 0.478 |
| 3) 0.032–0.034 | 80 | %9 | %6 | yeşil | 0.722 | 0.277 | -0.133 | 0.47 | -1.30 ±0.17 | 0.395 |


### record_lag (varsayım: tahsilatların deftere işlenme gecikmesi, gün (muhasebe))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0–5 | 77 | %8 | %8 | yeşil | 0.578 | 0.578 | -0.009 | 0.42 | -1.43 ±0.18 | 0.920 |
| 2) 5–9 | 69 | %4 | %14 | yeşil | 0.116 | 0.316 | -0.244 | 0.50 | -1.05 ±0.19 | 0.260 |
| 3) 9–14 | 94 | %5 | %9 | yeşil | 0.129 | 0.733 | -0.121 | 0.39 | -1.73 ±0.19 | 0.890 |


### ayin_gunu

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 1–10 | 72 | %7 | %4 | yeşil | 0.442 | 0.087 | -0.028 | 0.37 | -1.69 ±0.22 | 0.674 |
| 2) 10–21 | 87 | %7 | %10 | yeşil | 0.379 | 1.000 | -0.107 | 0.44 | -1.26 ±0.16 | 0.930 |
| 3) 21–31 | 81 | %4 | %15 | yeşil | 0.047 | 0.190 | -0.218 | 0.48 | -1.40 ±0.20 | 0.205 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 6–53 | 80 | %6 | %14 | yeşil | 0.277 | 0.350 | -0.209 | 0.50 | -0.38 ±0.09 | 0.020 |
| 2) 53–90 | 80 | %6 | %9 | yeşil | 0.277 | 0.722 | -0.041 | 0.35 | -0.98 ±0.10 | 0.979 |
| 3) 90–186 | 80 | %5 | %8 | yeşil | 0.142 | 0.474 | -0.112 | 0.44 | -2.95 ±0.21 | 0.217 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 74 | %8 | %8 | yeşil | 0.701 | 0.701 | -0.124 | 0.53 | -2.12 ±0.24 | 0.379 |
| 2) 14–37 | 86 | %7 | %13 | yeşil | 0.380 | 0.471 | -0.154 | 0.46 | -1.32 ±0.18 | 0.085 |
| 3) 37–120 | 80 | %2 | %9 | yeşil | 0.016 | 0.722 | -0.081 | 0.31 | -0.93 ±0.11 | 0.098 |


