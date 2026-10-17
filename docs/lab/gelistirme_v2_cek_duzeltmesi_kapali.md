## Senaryo laboratuvarı: gelistirme kümesi (240 sentetik işletme)

Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi "müşteri her zamanki kadar geç öder" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 eksiye düşme olasılıklarının kalibre olmadığını gösterir.

Gerçekçilik denetimi: hedef tahsil süresi medyanı 70 gün, ulaşılan 71 gün; senaryoların %83'i hedefin ±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: %9.

### Zayıf bölgeler

Ham Kupiec alt uç p < 0,05 olan kesit sayısı: 37 / 37 (çoklu testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.

- genel = tümü (n=240): Basel kırmızı, Kupiec alt q=0.000
- olcek = kucuk (n=96): Basel kırmızı, Kupiec alt q=0.000
- olcek = mikro (n=84): Basel kırmızı, Kupiec alt q=0.000
- olcek = orta (n=60): Basel kırmızı, Kupiec alt q=0.000
- season_amp = 1) 0.00–0.10 (n=80): Basel kırmızı, Kupiec alt q=0.000
- season_amp = 2) 0.10–0.20 (n=80): Basel kırmızı, Kupiec alt q=0.000
- season_amp = 3) 0.20–0.30 (n=80): Basel kırmızı, Kupiec alt q=0.000
- inflation = 1) 0.00–0.17 (n=80): Basel kırmızı, Kupiec alt q=0.000
- inflation = 2) 0.17–0.33 (n=80): Basel kırmızı, Kupiec alt q=0.000
- inflation = 3) 0.33–0.50 (n=80): Basel kırmızı, Kupiec alt q=0.000
- size_sigma = 1) 0.60–0.84 (n=80): Basel kırmızı, Kupiec alt q=0.000
- size_sigma = 2) 0.84–1.07 (n=80): Basel kırmızı, Kupiec alt q=0.000
- size_sigma = 3) 1.07–1.30 (n=80): Basel kırmızı, Kupiec alt q=0.000
- history = 1) 15–22 (n=74): Basel kırmızı, Kupiec alt q=0.000
- history = 2) 22–29 (n=80): Basel kırmızı, Kupiec alt q=0.000
- history = 3) 29–36 (n=86): Basel kırmızı, Kupiec alt q=0.000
- trend = 1) 0.00–0.40 (n=80): Basel kırmızı, Kupiec alt q=0.000
- trend = 2) 0.40–0.80 (n=80): Basel kırmızı, Kupiec alt q=0.000
- trend = 3) 0.80–1.20 (n=80): Basel kırmızı, Kupiec alt q=0.000
- shock = 1) 0.00–0.10 (n=80): Basel kırmızı, Kupiec alt q=0.000
- shock = 2) 0.10–0.20 (n=80): Basel kırmızı, Kupiec alt q=0.000
- shock = 3) 0.20–0.30 (n=80): Basel kırmızı, Kupiec alt q=0.000
- cheque_share = 1) 0.00–0.20 (n=80): Basel sarı, Kupiec alt q=0.009
- cheque_share = 2) 0.20–0.40 (n=80): Basel kırmızı, Kupiec alt q=0.000
- cheque_share = 3) 0.40–0.60 (n=80): Basel kırmızı, Kupiec alt q=0.000
- cheque_term = 1) 30–60 (n=80): Basel kırmızı, Kupiec alt q=0.000
- cheque_term = 2) 60–90 (n=80): Basel kırmızı, Kupiec alt q=0.000
- cheque_term = 3) 90–120 (n=80): Basel kırmızı, Kupiec alt q=0.000
- cheque_bounce = 1) 0.028–0.030 (n=80): Basel kırmızı, Kupiec alt q=0.000
- cheque_bounce = 2) 0.030–0.032 (n=80): Basel kırmızı, Kupiec alt q=0.000
- cheque_bounce = 3) 0.032–0.034 (n=80): Basel kırmızı, Kupiec alt q=0.000
- dso = 1) 14–55 (n=80): Basel kırmızı, Kupiec alt q=0.000
- dso = 2) 55–85 (n=80): Basel kırmızı, Kupiec alt q=0.000
- dso = 3) 85–184 (n=80): Basel kırmızı, Kupiec alt q=0.000
- customers = 1) 5–14 (n=77): Basel kırmızı, Kupiec alt q=0.000
- customers = 2) 14–37 (n=83): Basel kırmızı, Kupiec alt q=0.000
- customers = 3) 37–119 (n=80): Basel kırmızı, Kupiec alt q=0.000

