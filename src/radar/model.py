"""Vade aşımı (gün) için kantil tahmini.

Nokta tahmin + Gaussyen gürültü yerine doğrudan P10..P90 kantilleri öğrenilir ve
P10-P90 aralığı ayrılmış bir kalibrasyon dilimiyle (conformalized quantile regression)
düzeltilir. Başarı, "müşterinin geçmiş medyanı" basit tahminine göre ölçülür.
"""
from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd

from .features import FEATURES, build_features

QS = (0.10, 0.25, 0.50, 0.75, 0.90)


def training_frame(obs: pd.DataFrame, cutoff, mature_days: int = 60, feats: pd.DataFrame | None = None):
    """Yalnızca vadesi en az `mature_days` önce dolmuş faturalar eğitime girer.

    Yeni faturalarda sadece hızlı ödenenler görünür olduğu için hepsini almak modeli
    iyimser yapar. Olgunlaşmış ama hâlâ ödenmemiş faturaların etiketi, o güne kadarki
    gecikmedir (alt sınır).

    `feats`: tüm veri için önceden hesaplanmış (fatura tarihine göre) özellikler. Bu özellikler
    yalnızca fatura tarihinden önceki ödemelere baktığı için verinin hangi tarihte kesildiğinden
    etkilenmez; geçmiş tarihlere dönülürken yeniden hesaplanmaları gerekmez."""
    cutoff = pd.Timestamp(cutoff)
    X = feats.loc[obs.index] if feats is not None else build_features(obs)
    mature = obs["due_date"] <= cutoff - pd.Timedelta(days=mature_days)
    y = (obs["paid_date"].fillna(cutoff) - obs["due_date"]).dt.days.astype(float)
    order = obs.loc[mature].sort_values("issue_date").index
    return X.loc[order], y.loc[order]


class DelayModel:
    def __init__(self, alpha: float = 0.2, calib_share: float = 0.25, refit: bool = True, **params):
        """refit=False: kalibrasyon payı ayrılarak eğitilen model kullanılır (tam bölünmüş uyumlu
        aralık; daha hızlı). True: aynı pay korunarak tüm veriyle yeniden eğitilir (yaklaşık)."""
        self.alpha, self.calib_share, self.refit = alpha, calib_share, refit
        self.params = dict(n_estimators=300, learning_rate=0.05, num_leaves=15,
                           min_child_samples=20, subsample=0.8, subsample_freq=1,
                           colsample_bytree=0.8, verbose=-1, random_state=0, n_jobs=1) | params
        self.offset = 0.0
        self.models: dict[float, lgb.LGBMRegressor] = {}

    def _fit(self, X, y):
        return {q: lgb.LGBMRegressor(objective="quantile", alpha=q, **self.params).fit(X[FEATURES], y) for q in QS}

    def _raw(self, models, X):
        return np.column_stack([models[q].predict(X[FEATURES]) for q in QS])

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """X, y fatura tarihine göre sıralı gelmelidir; son dilim kalibrasyona ayrılır."""
        n_cal = max(int(len(X) * self.calib_share), 30)
        first = self._fit(X.iloc[:-n_cal], y.iloc[:-n_cal])
        raw = self._raw(first, X.iloc[-n_cal:])
        y_cal = y.iloc[-n_cal:].to_numpy()
        score = np.maximum(raw[:, 0] - y_cal, y_cal - raw[:, -1])
        level = min(1.0, (1 - self.alpha) * (1 + 1 / n_cal))
        self.offset = float(np.quantile(score, level))
        self.models = self._fit(X, y) if self.refit else first
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        Q = self._raw(self.models, X)
        Q[:, 0] -= self.offset
        Q[:, -1] += self.offset
        return np.sort(Q, axis=1)


class FallbackModel:
    """Az veride kullanılır: müşteri medyanı + geçmişteki sapmaların kantilleri."""

    DEFAULT = np.array([-3.0, 0.0, 4.0, 12.0, 30.0])

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.resid = np.quantile(y - X["hist_med"], QS) if len(X) >= 20 else self.DEFAULT
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X["hist_med"].to_numpy()[:, None] + self.resid[None, :]


MIN_LGBM_ROWS = 300


class CombinedModel:
    """Kantil ortalaması (Vincentization): LightGBM ile müşteri medyanı modelinin kantilleri eşit ağırlıkla.

    Tahmin birleştirmenin tek modelden çoğunlukla daha isabetli olduğu bilinir (Bates ve Granger 1969;
    kantil ortalaması için Lichtendahl, Grushka-Cockayne ve Winkler 2013). Açık verilerde müşteri medyanı
    fatura düzeyinde LightGBM'den biraz iyiydi; birinin seçilmesi (reddedildi) yerine ikisi ortalanır.
    Ağırlıklar veriden öğrenilmez: az veride öğrenilen ağırlıklar eşit ağırlıktan genellikle kötüdür."""

    def __init__(self, refit: bool = True):
        self.parts = [DelayModel(refit=refit), FallbackModel()]

    def fit(self, X, y):
        for m in self.parts:
            m.fit(X, y)
        return self

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.parts], axis=0)


def fit_model(X: pd.DataFrame, y: pd.Series, min_rows: int | None = None, refit: bool = True):
    """Yeterli olgun fatura varsa LightGBM + müşteri medyanı birleşimi, yoksa basit kantil modeli."""
    min_rows = MIN_LGBM_ROWS if min_rows is None else min_rows
    return (CombinedModel(refit=refit) if len(X) >= min_rows else FallbackModel()).fit(X, y)


def evaluate(Q: np.ndarray, y, baseline) -> dict:
    y, baseline = np.asarray(y, float), np.asarray(baseline, float)
    pinball = np.mean([np.mean(np.maximum(q * (y - Q[:, k]), (q - 1) * (y - Q[:, k]))) for k, q in enumerate(QS)])
    return {
        "n": len(y),
        "mae_model": float(np.mean(np.abs(y - Q[:, 2]))),
        "mae_baseline": float(np.mean(np.abs(y - baseline))),
        "pinball": float(pinball),
        "coverage_p10_p90": float(np.mean((y >= Q[:, 0]) & (y <= Q[:, -1]))),
    }
