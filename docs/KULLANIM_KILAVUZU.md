# KOBİ Nakit Akışı Radarı: Kullanım Kılavuzu

Bu kılavuz, kod bilgisi gerektirmeden paneli kurup kendi verinizle kullanmanız içindir.

## Panel size ne söyler

- Önümüzdeki 90 günde kasanızın ne olacağını, tek bir çizgi olarak değil **bir aralık** olarak gösterir: kötümser, beklenen ve iyimser durum.
- Kasanın bu dönemde eksiye düşme olasılığını ve kötümser durumda hangi gün düşeceğini söyler.
- Açığı kapatmak için hangi faturaları önce tahsil etmeniz gerektiğini sıralar ve müşteriye gönderilecek mesajın taslağını hazırlar.

Tahminler müşterilerinizin geçmişte nasıl ödediğine dayanır. Geçmiş ne kadar uzunsa tahmin o kadar kişiseldir; 1–2 yıllık fatura geçmişi idealdir.

## 1. Kurulum (bir kez)

1. **Python'u kurun.** python.org adresinden Python 3.13'ü indirin. Kurulumun ilk ekranında **"Add python.exe to PATH"** kutusunu işaretleyin.
2. **Paneli başlatın.** Proje klasöründeki **`KOBI_Radar_Baslat.bat`** dosyasına çift tıklayın. İlk açılışta gerekli programlar internetten kurulur; birkaç dakika sürer. Sonraki açılışlar birkaç saniyedir.
3. Panel hazır olunca tarayıcınızda kendiliğinden açılır (adres: http://127.0.0.1:8501).

Paneli kapatmak için siyah pencereyi kapatın. Panel yalnızca sizin bilgisayarınızdan açılabilir; ağdaki başka bir cihaz bağlanamaz.

Panel açıkken dosyaya yeniden tıklarsanız ikinci bir panel başlatılmaz, açık olan tarayıcıda gösterilir. Tarayıcı kendiliğinden açılmazsa siyah pencerede yazan adresi (http://127.0.0.1:8501) tarayıcıya yazın. Siyah pencere kapanmadan önce bir hata mesajı gösterirse o pencerenin ekran görüntüsünü saklayın.

## 2. Önce demo ile tanışın

Sol menüde **"Demo şirket"** seçiliyken panel uydurma bir şirketin verisini gösterir. Sekmeleri gezerek neyin nerede olduğunu görün; hiçbir şey kaydedilmez.

## 3. Kendi verinizi yükleyin

Sol menüde **"Kendi verim"**i seçin.

**Bugünün tarihi ve kasa.** Bugünün tarihini ve kasa + bankadaki toplam paranızı girin.

**Satışlarınız (zorunlu).** Aşağıdakilerden **birini** yükleyin:

| Seçenek | Muhasebe programından nasıl alınır (örnek) |
|---|---|
| Satış faturası listesi | Programınızın satış faturaları ekranında "Excel'e aktar" |
| Cari hesap ekstresi / cari hareket föyü / muavin defter | Borç ve Alacak sütunlu ekstre; faturalar ve tahsilatlar tek dosyada gelir |
| e-Fatura XML dosyaları | Entegratörünüzün portalından indirilen XML'ler |

Fatura listesinde en az **fatura no, müşteri, fatura tarihi, tutar** olmalı. Vade tarihi, VKN, kalan tutar, e-posta ve telefon sütunları varsa kullanılır. Panel sütun adlarını tanıyamazsa her alan için dosyanızdaki karşılığını sorar; seçiminizi hatırlar.

**İsteğe bağlı dosyalar:**

| Dosya | Ne işe yarar |
|---|---|
| Banka ekstresi | Hangi faturanın ödendiğini otomatik bulur. Fatura listesinde ödeme bilgisi yoksa gereklidir. |
| Planlı giderler | Maaş, kira, kredi taksidi gibi çıkışlar. Yoksa "aylık sabit giderler" kutusuna tutarları yazın; panel vergi takvimine göre yerleştirir. |
| Ödenecek faturalar | Tedarikçilere borçlarınız ve vadeleri. |
| Çek / senet portföyü | Elinizdeki müşteri çekleri ve vadeleri. "Durum" sütununda ciro edildi / iskonto yazanlar hesaba katılmaz. |

Biçimi görmek için panelin ilk ekranında örnek dosyaları indirebilirsiniz. Yüklediğiniz her şey yalnızca bu bilgisayarda saklanır; bir sonraki açılışta yeniden yüklemeniz gerekmez.

**Dövizli faturalar.** Döviz kurunu ilgili kutuya yazın (ör. `USD=41,50; EUR=48,20`). Kuru girilmeyen döviz tahmine katılmaz.

## 4. Paneli okumak

**Üst satır.** Kasa, açık alacak, vadesi geçmiş alacak, DSO (alacakların ortalama kaç günde tahsil edildiği) ve 90 günde kasanın eksiye düşme olasılığı.

**"Kasa tahmini" sekmesi.**
- Mavi bant, kasanızın %80 olasılıkla içinde kalacağı aralıktır; ortadaki çizgi beklenen durumdur. Kırmızı kesikli çizgi sıfırdır.
- **"Açığı kapatmak için ne gerekir?"** bölümü, kötümser durumdaki en derin açığı ve onu kapatmak için listenin ilk kaç faturasının bu hafta tahsil edilmesi gerektiğini söyler.
- Kaydırma çubuklarıyla "şu kadar fatura tahsil edilirse" ya da "şu gideri şu kadar ertelersem" senaryolarını deneyebilirsiniz.

**"Tahsilat işleri" sekmesi.**
- **Öncelikli tahsilat listesi:** en üstteki fatura, açığınız açısından en riskli olandır. Müşterinin sabit bir ödeme günü varsa (ör. "ayın 15'i", "her Cuma") panel ona göre iletişim tarihi önerir.
- **Mesaj taslağı:** faturayı seçin, taslağı düzenleyin. Müşterinin cep telefonunu girerseniz "WhatsApp'ta taslağı aç" düğmesi mesajı kendi WhatsApp'ınızda yazılmış hâlde açar; gönderme düğmesine siz basarsınız.
- Gönderdikten sonra **"Gönderildi olarak kaydet"** deyin. O fatura 7 gün listede yeniden önerilmez.
- Müşteri itiraz ettiyse ya da ödeme sözü verdiyse ilgili düğmelerle kaydedin; söz tarihi geçene kadar hatırlatma önerilmez.
- **Eşleşmeyen banka tahsilatları:** kimden geldiği bulunamayan paraları bir kez müşteriye bağlarsanız aynı gönderen sonraki ekstrelerde otomatik tanınır.
- **Şüpheli alacaklar:** çok gecikmiş ve tahsil edilme olasılığı düşük faturalar ayrı gösterilir. Bunlar için hatırlatma yerine hukuki yolları değerlendirin.

**"Tahmin doğruluğu" sekmesi.** Panel geçmişteki birkaç tarihe dönüp "o gün tahmin etseydim ne kadar tutardı" diye kendini sınar. En az 9 aylık geçmiş gerekir.

## 5. Mesajlar hakkında bilmeniz gerekenler

- Panel hiçbir mesajı kendiliğinden göndermez. E-posta gönderimi için kenar çubuğuna kendi e-posta hesabınızın bilgilerini girmeniz gerekir (Gmail ve Outlook'ta "uygulama parolası"). Parola kaydedilmez.
- Mesajlarda kampanya, indirim ya da ürün tanıtımı olmamalıdır; olursa ticari ileti izni kurallarına takılır. Taslaklar buna göre yazılmıştır.
- "Resmî bildirim" aşamasındaki metin **ihtarname değildir**. Türk Ticaret Kanunu'na göre tacirler arasında temerrüt ihtarı noter, taahhütlü mektup, telgraf ya da KEP (güvenli elektronik imzalı) ile yapılmalıdır.
- Panele tahsilat IBAN'ınızı girerseniz taslaklara "açıklamaya fatura numarasını yazın" talimatı eklenir. Müşteri buna uyarsa gelen para banka ekstresinde otomatik olarak doğru faturayla eşleşir.

## 6. Tahminin sınırları

- Tahmin müşterilerinizin geçmişteki davranışına dayanır. Gecikmeler hızla artıyorsa tahmin iyimser kalabilir; panel bu durumu fark ettiğinde uyarır, o zaman kötümser çizgiyi esas alın.
- Alacağınız birkaç müşteride toplanmışsa (panel bunu da uyarır), tek bir müşterinin gecikmesi sonucu tek başına belirler.
- Kur değişimi, yeni kredi, beklenmedik büyük giderler tahmine dahil değildir.
- Verileriniz bu bilgisayardaki şifrelenmemiş bir dosyada durur (yeri kenar çubuğunda yazar). Bilgisayarınızın Windows parolasını ve disk şifrelemesini açık tutun, dosyayı düzenli yedekleyin.
