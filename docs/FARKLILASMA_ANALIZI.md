# Farklılaşma analizi: neredeyiz, nerede fark yaratabiliriz (22 Ekim 2026)

Soru: Sistemsel olarak tamam mıyız; benzer ürünlerin gerisinde miyiz; pazarda olmayan ya da yeni başlayan, bizim yaparsak değer katacağımız neler var?

Kısa cevap:
- **Pilot için tamamız.** Yöntem bakımından incelediğimiz ürünlerin önündeyiz.
- **Ürün olarak bazı alanlarda gerideyiz:** canlı banka bağlantısı, mobil, bulut, finansmana bağlanma. Bunlar hata değil, olgunluk farkıdır ve çoğu lisans, ortaklık ya da gerçek kullanıcı gerektirir.
- **Fark yaratabileceğimiz yedi alan var.** Hiçbiri pilottan önce yapılmayacak (özellik dondurması). Önce pilot öncesi görüşmelerde talep olup olmadığı sınanacak (pilot hazırlık kiti, H7–H11).

Kaynak notu: Ürün bilgileri üreticilerin kendi sayfalarından ve basından alındı. Performans iddiaları kanıt sayılmadı. Bulunamayan bir özellik "yok" demek değildir; "kamuya açık kaynakta görülmedi" demektir.

## 1. Benzer ürünlere göre durum

| Alan | Biz | Pazar (görülen) | Değerlendirme |
|---|---|---|---|
| Fatura bazında ödeme günü tahmini | Var (kantil model + müşteri alışkanlığı) | Xero JAX ödeme günü tahmini ve tahmine göre hatırlatma (Eylül 2025); HighRadius, CashAnalytics | Eşit |
| Kasa belirsizliğinin ölçülmüş bandı | Var: P10/P50/P90, konformal ayar, Basel/Kupiec ile sınanmış | Float/FreeAgent "Forecast Confidence" göstergesi; HighRadius "%95 güven" diyor ama yöntemi açıklamıyor. Kalibrasyonu ölçülmüş bant sunan ticari ürün görülmedi | **Önde** |
| Bağımsız ve önceden kayıtlı isabet ölçümü | Pilot protokolü 1.8, basit yöntemlere karşı | Yayımlanmış bağımsız ölçüm görülmedi; isabet yüzdeleri üretici iddiası | **Önde** (pilot bitince) |
| Türk çek sistemi (vade, karşılıksızlık, ciro) | Var | Paraşüt'te çek hatırlatması var, risk modeli görülmedi | **Önde** |
| Hukuka uygun hatırlatma (TTK m.1530, ticari ileti yönetmeliği, MERSİS kilidi) | Var | Paraşüt otomatik hatırlatma e-postası gönderiyor; yasal içerik denetimi görülmedi | **Önde** |
| Veri yerelde, buluta gitmiyor | Var | Rakiplerin hepsi bulut | Farklı tercih: güven avantajı, ölçek dezavantajı |
| Canlı banka bağlantısı | Yok (ekstre yükleme) | Xero, QuickBooks, Paraşüt (banka entegrasyonu), Akbank mobil | **Geride** |
| Mobil uygulama | Yok | Paraşüt, Akbank, Xero, QuickBooks | **Geride** |
| Otomatik hatırlatma gönderimi | Bilinçli olarak yok (taslak + kullanıcı onayı) | Paraşüt, Xero | Farklı tercih (hukuki risk) |
| Tahsilat yolu (kartla ödeme bağlantısı) | Yok | Paraşüt (iyzico) | **Geride** |
| Finansmana bağlanma | Yok | Paraşüt–Figopara entegrasyonu; Albaraka–Figopara (Eylül 2026) | **Geride** |
| Banka içi nakit tahmini | — | Akbank Mobil "İşin için": nakit akışı ve "gelecek günler için tahmin" (yöntem açıklanmıyor) | Bankalar alana giriyor; kendi müşterisiyle sınırlı |

Sonuç: Yöntem, Türkiye'ye uyum ve güven tarafında öndeyiz; bağlantı, kanal ve olgunluk tarafında gerideyiz. Gerideki alanların çoğu pilottan sonra ortaklıkla kapanır; kendi başımıza yazmamız gerekmez.

## 2. Fark yaratabilecek yedi alan

Her biri için: pazarda durum, bizim için anlamı, ön koşul ve pilot öncesi sınanacak hipotez.

### 2.1 Doğrulanmış isabet karnesi
- **Pazarda:** Ürünler isabet yüzdesi iddia ediyor ama bağımsız, önceden kayıtlı ölçüm yayımlamıyor. Kalibre belirsizlik ticari üründe görülmedi; araştırma tarafında kalıyor.
- **Bizim için:** Pilot bittiğinde, bağımsız yeniden hesaplanmış (protokol 1.7) "basit yöntemlere karşı isabet karnesi" yayımlamak. Reklam Yönetmeliği m.9'un istediği kanıt da budur. Bu, kopyalanması en zor farktır.
- **Ön koşul:** Pilot verisi ve bağımsız hesaplayan kişi. Yeni kod gerekmez.

