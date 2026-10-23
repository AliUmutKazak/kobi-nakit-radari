""""Tahsilat işleri" sekmesi: öncelikli liste, eşleşmeyen tahsilatlar, mesaj taslağı ve bekleyen faturalar."""
import json

import streamlit as st

from radar import actions, ingest, mailer
from radar.reconcile import sender_key
from radar.ui.data import run_impact
from radar.ui.fmt import STAGES, show_table, tl


def render(res, res_key, store, own, seller, record, iban="", bank="", mail=None):
    st.subheader("Öncelikli tahsilat listesi")
    ranked = res["ranked"]
    todo = ranked[ranked["actionable"]].copy()
    todo["payday_label"] = [actions.payday_label(d, w) for d, w in zip(todo["payday"], todo["payweekday"])]
    todo["stage_label"] = todo["stage"].map(STAGES)
    impact = run_impact(res_key, res, tuple(todo["invoice_id"].head(30)))
    todo["impact"] = todo["invoice_id"].astype(str).map(impact)
    show_table(
        todo[["invoice_id", "customer_name", "due_date", "open_amount", "days_overdue", "p_late", "impact", "stage_label",
              "payday_label", "contact_date"]].rename(columns={
            "impact": "Gelmezse en düşük kasa düşüşü (TL)",
            "invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade", "open_amount": "Tutar (TL)",
            "days_overdue": "Gecikme (gün)", "p_late": "Risk", "stage_label": "Aşama",
            "payday_label": "Müşterinin ödeme günü", "contact_date": "Önerilen iletişim tarihi"}),
        help={"Risk": "Kasa açığı oluşmadan önce bu faturanın ödenmemiş olma olasılığı. Liste, tutar × risk'e göre sıralıdır.",
              "Gecikme (gün)": "Vadeden bu yana geçen gün. Eksi değer: vadesine kalan gün.",
              "Aşama": "Hatırlatma: vadesine 7 günden az kaldı. Mutabakat: 1-15 gün gecikmiş. Resmî bildirim: 15 günden fazla.",
              "Müşterinin ödeme günü": "Müşteri ödemelerini düzenli olarak belli bir günde yapıyorsa o gün.",
              "Gelmezse en düşük kasa düşüşü (TL)": "Bu fatura 90 gün içinde hiç gelmezse, kötümser senaryodaki en "
                                                    "düşük kasanın ne kadar azalacağı (listenin ilk 30 faturası için)."},
        width="stretch", hide_index=True)

    conc = actions.concentration(res["obs"])
    if conc["top_share"] >= 0.5:
        st.warning(f"Açık alacağın %{conc['top_share'] * 100:.0f}'i üç müşteride: {', '.join(conc['top_names'])}. "
                   f"Alacak, eşit büyüklükte yalnızca {conc['effective_n']:.1f} müşteriye yayılmış gibi; bu müşterilerden "
                   "birinin gecikmesi kasayı tek başına belirler.")
    unmatched = res.get("unmatched")
    if own and unmatched is not None and len(unmatched):
        with st.expander(f"Eşleşmeyen banka tahsilatları: {len(unmatched)} adet, {tl(unmatched['amount'].sum())}"):
            st.write("Bu girişlerin hangi müşteriden geldiği bulunamadı. Bir kez müşteriye bağlarsanız aynı gönderen "
                     "bundan sonraki ekstrelerde otomatik tanınır.")
            show = unmatched.reset_index(drop=True)
            show_table(show[["date", "amount", "description"]].rename(columns={
                "date": "Tarih", "amount": "Tutar (TL)", "description": "Açıklama"}), width="stretch")
            row = st.number_input("Satır no", 0, len(show) - 1, 0)
            names = res["obs"].drop_duplicates("customer_id").set_index("customer_id")["customer_name"]
            target = st.selectbox("Müşteri", names.index, format_func=lambda c: names[c])
            key = sender_key(show.at[int(row), "description"])
            st.caption(f"Tanınacak gönderen: \"{key}\"")
            if key and st.button("Bu göndereni müşteriye bağla"):
                aliases = json.loads(store.get("sender_aliases", "{}"))
                aliases[key] = str(target)
                store.set("sender_aliases", json.dumps(aliases, ensure_ascii=False))
                st.rerun()

    if own:
        outcomes = actions.message_outcomes(store.events(), res["obs"], res["as_of"])
        if len(outcomes):
            paid14 = (outcomes["Durum"] == "14 gün içinde ödendi").mean()
            with st.expander(f"Gönderilen mesajların sonucu: {len(outcomes)} mesaj, %{paid14 * 100:.0f}'i 14 gün içinde ödendi"):
                st.caption("Bu bir etki ölçümü değildir: mesaj olmasa da ödenecek faturalar da burada görünür. "
                           "Mesajın gerçek etkisi, ancak benzer faturalarla karşılaştırarak ölçülebilir.")
                show_table(outcomes, width="stretch", hide_index=True)

    doubtful = ranked[ranked["stage"] == "supheli"]
    if len(doubtful):
        with st.expander(f"Tahsili zor görünen alacaklar: {len(doubtful)} fatura, {tl(doubtful['open_amount'].sum())}"):
            st.write(f"Bu faturalar {actions.DOUBTFUL_MIN_OVERDUE} günden fazla gecikmiş ve geçmiş verinize göre önümüzdeki "
                     f"90 günde tahsil edilme olasılıkları %{actions.DOUBTFUL_MAX_COLLECT_PROB * 100:.0f}'in altında. "
                     "Hatırlatma listesinde gösterilmezler; yeni bir hatırlatma yerine hukuki yolları değerlendirin.")
            st.caption("Bu, geçmiş verinize dayanan istatistiksel bir sınıflamadır. Vergi bakımından \"şüpheli alacak\" "
                       "sayılması ve karşılık ayrılması ayrı şartlara bağlıdır (VUK m.323: dava veya icra safhasında olmak "
                       "ya da protestoya veya yazıyla birden fazla istenmesine rağmen ödenmemiş olup belirlenen tutarı "
                       "aşmamak). Muhasebe kaydını mali müşavirinizle değerlendirin.")
            show_table(doubtful[["invoice_id", "customer_name", "due_date", "open_amount", "days_overdue", "p_collect"]]
                         .rename(columns={"invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade",
                                          "open_amount": "Tutar (TL)", "days_overdue": "Gecikme (gün)",
                                          "p_collect": "90 günde tahsil olasılığı"}), width="stretch", hide_index=True)
            if own:
                gone = st.selectbox("Tahsil edilemez sayılacak fatura", doubtful["invoice_id"], key="writeoff_pick")
                if st.button("Tahsil edilemez olarak kaydet",
                             help="Fatura açık alacaktan ve kasa tahmininden çıkar; ödenmiş sayılmaz. Yalnızca bu panelin "
                                  "tahminini etkiler, muhasebe kaydı değildir. Şüpheli alacak karşılığı (VUK m.323) ya da "
                                  "değersiz alacak (VUK m.322) kararı mali müşavirinizle verilmelidir. Geri alınabilir."):
                    record(gone, "writeoff", "1")
    if own and "written_off" in res["obs"] and res["obs"]["written_off"].any():
        lost = res["obs"][res["obs"]["written_off"]]
        with st.expander(f"Tahsil edilemez sayılanlar: {len(lost)} fatura, {tl(lost['amount'].sum())}"):
            show_table(lost[["invoice_id", "customer_name", "due_date", "amount"]].rename(columns={
                "invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade", "amount": "Tutar (TL)"}),
                width="stretch", hide_index=True)
            back = st.selectbox("Geri alınacak fatura", lost["invoice_id"], key="writeoff_undo")
            if st.button("Tahsil edilemez kaydını kaldır"):
                record(back, "writeoff", "0")

    st.subheader("Mesaj taslağı")
    if len(todo):
        by_id = todo.set_index("invoice_id", drop=False)
        pick = st.selectbox("Fatura", todo["invoice_id"], format_func=lambda i: f"{i} · {by_id.at[i, 'customer_name']}")
        draft = actions.draft_message(by_id.loc[pick], seller, *((iban, bank) if own else ("", "")))
        body = st.text_area("Taslak (düzenleyebilirsiniz)", draft["body"], height=140, key=f"draft_{pick}")
        identity = actions.sender_identity_problem(seller)
        if identity:
            st.error(identity + " Kimlik tamamlanana kadar gönderme düğmeleri kapalıdır.")
        else:
            with st.expander("Taslağı kopyala"):
                st.caption("Sağ üstteki simgeyle panoya kopyalayıp istediğiniz kanaldan (WhatsApp, SMS, e-posta) gönderin.")
                st.code(body, language=None, wrap_lines=True)
        st.warning(actions.FORMAL_NOTICE_WARNING)
        if draft["note"]:
            st.info(draft["note"])
        if own:
            st.caption("Mesajı kendi e-posta ya da WhatsApp hesabınızdan gönderdikten sonra aşağıdan kayda geçirin. "
                       f"Kayda geçen fatura {actions.CONTACT_COOLDOWN_DAYS} gün boyunca listede yeniden önerilmez.")
            owner = st.text_input("Takipten sorumlu kişi (isteğe bağlı)", store.get("last_owner", ""), key=f"owner_{pick}",
                                  help="Kayda yazılır; birden çok kişi tahsilat yapıyorsa kimin takip ettiği görünür.")
            tag = f"[sorumlu: {owner.strip()}] " if owner.strip() else ""
            if owner.strip():
                store.set("last_owner", owner.strip())
            phones = res["obs"].set_index("invoice_id")["phone"] if "phone" in res["obs"] else {}
            phone = ingest.normalize_phone(st.text_input("Müşterinin cep telefonu (WhatsApp)", phones.get(pick, ""),
                                                         key=f"tel_{pick}", placeholder="05XX XXX XX XX"))
            if phone and not identity:
                st.link_button("WhatsApp'ta taslağı aç", actions.whatsapp_link(phone, body))
                st.caption("WhatsApp kendi hesabınızda, mesaj yazılmış hâlde açılır; gönderdikten sonra aşağıdan kayda geçirin.")
            if mail.ready:
                emails = res["obs"].set_index("invoice_id")["email"] if "email" in res["obs"] else {}
                to = st.text_input("Alıcı e-posta adresi", emails.get(pick, ""), key=f"to_{pick}")
                if st.button("E-posta ile gönder", disabled=not mailer.is_address(to) or bool(identity)):
                    try:
                        mailer.send(mail, to, draft["subject"], body)
                    except mailer.MailError as err:
                        st.error(str(err))
                    else:
                        record(pick, "message", f"{tag}[e-posta: {to.strip()}] {body}")
            b1, b2, b3 = st.columns(3)
            if b1.button("Gönderildi olarak kaydet"):
                record(pick, "message", tag + body)
            if b2.button("Müşteri itiraz etti"):
                record(pick, "dispute", "1")
            promise = b3.date_input("Ödeme sözü tarihi", value=None, format="DD.MM.YYYY", key=f"promise_{pick}")
            if promise and b3.button("Ödeme sözünü kaydet"):
                record(pick, "promise", str(promise))
    else:
        st.write("Şu an hatırlatma gerektiren fatura yok.")

    if own:
        obs = res["obs"]
        held = obs[(obs["open_amount"] > 0) & (obs["disputed"] | (obs["promised_date"] > res["as_of"]))]
        waiting = ranked[ranked["last_contact"].notna() & ~ranked["actionable"]]
        with st.expander(f"Beklemedeki faturalar ({len(held) + len(waiting)})"):
            if len(held):
                st.write("İtirazlı ya da ödeme sözü verilmiş faturalar:")
                show_table(held[["invoice_id", "customer_name", "open_amount", "disputed", "promised_date"]].rename(columns={
                    "invoice_id": "Fatura", "customer_name": "Müşteri", "open_amount": "Tutar (TL)",
                    "disputed": "İtirazlı", "promised_date": "Ödeme sözü"}), width="stretch", hide_index=True)
                undo = st.selectbox("Durumu kaldırılacak fatura", held["invoice_id"])
                u1, u2 = st.columns(2)
                if u1.button("İtirazı kaldır"):
                    record(undo, "dispute", "0")
                if u2.button("Ödeme sözünü kaldır"):
                    record(undo, "promise", "")
            if len(waiting):
                st.write("Yakın zamanda yazılmış, yanıt beklenen faturalar:")
                show_table(waiting[["invoice_id", "customer_name", "open_amount", "last_contact"]].rename(columns={
                    "invoice_id": "Fatura", "customer_name": "Müşteri", "open_amount": "Tutar (TL)",
                    "last_contact": "Son iletişim"}), width="stretch", hide_index=True)
            if not len(held) and not len(waiting):
                st.write("Beklemede fatura yok.")
