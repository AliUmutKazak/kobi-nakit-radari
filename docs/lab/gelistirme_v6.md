## Senaryo laboratuvarı: gelistirme kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 73 gün, ulaşılan 74 gün; senaryoların %79'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %8.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 26 / 52 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- Yok.

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %5 | %10 | yeşil | 0.003 | 1.000 | -0.176 | 0.51 | -1.14 ±0.10 | 0.817 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %6 | %9 | yeşil | 0.240 | 0.869 | -0.134 | 0.46 | -0.96 ±0.13 | 0.313 |
| mikro | 84 | %4 | %10 | yeşil | 0.035 | 1.000 | -0.247 | 0.67 | -1.55 ±0.19 | 0.267 |
| orta | 60 | %3 | %12 | yeşil | 0.068 | 0.831 | -0.144 | 0.38 | -0.85 ±0.17 | 0.644 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %4 | %11 | yeşil | 0.048 | 0.853 | -0.234 | 0.53 | -1.27 ±0.17 | 0.394 |
| 2) 0.10–0.20 | 80 | %1 | %11 | yeşil | 0.003 | 0.853 | -0.174 | 0.46 | -1.19 ±0.18 | 0.736 |
| 3) 0.20–0.30 | 80 | %9 | %8 | yeşil | 0.722 | 0.474 | -0.120 | 0.55 | -0.95 ±0.15 | 0.358 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 80 | %6 | %12 | yeşil | 0.277 | 0.577 | -0.103 | 0.50 | -1.07 ±0.16 | 0.054 |
| 2) 0.17–0.33 | 80 | %2 | %8 | yeşil | 0.016 | 0.474 | -0.251 | 0.50 | -1.21 ±0.16 | 0.636 |
| 3) 0.33–0.50 | 80 | %5 | %10 | yeşil | 0.142 | 1.000 | -0.174 | 0.54 | -1.14 ±0.18 | 0.306 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.83 | 80 | %4 | %12 | yeşil | 0.048 | 0.577 | -0.259 | 0.51 | -1.24 ±0.19 | 0.903 |
| 2) 0.83–1.07 | 80 | %5 | %10 | yeşil | 0.142 | 1.000 | -0.136 | 0.58 | -1.23 ±0.16 | 0.593 |
| 3) 1.07–1.30 | 80 | %5 | %8 | yeşil | 0.142 | 0.474 | -0.134 | 0.46 | -0.96 ±0.14 | 0.799 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 74 | %3 | %9 | yeşil | 0.023 | 1.000 | -0.156 | 0.52 | -0.83 ±0.15 | 0.845 |
| 2) 22–29 | 80 | %2 | %10 | yeşil | 0.016 | 1.000 | -0.328 | 0.54 | -1.18 ±0.19 | 0.548 |
| 3) 29–36 | 86 | %8 | %10 | yeşil | 0.601 | 1.000 | -0.051 | 0.49 | -1.37 ±0.16 | 0.433 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.40 | 80 | %4 | %12 | yeşil | 0.048 | 0.577 | -0.198 | 0.48 | -1.03 ±0.15 | 0.124 |
| 2) 0.40–0.80 | 80 | %8 | %11 | yeşil | 0.474 | 0.853 | -0.207 | 0.60 | -1.01 ±0.15 | 0.002 |
| 3) 0.80–1.20 | 80 | %2 | %6 | yeşil | 0.016 | 0.277 | -0.123 | 0.46 | -1.38 ±0.19 | 0.048 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %6 | %8 | yeşil | 0.277 | 0.474 | -0.076 | 0.51 | -1.08 ±0.16 | 0.572 |
| 2) 0.10–0.20 | 80 | %1 | %10 | yeşil | 0.003 | 1.000 | -0.284 | 0.52 | -0.98 ±0.14 | 0.738 |
| 3) 0.20–0.30 | 80 | %6 | %12 | yeşil | 0.277 | 0.577 | -0.169 | 0.52 | -1.37 ±0.19 | 0.880 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 80 | %2 | %11 | yeşil | 0.016 | 0.853 | -0.267 | 0.59 | -0.76 ±0.13 | 0.487 |
| 2) 0.20–0.40 | 80 | %8 | %10 | yeşil | 0.474 | 1.000 | -0.131 | 0.54 | -1.16 ±0.17 | 0.551 |
| 3) 0.40–0.60 | 80 | %4 | %9 | yeşil | 0.048 | 0.722 | -0.130 | 0.41 | -1.50 ±0.18 | 0.379 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–60 | 80 | %4 | %10 | yeşil | 0.048 | 1.000 | -0.203 | 0.55 | -1.05 ±0.15 | 0.689 |
| 2) 60–90 | 80 | %6 | %11 | yeşil | 0.277 | 0.853 | -0.191 | 0.51 | -1.33 ±0.19 | 0.857 |
| 3) 90–120 | 80 | %4 | %9 | yeşil | 0.048 | 0.722 | -0.135 | 0.49 | -1.04 ±0.15 | 0.315 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 80 | %8 | %11 | yeşil | 0.474 | 0.853 | -0.152 | 0.54 | -1.11 ±0.16 | 0.804 |
| 2) 0.030–0.032 | 80 | %2 | %9 | yeşil | 0.016 | 0.722 | -0.256 | 0.49 | -1.05 ±0.17 | 0.848 |
| 3) 0.032–0.034 | 80 | %4 | %10 | yeşil | 0.048 | 1.000 | -0.120 | 0.51 | -1.26 ±0.18 | 0.407 |


