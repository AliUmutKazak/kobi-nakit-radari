## Senaryo laboratuvarı: gelistirme kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 68 gün, ulaşılan 68 gün; senaryoların %80'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %8.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 23 / 49 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- Yok.

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %5 | %11 | yeşil | 0.003 | 0.747 | -0.159 | 0.44 | -1.11 ±0.10 | 0.393 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %4 | %12 | yeşil | 0.045 | 0.495 | -0.155 | 0.41 | -0.90 ±0.12 | 0.787 |
| mikro | 84 | %5 | %11 | yeşil | 0.107 | 0.855 | -0.224 | 0.58 | -1.71 ±0.22 | 0.649 |
| orta | 60 | %5 | %8 | yeşil | 0.210 | 0.686 | -0.077 | 0.31 | -0.62 ±0.09 | 0.396 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %1 | %5 | yeşil | 0.003 | 0.142 | -0.132 | 0.38 | -1.33 ±0.18 | 0.727 |
| 2) 0.10–0.20 | 80 | %6 | %15 | yeşil | 0.277 | 0.188 | -0.188 | 0.47 | -1.05 ±0.17 | 0.832 |
| 3) 0.20–0.30 | 80 | %6 | %12 | yeşil | 0.277 | 0.577 | -0.158 | 0.48 | -0.95 ±0.13 | 0.178 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 80 | %4 | %8 | yeşil | 0.048 | 0.474 | -0.094 | 0.39 | -1.08 ±0.17 | 0.261 |
| 2) 0.17–0.33 | 80 | %4 | %18 | yeşil | 0.048 | 0.062 | -0.279 | 0.50 | -0.96 ±0.18 | 0.233 |
| 3) 0.33–0.50 | 80 | %6 | %8 | yeşil | 0.277 | 0.474 | -0.105 | 0.44 | -1.29 ±0.14 | 0.112 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.83 | 80 | %4 | %10 | yeşil | 0.048 | 1.000 | -0.138 | 0.34 | -1.22 ±0.16 | 0.177 |
| 2) 0.83–1.07 | 80 | %8 | %9 | yeşil | 0.474 | 0.722 | -0.143 | 0.46 | -1.19 ±0.18 | 0.665 |
| 3) 1.07–1.30 | 80 | %2 | %14 | yeşil | 0.016 | 0.350 | -0.197 | 0.54 | -0.92 ±0.16 | 0.791 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 74 | %5 | %9 | yeşil | 0.189 | 1.000 | -0.099 | 0.39 | -1.01 ±0.16 | 0.010 |
| 2) 22–29 | 81 | %4 | %10 | yeşil | 0.047 | 1.000 | -0.201 | 0.44 | -1.31 ±0.21 | 0.706 |
| 3) 29–36 | 85 | %5 | %13 | yeşil | 0.107 | 0.470 | -0.172 | 0.49 | -1.01 ±0.13 | 0.194 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.40 | 80 | %5 | %9 | yeşil | 0.142 | 0.722 | -0.147 | 0.41 | -1.09 ±0.14 | 0.229 |
| 2) 0.40–0.80 | 80 | %8 | %15 | yeşil | 0.474 | 0.188 | -0.140 | 0.45 | -1.02 ±0.15 | 0.724 |
| 3) 0.80–1.20 | 80 | %1 | %9 | yeşil | 0.003 | 0.722 | -0.191 | 0.46 | -1.22 ±0.20 | 0.532 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %2 | %14 | yeşil | 0.016 | 0.350 | -0.188 | 0.42 | -1.17 ±0.17 | 0.147 |
| 2) 0.10–0.20 | 80 | %8 | %8 | yeşil | 0.474 | 0.474 | -0.094 | 0.45 | -1.01 ±0.16 | 0.911 |
| 3) 0.20–0.30 | 80 | %4 | %11 | yeşil | 0.048 | 0.853 | -0.196 | 0.46 | -1.16 ±0.17 | 0.869 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 80 | %2 | %16 | yeşil | 0.016 | 0.089 | -0.249 | 0.57 | -0.88 ±0.16 | 0.191 |
| 2) 0.20–0.40 | 80 | %4 | %10 | yeşil | 0.048 | 1.000 | -0.143 | 0.44 | -1.23 ±0.18 | 0.020 |
| 3) 0.40–0.60 | 80 | %8 | %6 | yeşil | 0.474 | 0.277 | -0.085 | 0.32 | -1.22 ±0.15 | 0.659 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–60 | 80 | %4 | %12 | yeşil | 0.048 | 0.577 | -0.190 | 0.46 | -0.92 ±0.15 | 0.405 |
| 2) 60–90 | 80 | %6 | %8 | yeşil | 0.277 | 0.474 | -0.186 | 0.46 | -1.10 ±0.16 | 0.514 |
| 3) 90–120 | 80 | %4 | %12 | yeşil | 0.048 | 0.577 | -0.102 | 0.41 | -1.31 ±0.19 | 0.191 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 80 | %6 | %14 | yeşil | 0.277 | 0.350 | -0.233 | 0.50 | -1.07 ±0.17 | 0.462 |
| 2) 0.030–0.032 | 80 | %2 | %11 | yeşil | 0.016 | 0.853 | -0.145 | 0.40 | -1.00 ±0.13 | 0.572 |
| 3) 0.032–0.034 | 80 | %5 | %8 | yeşil | 0.142 | 0.474 | -0.099 | 0.43 | -1.26 ±0.19 | 0.204 |


