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
    print("\nBasit yöntemlere karşı (hatalar aylık ciro cinsinden, düşük olan iyi; fark = model eksi yöntem, eksi = model daha iyi):")
    print(s["baselines"].to_string(float_format=lambda v: f"{v:.3f}"))
    print(f"Aralık skoru (%80, Gneiting-Raftery; düşük olan iyi): {s['interval_score']:.3f}")
    st = s["standards"]
    print("")
    print(f"Standart testler: Basel (alt uç) {st['basel_lower']['zone']} ({st['basel_lower']['exceptions']} aşım, "
          f"beklenen {st['basel_lower']['expected']:.0f}); Kupiec p: alt {st['kupiec_lower']['p_value']:.3f}, "
          f"üst {st['kupiec_upper']['p_value']:.3f}, merkezi {st['kupiec_central']['p_value']:.3f}; "
          f"Spiegelhalter p {st['spiegelhalter']['p_value']:.3f} (Brier {st['spiegelhalter']['brier']:.4f})")
    print("\nEksiye düşme olasılığı kalibrasyonu:")
    print(s["reliability"].to_string())
    for name, table in s["by_regime"].items():
        print(f"\n{name} kırılımı:")
        print(table.to_string())
