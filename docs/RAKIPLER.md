# Rakip İncelemesi ve Üzerine Koyduklarımız

Tarih: 14 Ekim 2026. Yöntem: her üründe yalnızca üreticinin kendi ürün sayfasında açıkça yazan özellikler "var" sayıldı. "Belirtilmemiş", özelliğin olmadığı anlamına gelmez; sayfada yazmadığı anlamına gelir. Kesin sonuç için demo görüşmesi gerekir. Üreticilerin performans iddiaları (DSO düşüşü vb.) kanıt sayılmadı.

## Özellik karşılaştırması

| Özellik | Agicap | Upflow | Chaser | Kolleno | Finrota NAP360 | Bu proje |
|---|---|---|---|---|---|---|
| Fatura bazında ödeme tahmini | Belirtilmemiş | Belirtilmemiş | Var (yöntem açıklanmamış) | Belirtilmemiş | Geçmiş ödemelerden tahmin | Var (kantil modeli) |
| Olasılık bandı / kasanın eksiye düşme olasılığı | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş (senaryo var) | Var |
| Tahminin geçmiş veriyle sınanması kullanıcıya gösterilir | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Var |
| Hatırlatma kanalları | E-posta, taahhütlü posta, ödeme bağlantısı | E-posta | E-posta, SMS, otomatik arama | Belirtilmemiş | "Hatırlatma" (kanal belirtilmemiş) | Yalnızca taslak |
| WhatsApp | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Taslak metin; gönderim yok |
| Ajan özerkliği | Belirtilmemiş | "Yalnızca öneri"den "tam otonom"a ayarlanabilir | Yapay zekâ e-posta üretici | "AI Agents" (ayrıntı yok) | Belirtilmemiş | Yalnızca öneri |
| İtirazlı fatura yönetimi | Var (hatırlatmayı durdurur, tahminden çıkarır) | Yanıtlardan itiraz niyetini çıkarır | Belirtilmemiş | Modül var | Belirtilmemiş | Var (bu turda eklendi) |
| Ödeme sözü takibi | Belirtilmemiş | Yanıtlardan ödeme sözünü çıkarır | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Var (elle girilir) |
| En uygun iletişim zamanı | Belirtilmemiş | Belirtilmemiş | Var (gün ve saat) | Belirtilmemiş | Belirtilmemiş | Var (müşterinin ödeme gününe göre) |
| Ödeme portalı / bağlantısı | Ödeme bağlantısı | Belirtilmemiş | Var | Var | Netahsilat (ayrı ürün) | Yok |
| Banka bağlantısı | Var | Tahsilat eşleştirme ajanı | Belirtilmemiş | Belirtilmemiş | Netekstre (açık bankacılık) | Yok (dosya yükleme) |
| Çek / senet | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Var (tek oranla) |
| Türkiye muhasebe / e-fatura uyumu | Yok | Yok | Yok | Yok | ERP entegrasyonu | UBL-TR ve Türkçe dışa aktarım dosyaları |
| Hedef müşteri | Yıllık 10–500 milyon £ ciro | Belirtilmemiş | Belirtilmemiş | Yıllık 1 milyon £ üstü ciro | KOBİ ve büyük şirket | KOBİ |
| Fiyat | Teklifle | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Teklifle | — |

## Yerli ön muhasebe programları

Bu ürünler doğrudan rakip değil, verinin durduğu yer; KOBİ'lerin çoğu faturasını bunlardan kesiyor. Aynı yöntemle (yalnızca kendi sayfalarında yazan) incelendi.

| Özellik | Logo İşbaşı | BizimHesap | Paraşüt | Mikro |
|---|---|---|---|---|
| Nakit akış tahmini yöntemi | Belirtilmemiş (kasa ve banka takibi) | Belirtilmemiş (takip) | Belirtilmemiş | Belirtilmemiş |
| Çek / senet takibi | Çek giriş-çıkış var; senet belirtilmemiş | Çek ve senet var | Belirtilmemiş | Senet (müşteri yorumunda) |
| Otomatik tahsilat hatırlatma | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş |
| Banka entegrasyonu | 17 banka | Var (gelen-giden eşleştirme) | "Akıllı Banka Entegrasyonu" | Belirtilmemiş |
| Online tahsilat | Kartla 7/24 ödeme alma | Sanal POS | Ayrı ürün sayfası var | Belirtilmemiş |
| Fiyat (KDV hariç) | 463–738 ₺/ay | Belirtilmemiş | Belirtilmemiş | Belirtilmemiş |