### record_lag (VUK m.219: kayıt en geç 10 gün, fişe dayanan kayıtta 45 gün; aralık varsayım)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0–5 | 77 | %4 | %12 | yeşil | 0.063 | 0.703 | -0.221 | 0.47 | -1.02 ±0.18 | 0.550 |
| 2) 5–9 | 69 | %1 | %12 | yeşil | 0.007 | 0.686 | -0.159 | 0.40 | -1.13 ±0.20 | 0.623 |
| 3) 9–14 | 94 | %7 | %10 | yeşil | 0.494 | 1.000 | -0.109 | 0.45 | -1.17 ±0.12 | 0.222 |


### partial_share (varsayım: faturalarını iki taksitte kapatan müşteri payı)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.13 | 80 | %2 | %6 | yeşil | 0.016 | 0.277 | -0.128 | 0.42 | -1.07 ±0.15 | 0.659 |
| 2) 0.13–0.27 | 80 | %8 | %8 | yeşil | 0.474 | 0.474 | -0.168 | 0.42 | -1.33 ±0.19 | 0.696 |
| 3) 0.27–0.40 | 80 | %4 | %19 | yeşil | 0.048 | 0.023 | -0.182 | 0.49 | -0.93 ±0.14 | 0.154 |


### missing_due (veri kalitesi: vadesi girilmemiş fatura payı (TTK m.1530/4-a: 30 gün))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %5 | %12 | yeşil | 0.142 | 0.577 | -0.157 | 0.47 | -1.31 ±0.18 | 0.406 |
| 2) 0.10–0.20 | 80 | %5 | %12 | yeşil | 0.142 | 0.577 | -0.142 | 0.46 | -0.91 ±0.14 | 0.403 |
| 3) 0.20–0.30 | 80 | %4 | %8 | yeşil | 0.048 | 0.474 | -0.179 | 0.40 | -1.12 ±0.18 | 0.142 |


### ayin_gunu

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 1–11 | 79 | %8 | %9 | yeşil | 0.577 | 0.853 | -0.075 | 0.41 | -1.18 ±0.16 | 0.137 |
| 2) 11–20 | 81 | %5 | %9 | yeşil | 0.141 | 0.721 | -0.142 | 0.47 | -1.11 ±0.16 | 0.652 |
| 3) 20–31 | 80 | %1 | %15 | yeşil | 0.003 | 0.188 | -0.259 | 0.45 | -1.05 ±0.18 | 0.644 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 16–51 | 80 | %5 | %16 | yeşil | 0.142 | 0.089 | -0.205 | 0.49 | -0.43 ±0.09 | 0.560 |
| 2) 51–84 | 80 | %8 | %11 | yeşil | 0.474 | 0.853 | -0.147 | 0.42 | -0.77 ±0.12 | 0.253 |
| 3) 84–180 | 80 | %1 | %5 | yeşil | 0.003 | 0.142 | -0.126 | 0.42 | -2.13 ±0.20 | 0.055 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 75 | %5 | %9 | yeşil | 0.187 | 0.855 | -0.207 | 0.58 | -1.69 ±0.22 | 0.813 |
| 2) 14–37 | 85 | %5 | %13 | yeşil | 0.107 | 0.470 | -0.167 | 0.43 | -1.09 ±0.15 | 0.701 |
| 3) 37–119 | 80 | %4 | %10 | yeşil | 0.048 | 1.000 | -0.106 | 0.32 | -0.59 ±0.08 | 0.376 |