### record_lag (VUK m.219: kayıt en geç 10 gün, fişe dayanan kayıtta 45 gün; aralık varsayım)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0–5 | 77 | %6 | %10 | yeşil | 0.350 | 1.000 | -0.158 | 0.53 | -1.39 ±0.21 | 0.784 |
| 2) 5–9 | 69 | %4 | %6 | yeşil | 0.116 | 0.248 | -0.019 | 0.46 | -0.75 ±0.12 | 0.182 |
| 3) 9–14 | 94 | %3 | %13 | yeşil | 0.018 | 0.387 | -0.305 | 0.54 | -1.23 ±0.14 | 0.597 |


### partial_share (varsayım: faturalarını iki taksitte kapatan müşteri payı)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.13 | 80 | %2 | %15 | yeşil | 0.016 | 0.188 | -0.256 | 0.54 | -0.90 ±0.16 | 0.716 |
| 2) 0.13–0.27 | 80 | %6 | %9 | yeşil | 0.277 | 0.722 | -0.136 | 0.52 | -1.11 ±0.17 | 0.716 |
| 3) 0.27–0.40 | 80 | %5 | %6 | yeşil | 0.142 | 0.277 | -0.137 | 0.48 | -1.41 ±0.16 | 0.735 |


### missing_due (veri kalitesi: vadesi girilmemiş fatura payı (TTK m.1530/4-a: 30 gün))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %8 | %15 | yeşil | 0.474 | 0.188 | -0.196 | 0.56 | -1.19 ±0.18 | 0.527 |
| 2) 0.10–0.20 | 80 | %4 | %5 | yeşil | 0.048 | 0.142 | -0.104 | 0.46 | -1.04 ±0.15 | 0.579 |
| 3) 0.20–0.30 | 80 | %2 | %10 | yeşil | 0.016 | 1.000 | -0.228 | 0.52 | -1.18 ±0.16 | 0.751 |


### outflow_sigma (varsayım: aylık giderlerin dalgalanması (log ölçekte sapma))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %1 | %10 | yeşil | 0.003 | 1.000 | -0.210 | 0.46 | -1.33 ±0.18 | 0.274 |
| 2) 0.10–0.20 | 80 | %5 | %11 | yeşil | 0.142 | 0.853 | -0.204 | 0.54 | -1.05 ±0.17 | 0.595 |
| 3) 0.20–0.30 | 80 | %8 | %9 | yeşil | 0.474 | 0.722 | -0.114 | 0.55 | -1.04 ±0.15 | 0.213 |


### ayin_gunu

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 1–11 | 78 | %1 | %6 | yeşil | 0.003 | 0.349 | -0.126 | 0.48 | -1.22 ±0.18 | 0.548 |
| 2) 11–21 | 80 | %4 | %10 | yeşil | 0.048 | 1.000 | -0.261 | 0.54 | -1.03 ±0.18 | 0.696 |
| 3) 21–31 | 82 | %9 | %13 | yeşil | 0.720 | 0.354 | -0.141 | 0.53 | -1.17 ±0.14 | 0.579 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–55 | 80 | %8 | %11 | yeşil | 0.474 | 0.853 | -0.186 | 0.57 | -0.48 ±0.09 | 0.760 |
| 2) 55–91 | 80 | %1 | %10 | yeşil | 0.003 | 1.000 | -0.197 | 0.45 | -0.61 ±0.10 | 0.285 |
| 3) 91–189 | 80 | %5 | %9 | yeşil | 0.142 | 0.722 | -0.145 | 0.53 | -2.32 ±0.19 | 0.717 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–15 | 80 | %4 | %10 | yeşil | 0.048 | 1.000 | -0.255 | 0.68 | -1.58 ±0.19 | 0.312 |
| 2) 15–38 | 79 | %5 | %10 | yeşil | 0.143 | 1.000 | -0.152 | 0.49 | -0.93 ±0.15 | 0.482 |
| 3) 38–116 | 81 | %5 | %10 | yeşil | 0.141 | 1.000 | -0.121 | 0.38 | -0.90 ±0.14 | 0.496 |


