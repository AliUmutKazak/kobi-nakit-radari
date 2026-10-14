"""Simülasyon çalışmasını çalıştırır: python run_validation.py [tohum_sayısı]"""
import sys

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd  # noqa: E402

from radar import validation  # noqa: E402

if __name__ == "__main__":
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    df = validation.study(seeds=range(n_seeds))
    df.to_csv("data/dogrulama.csv", index=False)
    s = validation.summarize(df)
    pd.set_option("display.float_format", "{:.2f}".format)
    pd.set_option("display.width", 200)

    print(f"Bağımsız tahmin sayısı: {s['n_cases']}  (üç açılış kasasıyla {s['n_rows']} şirket durumu)")
    print(f"Dönem sonu kasa P10-P90 bandında: {s['coverage']} (hedef %80)"
          f"  |  altında {s['below_p10']} (hedef %10)  |  üstünde {s['above_p90']} (hedef %10)")
    print(f"Beklenen değerin sapması: {s['bias_months']} aylık ciro (artı = iyimser)")
    print(f"Brier skoru: {s['brier']:.3f}  |  tahminsiz taban: {s['brier_baseline']:.3f} (düşük olan iyi)")
    print("\nEksiye düşme olasılığı kalibrasyonu:")
    print(s["reliability"].to_string())
    for name, table in s["by_regime"].items():
        print(f"\n{name} kırılımı:")
        print(table.to_string())