### 2.2 Keşideci bazlı çek riski (Findeks karekodlu çek skoru)
- **Durum (22.10.2026): yapıldı** (özellik dondurmasına bilinçli istisna).
- **Pazarda:** KKB'nin karekodlu çek raporunda keşidecinin gelecek 9 ayda çeklerini ödeme olasılığı (Karekodlu Çek Skoru), son 5 yılın ödenmeyen çekleri ve çek endeksi var. Rapor bugün Findeks mobil uygulamasında karekod okutularak alınıyor. Bu skoru kasa tahminine girdi yapan bir ürün görülmedi.
- **Bizim için:** İlk adım entegrasyon değil, çek portföyüne isteğe bağlı "Findeks ödeme olasılığı" sütunu. Kullanıcı skoru kendi Findeks uygulamasından okur; panel TBB ortalaması yerine bu olasılığı kullanır.
- **Ön koşul:** Kullanım koşullarının ve KVKK'nın avukatla değerlendirilmesi (keşideci bilgisi); kurumsal entegrasyon için KKB ile sözleşme.
- **Hipotez H7:** Çekle çalışan işletmeler Findeks çek raporunu zaten kullanıyor ve skoru dosyaya girmeye razı.

### 2.3 e-Fatura kabul ve ret yanıtı: itirazın resmî sinyali
- **Durum (22.10.2026): yapıldı** (özellik dondurmasına bilinçli istisna).
- **Pazarda:** Ticari faturada alıcı faturayı kabul, ret ya da iade edebiliyor. Yanıt UBL-TR'de "uygulama yanıtı" olarak iletiliyor. 8 gün içinde itiraz edilmeyen fatura kabul edilmiş sayılır (TTK m.21/2). Bu sinyali tahsilat tahminine katan ürün görülmedi.
- **Bizim için:** Reddedilen fatura itirazlı sayılır ve tahminden çıkar; kabul edilen ticari fatura "itiraz riski düşük" işaretlenir. İtiraz bugün elle giriliyor.
- **Ön koşul:** GİB'in UBL-TR uygulama yanıtı belgesinin birincil kaynaktan okunması; entegratör dışa aktarımlarında yanıtın bulunup bulunmadığı (pilot işletmesinin dosyasıyla).
- **Hipotez H8:** Pilot işletmelerinin entegratör dışa aktarımında kabul ve ret bilgisi var.

### 2.4 Açığı kapatmanın maliyet karşılaştırması
- **Pazarda:** Faktoring ve tedarik zinciri finansmanı büyüyor (Albaraka–Figopara, Eylül 2026). Paraşüt Figopara'ya bağlanıyor. Görülen ürünler ya tahmin ya finansman sunuyor. "Kasa şu gün açık veriyor; açığı kapatmanın en ucuz yolu hangisi" karşılaştırmasını yapan ürün görülmedi.
- **Bizim için:** Panel zaten "açığı kapatmak için ne gerekir" hesabını yapıyor (hangi faturalar, hangi ödeme ertelemesi). Bunun yanına kullanıcının girdiği faktoring ya da kredi maliyetiyle karşılaştırma eklenebilir: erken tahsilat için iskonto, faktoring, kredi limiti, ödeme erteleme (TTK m.1530 temerrüt faizi dahil).
- **Ön koşul:** Bunun yatırım ya da finansal danışmanlık sayılmayacağı avukat görüşü (soru 19 ve 22); faiz verisi için TCMB izni ya da kullanıcı girişi.
- **Hipotez H9:** İşletmeler son bir yılda nakit açığını faktoring, kredi ya da erken ödeme iskontosuyla kapattı ve seçeneklerin maliyetini karşılaştırmakta zorlandı.

### 2.5 Mali müşavir portföy görünümü
- **Durum (22.10.2026): yapıldı** (özellik dondurmasına bilinçli istisna).
- **Pazarda:** KOBİ'ler muhasebecisini "güvenilen ortak" olarak görüyor (Blackburn, Carey ve Tanewski). 10–49 çalışanlı Türk işletmelerinin yalnızca %23,6'sı ERP kullanıyor (TÜİK 2025, ikincil aktarım). Müşavire, müşterilerinin hepsinin kasa riskini tek ekranda sıralayan bir araç görülmedi.
- **Bizim için:** Panelde birden çok işletme desteği zaten var. Bunun üstüne "müşterilerim: önümüzdeki 90 günde kasası en riskli olanlar" listesi kurulabilir. Müşavire yeni bir danışmanlık hizmeti, bize de dağıtım kanalı sağlar.
- **Ön koşul:** Her müşteri için Ek A ve müşavirin sır saklama yükümlülüğünün avukatla değerlendirilmesi (soru 13).
- **Hipotez H10:** Müşavirler müşterilerine nakit konusunda danışmanlık vermek istiyor ve birden çok müşteriyi tek ekranda görmek bunu kolaylaştırır.

