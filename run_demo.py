"""Sentetik veriyle uçtan uca çalıştırma ve geri test özeti: python run_demo.py"""
import sys

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")

from radar import actions, pipeline  # noqa: E402

AS_OF = "2026-10-01"
res = pipeline.demo(as_of=AS_OF)
sim, m = res["sim"], res["metrics"]

print(f"Fatura sayısı: {len(res['obs'])}  |  açık fatura: {(res['obs']['open_amount'] > 0).sum()}")
print(f"Açık alacak: {m['open_ar']:,.0f} TL  |  vadesi geçmiş: {m['overdue_ar']:,.0f} TL  |  DSO: {m['dso']:.0f} gün")
print(f"Açılış kasası: {res['opening']:,.0f} TL")
print(f"90 günde kasanın eksiye düşme olasılığı: %{sim.prob_any_breach * 100:.0f}")
print("Kötümser bant (P10) sıfırı kesiyor: " + (f"{sim.breach_day}. gün" if sim.breach_day else "kesmiyor"))
for d in (30, 60, 90):
    print(f"  {d}. gün  P10 {sim.p10[d]:>12,.0f}   P50 {sim.p50[d]:>12,.0f}   P90 {sim.p90[d]:>12,.0f}")

print("\nÖncelikli 5 fatura:")
print(res["ranked"].head(5)[["invoice_id", "customer_name", "open_amount", "days_overdue", "p_late", "stage"]]
      .to_string(index=False))
print(f"Sabit ödeme günü tespit edilen müşteri: {(res['ranked'].drop_duplicates('customer_id')['payday'] > 0).sum()}")
draft = next(filter(None, (actions.draft_message(r, "Örnek Ticaret A.Ş.") for _, r in res["ranked"].iterrows())))
print(f"\nÖrnek taslak ({draft['stage']}):\n{draft['body']}")

print("\nModel geri testi (eğitimde görülmemiş dönem):")
bt = pipeline.backtest_model(res["full"], AS_OF)
print(f"  n={bt['n']}  MAE model {bt['mae_model']:.1f} gün  |  MAE müşteri medyanı {bt['mae_baseline']:.1f} gün"
      f"  |  P10-P90 kapsama %{bt['coverage_p10_p90'] * 100:.0f} (hedef %80)")

print("\nTahsilat geri testi (90 günlük gerçekleşen / tahmin bandı):")
print(pipeline.backtest_collections(res["full"], AS_OF).round(0).to_string(index=False))
