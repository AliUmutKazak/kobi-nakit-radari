"""Panelde Türkçe sayı, para ve tablo gösterimi."""
import pandas as pd
import streamlit as st

STAGES = {"hatirlatma": "Hatırlatma", "mutabakat": "Mutabakat", "resmi": "Resmî bildirim"}

# Bu olasılıktan itibaren risk "en az" diye gösterilir: doğrulamada yüksek riskte gerçekleşme gösterilenden yüksekti
# (%80 → %92; docs/DOGRULAMA.md). Yeniden ayar (izotonik) gerçek sonuç verisi gerektirir, pilot sonrasına kayıtlı.
HIGH_RISK = 0.5


def tr_number(x: float, digits: int = 2) -> str:
    """Türkçe sayı biçimi: binlik ayırıcı nokta, ondalık virgül (yalnızca sayıya uygulanır, cümleye değil)."""
    return f"{x:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def verdict_text(v) -> str:
    """B1/B2 sonucu: True/False/None; kayıttan (JSON) okununca 1.0/0.0/NaN da gelebilir."""
    if v is None or (isinstance(v, float) and v != v):
        return "değerlendirilemedi"
    return "geçti" if bool(v) else "kaldı"


def synced_state(key: str, stored) -> None:
    """Anahtarlı alanı kayıtlı değerle eşler. Kayıtlı değer panel dışında değiştiyse (yedekten geri yükleme, işletme
    verisinin silinmesi) alan da güncellenir; yoksa eski oturum değeri kayda geri yazılırdı."""
    shadow = key + "::stored"
    if key not in st.session_state or st.session_state.get(shadow) != stored:
        st.session_state[key] = stored
    st.session_state[shadow] = stored




def tl(x, compact: bool = False) -> str:
    """Türkçe para biçimi: 2.108.055 TL; compact=True ise 2,1 mn TL."""
    x = float(x)
    if compact and abs(x) >= 1e6:
        return f"{x / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mn TL"
    return f"{x:,.0f}".replace(",", ".") + " TL"


def show_table(df, help: dict | None = None, **kwargs):
    """Tabloları Türkçe gösterir: tarih GG.AA.YYYY, "(TL)" sütunları binlik ayraçlı, olasılıklar yüzde."""
    config, df = {}, df.copy()
    for col in df.columns:
        tip = (help or {}).get(col)
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            config[col] = st.column_config.DateColumn(col, format="DD.MM.YYYY", help=tip)
        elif "(TL)" in col:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(0)
            config[col] = st.column_config.NumberColumn(col, format="localized", help=tip)
        elif "olasılı" in col.lower() or "risk" in col.lower():
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)
            config[col] = st.column_config.NumberColumn(col, format="percent", help=tip)
        elif tip:
            config[col] = st.column_config.Column(col, help=tip)
    return st.dataframe(df, column_config=config, **kwargs)


def turkish_axes(fig):
    """Grafikte Türkçe sayı ayracı ve gün.ay biçimli tarih."""
    fig.update_layout(separators=",.", yaxis_tickformat=",.0f", xaxis_tickformat="%d.%m", xaxis_hoverformat="%d.%m.%Y",
                      yaxis_hoverformat=",.0f", legend=dict(orientation="h", y=-0.15))
    return fig
