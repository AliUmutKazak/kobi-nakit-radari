"""Tahsilat önceliklendirme, mesaj taslakları ve temel alacak metrikleri.

Mesajlar yalnızca TASLAKTIR; hiçbir şey kullanıcı onayı olmadan gönderilmez. Resmî
bildirim tonundaki taslaklar ayrıca hukukçu kontrolü notu taşır.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .features import MONTH_END, next_payday, payday_habit

# TTK m.1530/7 uyarınca TCMB'nin her yıl ocak ayında ilan ettiği değerler. 2026: yıllık %43,00 ve 2.020,00 TL,
# 1.1.2026'dan geçerli (TCMB Tebliği, Resmî Gazete 02.01.2026, sayı 33125; metinden doğrulandı 18.10.2026).
# Avukat şerhi gereği mesaj metinlerine yazılmaz; her ocakta güncellenmelidir.
LATE_INTEREST_RATE = 0.43
MIN_RECOVERY_COST_TL = 2020
# Aynı fatura için yeni hatırlatma önermeden önce beklenen süre.
CONTACT_COOLDOWN_DAYS = 7
# 90 günden fazla gecikmiş ve simülasyonda ufuk içinde tahsil olasılığı bunun altında kalan fatura
# "tahsili zor" sayılır: hatırlatma listesine girmez, ayrı gösterilir. Eşik bir iş kuralıdır; vergi bakımından
# şüpheli alacak (VUK m.323) ayrı şartlara bağlıdır ve panelde bu ayrım açıkça yazılır.
DOUBTFUL_MIN_OVERDUE = 90
DOUBTFUL_MAX_COLLECT_PROB = 0.15


def metrics(obs: pd.DataFrame, as_of) -> dict:
    as_of = pd.Timestamp(as_of)
    open_inv = obs[obs["open_amount"] > 0]
    overdue = open_inv[open_inv["due_date"] < as_of]
    sales_90 = obs.loc[obs["issue_date"] > as_of - pd.Timedelta(days=90), "amount"].sum()
    paid = obs[obs["paid_date"] > as_of - pd.Timedelta(days=180)]
    dbt = (paid["paid_date"] - paid["due_date"]).dt.days
    # Gecikme eğilimi: son 90 günde yapılan ödemelerin medyan gecikmesi, önceki 90 güne göre kaç gün uzadı.
    recent = dbt[paid["paid_date"] > as_of - pd.Timedelta(days=90)]
    before = dbt[paid["paid_date"] <= as_of - pd.Timedelta(days=90)]
    trend = float(recent.median() - before.median()) if len(recent) >= 20 and len(before) >= 20 else 0.0
    return {
        "delay_trend_days": trend,
        "open_ar": float(open_inv["open_amount"].sum()),
        "overdue_ar": float(overdue["open_amount"].sum()),
        "dso": float(open_inv["open_amount"].sum() / sales_90 * 90) if sales_90 else float("nan"),
        "avg_days_beyond_terms": float(np.average(dbt, weights=paid["amount"])) if len(paid) else float("nan"),
        "on_time_rate": float((dbt <= 0).mean()) if len(paid) else float("nan"),
        # TTK m.1530/5: alacaklı KOBİ ise ya da borçlu büyük işletmeyse vade 60 günü aşamaz.
        "over_60_terms": int(((open_inv["due_date"] - open_inv["issue_date"]).dt.days > 60).sum()),
    }


def message_outcomes(events: pd.DataFrame, obs: pd.DataFrame, as_of, window: int = 14) -> pd.DataFrame:
    """Kayda geçirilen her mesajdan sonra fatura ödendi mi, kaç günde? Kontrol grubu olmadığı için
    bu bir etki ölçümü değil, takip listesidir: mesaj olmasa da ödenecek olanlar da burada görünür."""
    msgs = events[events["kind"] == "message"].drop_duplicates("invoice_id", keep="last")
    if msgs.empty:
        return pd.DataFrame()
    inv = obs.drop_duplicates("invoice_id").set_index("invoice_id")
    msgs = msgs[msgs["invoice_id"].isin(inv.index)]
    paid = inv.loc[msgs["invoice_id"], "paid_date"].to_numpy()
    sent = msgs["ts"].dt.normalize().to_numpy()
    days = (pd.to_datetime(paid) - pd.to_datetime(sent)).days
    return pd.DataFrame({
        "Fatura": msgs["invoice_id"].to_numpy(), "Müşteri": inv.loc[msgs["invoice_id"], "customer_name"].to_numpy(),
        "Mesaj tarihi": pd.to_datetime(sent), "Ödeme tarihi": pd.to_datetime(paid),
        "Mesajdan sonra (gün)": days,
        "Durum": np.where(pd.isna(paid), np.where((pd.Timestamp(as_of) - pd.to_datetime(sent)).days > window,
                                                  f"{window} günden uzun süredir açık", "Bekleniyor"),
                          np.where(days <= window, f"{window} gün içinde ödendi", "Geç ödendi")),
    })


def concentration(obs: pd.DataFrame, top: int = 3) -> dict:
    """Açık alacağın müşterilere dağılımı. Herfindahl-Hirschman endeksi (paylar karesi toplamı) ve
    "eşdeğer müşteri sayısı" (1 / HHI): alacak, eşit büyüklükte kaç müşteriye yayılmış gibi davranıyor."""
    open_by = obs.loc[obs["open_amount"] > 0].groupby("customer_name")["open_amount"].sum().sort_values(ascending=False)
    total = open_by.sum()
    if total <= 0:
        return {"top_share": 0.0, "top_names": [], "hhi": 0.0, "effective_n": 0.0}
    share = open_by / total
    hhi = float((share ** 2).sum())
    return {"top_share": float(share.head(top).sum()), "top_names": list(share.head(top).index),
            "hhi": hhi, "effective_n": 1 / hhi}


def payment_habits(obs: pd.DataFrame) -> pd.DataFrame:
    """Müşteri bazında sabit ödeme günü (0 = yok) ve vadesinde ödeme oranı."""
    paid = obs.dropna(subset=["paid_date"])
    rows = {}
    for cid, g in paid.groupby("customer_id"):
        d = g["paid_date"]
        rows[cid] = {"payday": payday_habit(d.dt.day.to_numpy(), (d.dt.days_in_month - d.dt.day).to_numpy()),
                     "payweekday": weekday_habit(d.dt.dayofweek.to_numpy()),
                     "cust_on_time": float((d <= g["due_date"]).mean()), "cust_n_paid": len(g)}
    return pd.DataFrame.from_dict(rows, orient="index", columns=["payday", "payweekday", "cust_on_time", "cust_n_paid"])


WEEKDAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def weekday_habit(weekdays, min_n: int = 6, share: float = 0.6) -> int:
    """Haftanın sabit bir gününde (ör. Cuma ödeme listesi) ödeme alışkanlığı: -1 = yok, 0-6 = gün.

    Rastgele ödemede her gün ~%20 pay alır (hafta içi); %60 eşiği bunun üç katıdır."""
    weekdays = np.asarray(weekdays, int)
    if len(weekdays) < min_n:
        return -1
    counts = np.bincount(weekdays, minlength=7)
    day = int(np.argmax(counts))
    return day if counts[day] / len(weekdays) >= share else -1


def prioritize(open_inv: pd.DataFrame, pay_day: np.ndarray, as_of, gap_day: int,
               habits: pd.DataFrame | None = None, horizon: int = 90) -> pd.DataFrame:
    """Faturaları "açık gününe kadar tahsil edilememe riski taşıyan tutar"a göre sıralar."""
    as_of = pd.Timestamp(as_of)
    df = open_inv[["invoice_id", "customer_id", "customer_name", "due_date", "open_amount"]].copy()
    promised = open_inv["promised_date"] if "promised_date" in open_inv else pd.Series(pd.NaT, index=df.index)
    df["promised_date"] = promised.where(promised > as_of)
    df["days_overdue"] = (as_of - df["due_date"]).dt.days
    df["p_late"] = (pay_day > gap_day).mean(axis=1)
    df["p_collect"] = (pay_day <= horizon).mean(axis=1)
    df["expected_pay_day"] = np.median(pay_day, axis=1)
    df["amount_at_risk"] = df["open_amount"] * df["p_late"]
    df["stage"] = pd.cut(df["days_overdue"], [-np.inf, -8, 0, 15, np.inf],
                         labels=["bekle", "hatirlatma", "mutabakat", "resmi"]).astype(str)
    doubtful = (df["days_overdue"] > DOUBTFUL_MIN_OVERDUE) & (df["p_collect"] < DOUBTFUL_MAX_COLLECT_PROB)
    df.loc[doubtful, "stage"] = "supheli"
    df.loc[df["promised_date"].notna(), "stage"] = "soz"      # söz tarihi geçene kadar hatırlatma yok
    # Vadesine bir haftadan fazla olan faturalar için hatırlatma işe yaramaz; listede sona alınır.
    last = open_inv["last_contact"] if "last_contact" in open_inv else pd.Series(pd.NaT, index=df.index)
    df["last_contact"] = pd.to_datetime(last)
    contacted = (as_of - df["last_contact"]).dt.days < CONTACT_COOLDOWN_DAYS
    df["actionable"] = ~df["stage"].isin(["bekle", "soz", "supheli"]) & ~contacted
    if habits is not None and len(habits):
        df = df.join(habits, on="customer_id")
    for col, default in (("payday", 0), ("payweekday", -1), ("cust_on_time", np.nan), ("cust_n_paid", 0)):
        df[col] = df[col].fillna(default) if col in df else default
    # Sabit ödeme günü olan müşteriye, o günden 3 gün önce ulaşmak ödeme listesine girmeyi sağlar.
    today, lead = np.datetime64(as_of.date()), np.timedelta64(3, "D")
    def contact(day_habit, week_habit):
        if day_habit:
            return pd.Timestamp(max(today, next_payday(today + lead, int(day_habit)) - lead))
        if week_habit >= 0:          # haftalık ödeme listesinden 2 gün önce
            ahead = (int(week_habit) - (as_of + pd.Timedelta(days=2)).dayofweek) % 7
            return as_of + pd.Timedelta(days=ahead)
        return as_of
    df["contact_date"] = [contact(h, w) for h, w in zip(df["payday"], df["payweekday"])]
    return df.sort_values(["actionable", "amount_at_risk"], ascending=False).reset_index(drop=True)


def _tl(x: float) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def payday_label(habit: int, weekday: int = -1) -> str:
    if habit:
        return "ay sonu" if habit == MONTH_END else f"ayın {int(habit)}. günü"
    return f"her {WEEKDAYS[int(weekday)]}" if weekday is not None and weekday >= 0 else ""


def whatsapp_link(phone: str, text: str) -> str:
    """Tıklanınca kullanıcının kendi WhatsApp'ında taslak hazır bir sohbet açan bağlantı.
    Gönderme işini kullanıcı yapar; API ya da Meta şablon onayı gerekmez."""
    from urllib.parse import quote
    return f"https://wa.me/{phone}?text={quote(text)}"


def payment_line(invoice_id: str, iban: str = "", bank: str = "") -> str:
    """Ödeme bilgisi. Açıklamaya fatura numarasının yazılmasını istemek, gelen paranın faturayla
    banka ekstresinde otomatik eşleşmesini sağlar."""
    if not iban:
        return ""
    where = f"{iban} ({bank})" if bank else iban
    return f" Ödemeyi {where} hesabımıza, açıklamaya {invoice_id} yazarak yapabilirsiniz."


def sender_identity_problem(seller: str) -> str | None:
    """Gönderen kimliği eksikse açıklaması, tamamsa None.

    Ticari İletişim ve Ticari Elektronik İletiler Hakkında Yönetmelik m.8/2-3: iletinin başlığında ya da içeriğinde
    tacirler için ticaret unvanı ve MERSİS numarası, esnaflar için adı soyadı ile T.C. kimlik ya da vergi kimlik
    numarası yer alır. Borç hatırlatma ve tahsilat iletileri önceden onay gerektirmez (m.6/2), ama kimlik kuralı
    ticari elektronik iletilerin tümüne uygulanır. Rakamlar 16 hane (MERSİS) ya da 10/11 hane (VKN/TCKN) olmalıdır."""
    text = str(seller or "")
    numbers = [re.sub(r"\D", "", n) for n in re.findall(r"\d[\d .-]{8,}\d", text)]
    letters = re.sub(r"[^A-Za-zÇĞİÖŞÜçğıöşü]", "", re.sub(r"(?i)mersis|vkn|tckn|t\.c\.", "", text))
    if len(letters) < 3:
        return "Mesaj imzasında ticaret unvanı ya da ad soyad yok."
    if any(len(n) == 16 for n in numbers) or any(len(n) in (10, 11) for n in numbers):
        return None
    return ("Mesaj imzasında MERSİS numarası (tacirler) ya da T.C. kimlik / vergi kimlik numarası (esnaf) yok. Ticari "
            "İletişim ve Ticari Elektronik İletiler Hakkında Yönetmelik m.8 gereği ileti bu bilgiyi içermelidir. "
            "Sol menüde \"4. Mesaj ayarları > İmza\" alanını tamamlayın.")


# Avukat şerhi (15.10.2026): her mesaj taslağının yanında sabit olarak gösterilir.
FORMAL_NOTICE_WARNING = ("Bu ileti TTK m. 18/3 kapsamında resmi ihtarname yerine geçmez; dava/icra öncesi KEP veya "
                         "Noter kullanılmalıdır.")


_COMPANY = re.compile(r"(\bA\.\s?Ş\b|\bAŞ\b|\bANON[İI]M\b|\bLTD\b|\bL[İI]M[İI]TED\b|\bŞT[İI]\b|\bSTI\b|\bKOLL\b"
                      r"|\bKOMAND[İI]T\b|\bKOOP\b|\bKOOPERAT[İI]F\b)", re.I)


def is_business(row) -> bool:
    """Müşterinin ticari işletme olduğu kayıttan anlaşılıyor mu: 10 haneli VKN ya da unvanda şirket türü.

    TTK m.1530 yalnızca ticari işletmeler arasındaki mal ve hizmet tedarikinde uygulanır. 11 haneli TCKN'li
    müşteri şahıs işletmesi (tacir) de tüketici de olabilir; bu kayıttan ayırt edilemez."""
    vkn = str(row.get("vkn") or "").strip()
    return (len(vkn) == 10 and vkn.isdigit()) or bool(_COMPANY.search(str(row.get("customer_name") or "")))


def draft_message(row, seller: str, iban: str = "", bank: str = "") -> dict | None:
    """Aşamaya göre WhatsApp/e-posta taslağı üretir. Tanıtım içeriği eklenmez.

    `seller` gönderenin ticaret unvanıdır (varsa MERSİS numarasıyla); ticari iletilerde
    gönderenin kimliğinin açıkça belirtilmesi gerekir."""
    pay = payment_line(row["invoice_id"], iban, bank)
    already = " Ödemeyi yaptıysanız bu mesajı dikkate almayınız."
    due, amount = pd.Timestamp(row["due_date"]).strftime("%d.%m.%Y"), _tl(row["open_amount"])
    ref = f"{row['invoice_id']} numaralı, {amount} tutarındaki faturamız"
    if row["stage"] in ("bekle", "soz", "supheli"):
        return None
    if row["stage"] == "hatirlatma":
        habit = (" Bugüne kadarki ödemelerinizin büyük bölümünü vadesinde yaptığınız için teşekkür ederiz."
                 if row.get("cust_n_paid", 0) >= 5 and row.get("cust_on_time", 0) >= 0.7 else "")
        body = (f"Merhaba, {ref} için vade tarihi {due}.{habit} "
                f"Ödeme planınızda bir değişiklik varsa bize bildirmeniz yeterli.{pay}{already} {seller}")
        note = None
    elif row["stage"] == "mutabakat":
        body = (f"Merhaba, {ref} {due} tarihinde vadesini doldurdu ve kayıtlarımızda açık görünüyor. "
                f"Ödeme yapıldıysa dekontu, eksik bir belge (irsaliye, sipariş onayı) varsa bilgisini "
                f"paylaşabilir misiniz? Kayıtlarımızı birlikte kontrol edelim.{pay} {seller}")
        note = None
    elif is_business(row):
        body = (f"Sayın yetkili, aramızdaki mal/hizmet tedariki kapsamında düzenlenen {ref} {due} tarihli vadesi "
                f"dolmuş olup {int(row['days_overdue'])} gündür kayıtlarımızda açık görünmektedir. "
                f"Türk Ticaret Kanunu m.1530 uyarınca ticari işletmeler arasındaki mal ve hizmet tedariklerinde ödeme "
                f"süresinin aşılmasıyla ihtara gerek olmaksızın temerrüt hükümleri doğmaktadır. TCMB tarafından ilan "
                f"edilen temerrüt faizi ve alacağın tahsili masrafları için asgari giderim tutarı ile kısmi ödemelerde "
                f"kalan bakiye dahil tüm yasal ve sözleşmesel haklarımız saklıdır. Bakiyenin ödenmesini "
                f"ya da ödeme yapıldıysa dekontun paylaşılmasını rica ederiz.{pay} {seller}")
        # Avukat şerhi (15.10.2026): metinde sabit oran ve tutar yazılmaz, "TCMB tarafından ilan edilen" denir.
        # Terim TTK m.1530/7'deki ifadeye çekildi ("asgari giderim tutarı", 18.10.2026).
        note = ("Göndermeden önce teslimin (irsaliye) belgelendiğini ve sözleşme koşullarını kontrol edin.")
    else:
        body = (f"Sayın ilgili, {ref} {due} tarihinde vadesini doldurmuş olup {int(row['days_overdue'])} gündür "
                f"kayıtlarımızda açık görünmektedir. Bakiyenin ödenmesini ya da ödeme yapıldıysa dekontun "
                f"paylaşılmasını rica ederiz. Yasal ve sözleşmesel haklarımız saklıdır.{pay} {seller}")
        note = ("Müşterinin ticari işletme olduğu kayıttan anlaşılamadı (10 haneli VKN ya da şirket unvanı yok). TTK m.1530 "
                "yalnızca ticari işletmeler arasındaki mal ve hizmet tedariklerinde uygulanır; müşteri tüketiciyse 6502 "
                "sayılı Tüketicinin Korunması Hakkında Kanun geçerlidir. Bu yüzden taslakta kanun maddesine ve temerrüt "
                "faizine atıf yapılmadı. Göndermeden önce teslimin belgelendiğini kontrol edin; gerekirse hukukçunuza danışın.")
    return {"invoice_id": row["invoice_id"], "customer_name": row["customer_name"], "stage": row["stage"],
            "subject": (f"Vade hatırlatma ve TTK m. 1530 bilgilendirmesi: {row['invoice_id']}"
                        if row["stage"] == "resmi" and is_business(row) else
                        f"Vadesi geçmiş fatura hakkında: {row['invoice_id']}" if row["stage"] == "resmi"
                        else f"{row['invoice_id']} numaralı fatura hakkında"), "body": body,
            "requires_approval": True, "note": note}
