"""Simülasyon çalışmasını çalıştırır: python run_validation.py [tohum_sayısı]"""
import sys

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd  # noqa: E402

from radar import validation  # noqa: E402

n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 3
df = validation.study(seeds=range(n_seeds))
df.to_csv("data/dogrulama.csv", index=False)
s = validation.summarize(df)
pd.set_option("display.float_format", "{:.2f}".format)

print(f"Şirket sayısı: {s['n']}")
print(f"Dönem sonu kasa P10-P90 bandında: %{s['coverage'] * 100:.0f} (hedef %80)"
      f"  |  bandın altında %{s['below_p10'] * 100:.0f} (hedef %10)  |  üstünde %{s['above_p90'] * 100:.0f} (hedef %10)")
print(f"Beklenen değerin sapması: {s['bias_months']:+.2f} aylık ciro (artı = iyimser)")
print(f"Brier skoru: {s['brier']:.3f}  |  tahminsiz taban: {s['brier_baseline']:.3f} (düşük olan iyi)")
print("\nEksiye düşme olasılığı kalibrasyonu:")
print(s["reliability"].to_string())
for name, table in s["by_regime"].items():
    print(f"\n{name} kırılımı:")
    print(table.to_string())
