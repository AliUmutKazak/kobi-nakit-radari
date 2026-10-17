## Senaryo laboratuvarı: gelistirme kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 66 gün, ulaşılan 69 gün; senaryoların %75'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %11.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 5 / 43 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- Yok.

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %6 | %7 | yeşil | 0.043 | 0.086 | -0.057 | 0.43 | -1.40 ±0.11 | 0.739 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %5 | %5 | yeşil | 0.127 | 0.127 | -0.052 | 0.41 | -1.21 ±0.14 | 0.789 |
| mikro | 84 | %6 | %5 | yeşil | 0.218 | 0.107 | -0.073 | 0.53 | -2.11 ±0.23 | 0.552 |
| orta | 60 | %8 | %12 | yeşil | 0.686 | 0.831 | -0.045 | 0.34 | -0.69 ±0.11 | 0.078 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %8 | %2 | yeşil | 0.474 | 0.016 | 0.078 | 0.41 | -1.76 ±0.19 | 0.186 |
| 2) 0.10–0.20 | 80 | %4 | %8 | yeşil | 0.048 | 0.474 | -0.132 | 0.45 | -0.92 ±0.15 | 0.730 |
| 3) 0.20–0.30 | 80 | %8 | %10 | yeşil | 0.474 | 1.000 | -0.118 | 0.44 | -1.51 ±0.21 | 0.274 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 80 | %6 | %4 | yeşil | 0.277 | 0.048 | 0.030 | 0.40 | -1.75 ±0.20 | 0.622 |
| 2) 0.17–0.33 | 80 | %5 | %5 | yeşil | 0.142 | 0.142 | -0.049 | 0.45 | -1.31 ±0.17 | 0.376 |
| 3) 0.33–0.50 | 80 | %8 | %11 | yeşil | 0.474 | 0.853 | -0.153 | 0.45 | -1.13 ±0.19 | 0.425 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.83 | 80 | %6 | %6 | yeşil | 0.277 | 0.277 | -0.005 | 0.40 | -1.56 ±0.18 | 0.187 |
| 2) 0.83–1.07 | 80 | %4 | %8 | yeşil | 0.048 | 0.474 | -0.065 | 0.44 | -1.22 ±0.18 | 0.318 |
| 3) 1.07–1.30 | 80 | %9 | %6 | yeşil | 0.722 | 0.277 | -0.102 | 0.46 | -1.41 ±0.20 | 0.078 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 74 | %7 | %9 | yeşil | 0.356 | 1.000 | -0.174 | 0.49 | -0.94 ±0.17 | 0.450 |
| 2) 22–29 | 81 | %6 | %5 | yeşil | 0.276 | 0.141 | -0.013 | 0.42 | -1.47 ±0.20 | 0.322 |
| 3) 29–36 | 85 | %6 | %6 | yeşil | 0.216 | 0.216 | 0.001 | 0.40 | -1.72 ±0.18 | 0.750 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.40 | 80 | %8 | %9 | yeşil | 0.474 | 0.722 | -0.126 | 0.47 | -1.31 ±0.18 | 0.802 |
| 2) 0.40–0.80 | 80 | %5 | %6 | yeşil | 0.142 | 0.277 | -0.030 | 0.42 | -1.41 ±0.19 | 0.748 |
| 3) 0.80–1.20 | 80 | %6 | %5 | yeşil | 0.277 | 0.142 | -0.016 | 0.41 | -1.47 ±0.20 | 0.619 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %9 | %10 | yeşil | 0.722 | 1.000 | -0.078 | 0.42 | -1.27 ±0.16 | 0.501 |
| 2) 0.10–0.20 | 80 | %5 | %6 | yeşil | 0.142 | 0.277 | -0.097 | 0.49 | -1.48 ±0.21 | 0.672 |
| 3) 0.20–0.30 | 80 | %5 | %4 | yeşil | 0.142 | 0.048 | 0.003 | 0.38 | -1.44 ±0.18 | 0.596 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 80 | %9 | %8 | yeşil | 0.722 | 0.474 | -0.104 | 0.48 | -1.46 ±0.21 | 0.936 |
| 2) 0.20–0.40 | 80 | %4 | %8 | yeşil | 0.048 | 0.474 | -0.058 | 0.46 | -1.32 ±0.16 | 0.997 |
| 3) 0.40–0.60 | 80 | %6 | %5 | yeşil | 0.277 | 0.142 | -0.010 | 0.36 | -1.41 ±0.19 | 0.521 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–60 | 80 | %6 | %8 | yeşil | 0.277 | 0.474 | -0.002 | 0.45 | -1.32 ±0.18 | 0.634 |
| 2) 60–90 | 80 | %6 | %4 | yeşil | 0.277 | 0.048 | -0.082 | 0.42 | -1.47 ±0.19 | 0.208 |
| 3) 90–120 | 80 | %6 | %9 | yeşil | 0.277 | 0.722 | -0.087 | 0.43 | -1.39 ±0.19 | 0.830 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 80 | %2 | %14 | yeşil | 0.016 | 0.350 | -0.121 | 0.45 | -1.29 ±0.18 | 0.153 |
| 2) 0.030–0.032 | 80 | %6 | %2 | yeşil | 0.277 | 0.016 | 0.013 | 0.40 | -1.62 ±0.21 | 0.364 |
| 3) 0.032–0.034 | 80 | %10 | %4 | yeşil | 1.000 | 0.048 | -0.064 | 0.46 | -1.28 ±0.17 | 0.932 |


### record_lag (varsayım: tahsilatların deftere işlenme gecikmesi, gün (muhasebe))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0–5 | 77 | %6 | %8 | yeşil | 0.350 | 0.578 | -0.012 | 0.41 | -1.39 ±0.18 | 0.598 |
| 2) 5–9 | 69 | %6 | %13 | yeşil | 0.248 | 0.418 | -0.176 | 0.49 | -1.03 ±0.19 | 0.866 |
| 3) 9–14 | 94 | %6 | %1 | yeşil | 0.243 | 0.001 | -0.008 | 0.42 | -1.67 ±0.18 | 0.934 |


### ayin_gunu

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 1–10 | 72 | %7 | %3 | yeşil | 0.442 | 0.032 | 0.033 | 0.36 | -1.64 ±0.22 | 0.329 |
| 2) 10–21 | 87 | %6 | %8 | yeşil | 0.214 | 0.600 | -0.032 | 0.44 | -1.23 ±0.15 | 0.933 |
| 3) 21–31 | 81 | %6 | %9 | yeşil | 0.276 | 0.721 | -0.165 | 0.50 | -1.36 ±0.19 | 0.677 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 6–53 | 80 | %8 | %12 | yeşil | 0.474 | 0.577 | -0.156 | 0.46 | -0.35 ±0.08 | 0.220 |
| 2) 53–90 | 80 | %6 | %5 | yeşil | 0.277 | 0.142 | 0.059 | 0.38 | -0.93 ±0.10 | 0.666 |
| 3) 90–186 | 80 | %5 | %2 | yeşil | 0.142 | 0.016 | -0.075 | 0.46 | -2.91 ±0.21 | 0.189 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 74 | %5 | %5 | yeşil | 0.189 | 0.189 | -0.101 | 0.53 | -2.09 ±0.24 | 0.921 |
| 2) 14–37 | 86 | %6 | %6 | yeşil | 0.215 | 0.215 | -0.066 | 0.45 | -1.30 ±0.18 | 0.393 |
| 3) 37–120 | 80 | %8 | %9 | yeşil | 0.474 | 0.722 | -0.008 | 0.32 | -0.86 ±0.11 | 0.112 |