Sonuç: yerli programlar kaydı, banka eşleştirmesini ve ödeme almayı çözmüş; hiçbirinin sayfasında tahmin yöntemi ya da otomatik hatırlatma geçmiyor. Bu, konumlanmayı netleştiriyor: bu ürün ön muhasebe programının yerine değil üstüne oturmalı, veriyi onlardan almalı. Logo İşbaşı'nın aylık 463–738 ₺ fiyatı da KOBİ'nin bu tür yazılıma ödediği düzey için bir referans.

Kaynaklar: [Logo İşbaşı](https://isbasi.com/), [BizimHesap](https://bizimhesap.com/), [Paraşüt özellikler](https://www.parasut.com/ozellikler), [Mikro tahsilat](https://www.mikro.com.tr/Tahsilat-programi/).

## Rakiplerden alınıp uygulananlar

1. **İtirazlı fatura (Agicap).** İtirazlı işaretlenen fatura hatırlatma listesine ve kasa tahminine girmez; toplamı ayrıca gösterilir. Gerekçe: itirazlı faturaya hatırlatma göndermek ilişkiyi bozar, tahsil edilecekmiş gibi saymak tahmini şişirir.
2. **Ödeme sözü (Upflow).** Söz tarihi girilen faturada bu tarih yeni vade sayılır ve söz tarihi geçene kadar hatırlatma üretilmez. Upflow bunu e-posta yanıtlarından otomatik çıkarıyor; bizde panelden elle giriliyor.
3. **İletişim zamanı (Chaser).** Chaser "en iyi gün ve saat" öneriyor ama yöntemini açıklamıyor. Bizde kural açık: müşterinin ödemelerinin en az %60'ı aynı günün ±1 gün çevresinde toplanıyorsa sabit ödeme günü sayılır ve iletişim o günden 3 gün öncesine önerilir. Örnek veride 40 müşterinin 12'sinde tespit edildi.

## Rakiplerde olmayan, bizde olan

1. **Olasılıksal kasa görünümü.** İncelenen hiçbir ürün sayfasında güven bandı ya da "kasanın eksiye düşme olasılığı" geçmiyor; en yakını Finrota'nın elle kurulan senaryoları.
2. **Tahsilat listesinin kasa açığına bağlanması.** Sıralama "en çok gecikmiş" ya da "en büyük tutar"a göre değil, açık gününe kadar gelmeme riski taşıyan tutara göre.
3. **Çek/senet ve cari hesap mantığı.** Yabancı ürünlerde yok; Finrota sayfasında belirtilmemiş.
4. **Kendini sınayan tahmin.** Geçmiş tarihlerde tahmin üretip gerçekleşenle karşılaştıran geri test kodda var. Panelde "Bu tahmin geçmişte ne kadar tuttu?" bölümünde kullanıcının kendi verisiyle çalışır.

## Rakiplerde olup bizde olmayan (öncelik sırasıyla)

| Eksik | Neden önemli | Engel |
|---|---|---|
| Canlı veri bağlantısı (muhasebe programı, e-fatura entegratörü, banka) | Dosya yükleme düzenli kullanımı öldürür; rakiplerin hepsi bağlantılı çalışıyor | Banka tarafı TCMB lisanslı sağlayıcı gerektirir; e-fatura tarafı entegratör API anlaşması |
| Mesajın gerçekten gönderilmesi (e-posta, sonra WhatsApp) | Taslak üretmek işin yarısı | WhatsApp için Meta onaylı şablon ve çözüm sağlayıcı; hukuki metin kontrolü |
| Yanıtların okunması (itiraz, ödeme sözü) | Upflow'un asıl farkı; elle giriş ölçeklenmez | Gelen kutusu erişimi, dil modeli ve KVKK değerlendirmesi |
| Ödeme bağlantısı | Hatırlatmadan ödemeye geçişi kısaltır | Ödeme kuruluşu ortaklığı |
| Çok kullanıcılı hesap ve yetki | Gerçek üründe zorunlu | Kayıt katmanı eklendi (tek şirket, tek bilgisayar); hesap ve yetki için ayrı bir uygulama katmanı gerekir |

## Kaynaklar

- [Agicap alacak yönetimi](https://agicap.com/en/products/account-receivable/)
- [Upflow AI](https://upflow.io/features/upflow-ai)
- [Chaser özellikler](https://www.chaserhq.com/features)
- [Kolleno özellikler](https://www.kolleno.com/features/)
- [Finrota NAP360](https://www.finrota.com/ozel-cozumler/cash-flow-management-nap360-finrota)

Paraşüt ve Mikro'nun sayfaları özellikleri ayrıntılandırmıyor; bu ikisi için kesin bilgi ancak deneme hesabıyla alınır.