### genel

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| tümü | 240 | %40 | %3 | kırmızı | 0.000 | 0.000 | 0.559 | 0.83 | -0.78 ±0.11 | 0.000 |


### olcek

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| kucuk | 96 | %39 | %2 | kırmızı | 0.000 | 0.004 | 0.598 | 0.79 | -0.64 ±0.15 | 0.000 |
| mikro | 84 | %29 | %6 | kırmızı | 0.000 | 0.218 | 0.413 | 0.92 | -1.31 ±0.23 | 0.000 |
| orta | 60 | %57 | %0 | kırmızı | 0.000 | 0.002 | 0.700 | 0.75 | -0.25 ±0.11 | 0.000 |


### season_amp (UCI Online Retail II: gerçek KOBİ'de genlik 0,30)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %44 | %2 | kırmızı | 0.000 | 0.016 | 0.657 | 0.88 | -0.81 ±0.19 | 0.000 |
| 2) 0.10–0.20 | 80 | %38 | %1 | kırmızı | 0.000 | 0.003 | 0.541 | 0.80 | -0.91 ±0.19 | 0.000 |
| 3) 0.20–0.30 | 80 | %38 | %5 | kırmızı | 0.000 | 0.142 | 0.478 | 0.81 | -0.61 ±0.17 | 0.000 |


### inflation (TÜİK TÜFE yıllık, 2021-2025: ~%20-%85)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.17 | 80 | %40 | %1 | kırmızı | 0.000 | 0.003 | 0.605 | 0.79 | -1.14 ±0.20 | 0.000 |
| 2) 0.17–0.33 | 80 | %34 | %4 | kırmızı | 0.000 | 0.048 | 0.455 | 0.76 | -0.71 ±0.17 | 0.000 |
| 3) 0.33–0.50 | 80 | %45 | %4 | kırmızı | 0.000 | 0.048 | 0.616 | 0.93 | -0.48 ±0.17 | 0.000 |


### size_sigma (Online Retail II alt örneklemleri: Gini 0,56-0,70)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.60–0.84 | 80 | %44 | %4 | kırmızı | 0.000 | 0.048 | 0.647 | 0.93 | -0.74 ±0.17 | 0.000 |
| 2) 0.84–1.07 | 80 | %39 | %1 | kırmızı | 0.000 | 0.003 | 0.609 | 0.79 | -0.79 ±0.18 | 0.000 |
| 3) 1.07–1.30 | 80 | %36 | %4 | kırmızı | 0.000 | 0.048 | 0.421 | 0.77 | -0.80 ±0.20 | 0.000 |


### history (varsayım: işletmenin sisteme verdiği geçmiş (ay))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 15–22 | 74 | %45 | %0 | kırmızı | 0.000 | 0.000 | 0.646 | 0.81 | -0.65 ±0.17 | 0.000 |
| 2) 22–29 | 80 | %42 | %2 | kırmızı | 0.000 | 0.016 | 0.564 | 0.81 | -0.49 ±0.15 | 0.000 |
| 3) 29–36 | 86 | %33 | %6 | kırmızı | 0.000 | 0.215 | 0.479 | 0.86 | -1.15 ±0.21 | 0.000 |


