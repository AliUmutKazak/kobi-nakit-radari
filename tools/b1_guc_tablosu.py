"""B1 ölçütünün gücü: model gerçekten kötüyken Diebold-Mariano testi bunu ne sıklıkla yakalar (protokol 1.7).

Bu yeni bir test değil; mevcut testin (standards.diebold_mariano) pilotun kayıt sayısıyla ne kadar kanıt
üretebileceğinin beyanıdır. Kurgu, dış inceleme raporundakiyle aynı (21.10.2026):
- haftalık kayıtlar, ufuk kadar üst üste biner: 14 günde 2, 30 günde 5 hafta (MA(q-1) hata);
- model ile en iyi basit yöntemin hataları arasında 0,7 korelasyon;
- modelin hata ölçeği basit yöntemin 1; 1,2; 1,5 ve 2 katı;
- kayıp mutlak hatadır; 4.000 tekrar; anlamlılık %5 (tek yönlü, "model kötü").

Kullanım: python tools/b1_guc_tablosu.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from radar.standards import SIGNIFICANCE, diebold_mariano  # noqa: E402

RHO, REPS = 0.7, 4000


def errors(rng, n: int, q: int, scale: float) -> tuple[np.ndarray, np.ndarray]:
    z = rng.standard_normal((2, n + q - 1))
    z[1] = RHO * z[0] + np.sqrt(1 - RHO ** 2) * z[1]
    ma = lambda x: np.convolve(x, np.ones(q) / np.sqrt(q), mode="valid")   # MA(q-1): q hafta üst üste
    return np.abs(scale * ma(z[1])), np.abs(ma(z[0]))


def power(n: int, h: int, scale: float, seed: int = 0) -> float:
    rng, q = np.random.default_rng(seed), int(np.ceil(h / 7))
    hits = 0
    for _ in range(REPS):
        model, bench = errors(rng, n, q, scale)
        hits += diebold_mariano(model, bench, overlap=q)["p_worse"] < SIGNIFICANCE
    return hits / REPS


if __name__ == "__main__":
    print("| Kayıt | Ufuk | Model eşit | %20 kötü | %50 kötü | 2 kat kötü |")
    print("|---|---|---|---|---|---|")
    for n in (13, 52):
        for h in (14, 30):
            cells = " | ".join(f"%{power(n, h, s) * 100:.0f}" for s in (1.0, 1.2, 1.5, 2.0))
            print(f"| {n} | {h} gün | {cells} |")