### 2.6 Açık bankacılıkla otomatik banka verisi
- **Pazarda:** TCMB ÖHVPS 2.0.0 sürümünü 17 Mart 2026'da devreye aldı. Hesap bilgisi hizmeti genişledi; ileri tarihli ve düzenli ödeme emri geldi. Ekosistemde 53 katılımcı ve 16,4 milyon kullanıcı var. Tüzel kişi hesaplarının kapsamı ve muhasebe entegrasyonu kamuya açık kaynaklarda net değil.
- **Bizim için:** Haftalık ekstre yükleme yükünü (pilotun en büyük kayıp riski) ortadan kaldırır.
- **Ön koşul:** Hesap bilgisi hizmeti TCMB iznine bağlı bir ödeme hizmeti. Kendimiz lisans almak yerine lisanslı bir kuruluşla ortaklık; yerel çalışma ilkesinin yeniden değerlendirilmesi. Uzun vadeli.
- **Hipotez H11:** Haftalık dosya yükleme, pilotta bırakmanın birinci nedeni olur (pilot çıkış görüşmelerinden ölçülecek).

### 2.7 Değeri ölçülen kullanıcı düzeltmesi ve etkiye göre tahsilat önceliği
- **Pazarda:** Kullanıcının tahmini az da olsa düzeltebilmesi algoritmaya güveni artırır (Dietvorst, Simmons ve Massey 2018). Ama küçük ve iyimser düzeltmeler isabeti sık bozar (Fildes vd. 2009). Tahsilat araçları müşterileri riske göre sıralıyor. Hatırlatmanın kimde gerçekten fark yarattığını ölçen KOBİ ürünü görülmedi (etkiye göre sıralama ve rastgele kontrol grubu; Tala).
- **Bizim için:** Düzeltmeyi kaydedip değerini ölçmek (Forecast Value Added; Gilliland 2013) ve pilotun ikinci aşamasında küçük rastgele kontrol grupları tutmak. İkisi birlikte "kullanıcıya söz hakkı veren ama sonucunu ölçen" bir ürün demek.
- **Ön koşul:** Pilot verisi; kontrol grupları için katılımcı onayı.

## 3. Sıralama

| Sıra | Alan | Neden bu sırada | Ne zaman |
|---|---|---|---|
| 1 | Doğrulanmış isabet karnesi | Kod gerektirmez; en güçlü güven farkı; reklam kuralının şartı | Pilot sonu |
| 2 | e-Fatura kabul/ret sinyali | Küçük iş, resmî veri, rakipte yok | İlk pilot işletmesinin dosyasıyla, talep olursa |
| 3 | Findeks çek skoru (elle giriş) | Küçük iş, Türkiye'ye özgü en belirgin model boşluğu | Çekli pilot işletmesi isterse |
| 4 | Müşavir portföy görünümü | Dağıtım kanalı; mevcut altyapı üstüne | Pilot müşaviri isterse |
| 5 | Açığı kapatmanın maliyet karşılaştırması | Değerli, ama hukuki görüş gerektirir | Avukat görüşünden sonra |
| 6 | Kullanıcı düzeltmesi ve kontrol grupları | Ölçüm tasarımı pilotun ikinci aşamasında | Pilot faz 2 |
| 7 | Açık bankacılık | En büyük kullanım kazancı; lisanslı ortak gerektirir | Pilot sonrası, ortaklıkla |

Bu sıralama, pilot öncesi görüşmelerde H7–H11'in sonucuna göre değişebilir. Talep görülmeyen alan yapılmaz.

## Kaynaklar

- Xero JAX, ödeme günü tahmini: TechRepublic, "Xero's JAX Now Smarter at Predicting When Customers Will Pay" (2025).
- FreeAgent, "3 cashflow forecasting integrations for 2026" (Float, Forecast Confidence).
- HighRadius, AI-Powered Cash Forecasting ürün sayfası.
- Akbank, Dijital Çözümler (KOBİ): "İşin için" nakit akışı ve tahmin.
- Paraşüt, Nakit Yönetimi sayfası ve Figopara entegrasyonu kullanım kılavuzu.
- Albaraka Türk ve Figopara tedarikçi finansmanı iş birliği (Foreks/AA, Eylül 2026).
- KKB/Findeks, Karekodlu Çek Raporu örneği.
- e-Fatura uygulama yanıtı (kabul, red, iade) ve 8 günlük süre: ikincil kaynaklar (Muhasebetr, Alomaliye); TTK m.21/2. GİB UBL-TR belgesi birincil kaynaktan okunacak.
- TCMB açık bankacılık ÖHVPS 2.0.0 duyurusu (17 Mart 2026; Bloomberg HT, Alomaliye aktarımı).
- arXiv 2511.03631, "Financial Management System for SMEs: Real-World Deployment of Accounts Receivable and Cash Flow Prediction" (2025): belirsizlik ele alınmıyor.
- Blackburn, Carey ve Tanewski (2010); Dietvorst, Simmons ve Massey (2018), Management Science; Fildes, Goodwin, Lawrence ve Nikolopoulos (2009), IJF; Gilliland (2013), Foresight.
