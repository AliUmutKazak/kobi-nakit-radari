## Senaryo laboratuvarı: gelistirme kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 70 gün, ulaşılan 71 gün; senaryoların %83'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %9.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 2 / 37 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- size_sigma = 1) 0.60–0.84 (n=80): Basel sarı
- trend = 3) 0.80–1.20 (n=80): Basel sarı
- cheque_bounce = 2) 0.030–0.032 (n=80): Basel sarı

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %10 | %7 | yeşil | 1.000 | 0.134 | -0.057 | 0.46 | -1.15 ±0.10 | 0.202 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %8 | %6 | yeşil | 0.620 | 0.240 | -0.039 | 0.40 | -1.04 ±0.15 | 0.886 |
| mikro | 84 | %8 | %11 | yeşil | 0.719 | 0.855 | -0.145 | 0.68 | -1.55 ±0.22 | 0.400 |
| orta | 60 | %15 | %3 | yeşil | 0.279 | 0.068 | 0.037 | 0.24 | -0.77 ±0.10 | 0.164 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %10 | %6 | yeşil | 1.000 | 0.277 | -0.011 | 0.43 | -1.26 ±0.19 | 0.371 |
| 2) 0.10–0.20 | 80 | %10 | %5 | yeşil | 1.000 | 0.142 | -0.030 | 0.45 | -1.25 ±0.18 | 0.936 |
| 3) 0.20–0.30 | 80 | %10 | %10 | yeşil | 1.000 | 1.000 | -0.130 | 0.48 | -0.93 ±0.17 | 0.217 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 80 | %10 | %2 | yeşil | 1.000 | 0.016 | 0.034 | 0.41 | -1.52 ±0.20 | 0.394 |
| 2) 0.17–0.33 | 80 | %12 | %11 | yeşil | 0.577 | 0.853 | -0.121 | 0.50 | -0.98 ±0.16 | 0.730 |
| 3) 0.33–0.50 | 80 | %8 | %8 | yeşil | 0.474 | 0.474 | -0.085 | 0.46 | -0.96 ±0.16 | 0.081 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.84 | 80 | %18 | %9 | sarı | 0.062 | 0.722 | -0.021 | 0.50 | -1.17 ±0.17 | 0.557 |
| 2) 0.84–1.07 | 80 | %4 | %4 | yeşil | 0.048 | 0.048 | 0.008 | 0.35 | -1.23 ±0.17 | 0.289 |
| 3) 1.07–1.30 | 80 | %9 | %9 | yeşil | 0.722 | 0.722 | -0.158 | 0.52 | -1.05 ±0.20 | 0.086 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 74 | %15 | %5 | yeşil | 0.244 | 0.189 | 0.024 | 0.44 | -1.02 ±0.17 | 0.599 |
| 2) 22–29 | 80 | %6 | %8 | yeşil | 0.277 | 0.474 | -0.038 | 0.44 | -0.87 ±0.15 | 0.268 |
| 3) 29–36 | 86 | %9 | %8 | yeşil | 0.862 | 0.601 | -0.144 | 0.49 | -1.52 ±0.20 | 0.558 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.40 | 80 | %5 | %5 | yeşil | 0.142 | 0.142 | -0.035 | 0.38 | -1.19 ±0.15 | 0.283 |
| 2) 0.40–0.80 | 80 | %8 | %9 | yeşil | 0.474 | 0.722 | -0.184 | 0.53 | -1.18 ±0.22 | 0.439 |
| 3) 0.80–1.20 | 80 | %18 | %8 | sarı | 0.062 | 0.474 | 0.049 | 0.45 | -1.08 ±0.15 | 0.708 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %9 | %8 | yeşil | 0.722 | 0.474 | -0.087 | 0.37 | -1.13 ±0.17 | 0.436 |
| 2) 0.10–0.20 | 80 | %10 | %8 | yeşil | 1.000 | 0.474 | -0.055 | 0.50 | -1.03 ±0.17 | 0.761 |
| 3) 0.20–0.30 | 80 | %11 | %6 | yeşil | 0.853 | 0.277 | -0.030 | 0.49 | -1.29 ±0.19 | 0.264 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 80 | %9 | %5 | yeşil | 0.722 | 0.142 | -0.077 | 0.57 | -0.86 ±0.16 | 0.890 |
| 2) 0.20–0.40 | 80 | %8 | %12 | yeşil | 0.474 | 0.577 | -0.099 | 0.47 | -1.10 ±0.18 | 0.698 |
| 3) 0.40–0.60 | 80 | %14 | %4 | yeşil | 0.350 | 0.048 | 0.006 | 0.33 | -1.49 ±0.19 | 0.049 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–60 | 80 | %11 | %4 | yeşil | 0.853 | 0.048 | 0.001 | 0.46 | -1.42 ±0.18 | 0.184 |
| 2) 60–90 | 80 | %4 | %8 | yeşil | 0.048 | 0.474 | -0.160 | 0.44 | -1.01 ±0.18 | 0.533 |
| 3) 90–120 | 80 | %15 | %10 | yeşil | 0.188 | 1.000 | -0.012 | 0.46 | -1.03 ±0.18 | 0.805 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 80 | %9 | %11 | yeşil | 0.722 | 0.853 | -0.123 | 0.43 | -1.03 ±0.16 | 0.377 |
| 2) 0.030–0.032 | 80 | %16 | %2 | sarı | 0.089 | 0.016 | 0.077 | 0.44 | -1.10 ±0.16 | 0.054 |
| 3) 0.032–0.034 | 80 | %5 | %8 | yeşil | 0.142 | 0.474 | -0.126 | 0.49 | -1.32 ±0.21 | 0.563 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 14–55 | 80 | %12 | %10 | yeşil | 0.577 | 1.000 | -0.107 | 0.49 | -0.38 ±0.08 | 0.321 |
| 2) 55–85 | 80 | %11 | %10 | yeşil | 0.853 | 1.000 | -0.016 | 0.45 | -0.67 ±0.10 | 0.035 |
| 3) 85–184 | 80 | %6 | %1 | yeşil | 0.277 | 0.003 | -0.048 | 0.43 | -2.39 ±0.23 | 0.325 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 77 | %9 | %12 | yeşil | 0.854 | 0.703 | -0.157 | 0.71 | -1.46 ±0.24 | 0.776 |
| 2) 14–37 | 83 | %10 | %2 | yeşil | 1.000 | 0.012 | -0.004 | 0.40 | -1.30 ±0.17 | 0.197 |
| 3) 37–119 | 80 | %11 | %8 | yeşil | 0.853 | 0.474 | -0.016 | 0.27 | -0.70 ±0.09 | 0.560 |