### trend (varsayım: gecikmelerin dönem içinde kötüleşmesi)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.40 | 80 | %35 | %1 | kırmızı | 0.000 | 0.003 | 0.587 | 0.77 | -0.80 ±0.13 | 0.000 |
| 2) 0.40–0.80 | 80 | %36 | %4 | kırmızı | 0.000 | 0.048 | 0.409 | 0.81 | -0.90 ±0.24 | 0.000 |
| 3) 0.80–1.20 | 80 | %48 | %4 | kırmızı | 0.000 | 0.048 | 0.680 | 0.90 | -0.63 ±0.16 | 0.000 |


### shock (varsayım: çeyreklik ortak piyasa şoku)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.10 | 80 | %38 | %4 | kırmızı | 0.000 | 0.048 | 0.583 | 0.78 | -0.72 ±0.18 | 0.000 |
| 2) 0.10–0.20 | 80 | %41 | %4 | kırmızı | 0.000 | 0.048 | 0.567 | 0.85 | -0.69 ±0.18 | 0.000 |
| 3) 0.20–0.30 | 80 | %40 | %1 | kırmızı | 0.000 | 0.003 | 0.527 | 0.86 | -0.92 ±0.19 | 0.000 |


### cheque_share (varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.00–0.20 | 80 | %21 | %4 | sarı | 0.004 | 0.048 | 0.136 | 0.67 | -0.75 ±0.15 | 0.002 |
| 2) 0.20–0.40 | 80 | %38 | %5 | kırmızı | 0.000 | 0.142 | 0.527 | 0.79 | -0.78 ±0.19 | 0.000 |
| 3) 0.40–0.60 | 80 | %60 | %0 | kırmızı | 0.000 | 0.000 | 1.014 | 1.02 | -0.80 ±0.21 | 0.000 |


### cheque_term (varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok))

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 30–60 | 80 | %31 | %4 | kırmızı | 0.000 | 0.048 | 0.524 | 0.77 | -1.11 ±0.18 | 0.000 |
| 2) 60–90 | 80 | %42 | %1 | kırmızı | 0.000 | 0.003 | 0.455 | 0.82 | -0.63 ±0.17 | 0.000 |
| 3) 90–120 | 80 | %45 | %4 | kırmızı | 0.000 | 0.048 | 0.697 | 0.90 | -0.59 ±0.19 | 0.000 |


### cheque_bounce (TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz)

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 0.028–0.030 | 80 | %42 | %6 | kırmızı | 0.000 | 0.277 | 0.567 | 0.87 | -0.59 ±0.17 | 0.000 |
| 2) 0.030–0.032 | 80 | %49 | %1 | kırmızı | 0.000 | 0.003 | 0.669 | 0.84 | -0.70 ±0.16 | 0.000 |
| 3) 0.032–0.034 | 80 | %28 | %1 | kırmızı | 0.000 | 0.003 | 0.440 | 0.78 | -1.04 ±0.22 | 0.000 |


### dso

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 14–55 | 80 | %42 | %2 | kırmızı | 0.000 | 0.016 | 0.485 | 0.86 | -0.01 ±0.07 | 0.000 |
| 2) 55–85 | 80 | %46 | %5 | kırmızı | 0.000 | 0.142 | 0.573 | 0.80 | -0.32 ±0.09 | 0.000 |
| 3) 85–184 | 80 | %30 | %1 | kırmızı | 0.000 | 0.003 | 0.618 | 0.82 | -2.00 ±0.24 | 0.000 |


### customers

| kesit | n | alt_aşım | üst_aşım | basel | kupiec_alt_p | kupiec_üst_p | sapma_ay | hata_ay | fark_medyan | spiegelhalter_p |
|---|---|---|---|---|---|---|---|---|---|---|
| 1) 5–14 | 77 | %31 | %6 | kırmızı | 0.000 | 0.350 | 0.415 | 0.95 | -1.22 ±0.24 | 0.000 |
| 2) 14–37 | 83 | %37 | %1 | kırmızı | 0.000 | 0.002 | 0.606 | 0.81 | -0.89 ±0.17 | 0.000 |
| 3) 37–119 | 80 | %50 | %1 | kırmızı | 0.000 | 0.003 | 0.647 | 0.73 | -0.23 ±0.09 | 0.000 |

