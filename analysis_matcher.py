"""
analizle.xlsx dosyasından anahtar kelime eşleştirmesi yapan modül.
Fatura kalem açıklamalarını analiz ederek KAYIT ALT TÜRÜ alanını otomatik belirler.
"""

import pandas as pd
from os.path import exists

_TR_MAP = str.maketrans(
    'çÇğĞıİöÖşŞüÜâÂîÎûÛ',
    'ccggiioossuuaaiiuu'
)

def _normalize(text):
    """Metni küçük harfe çevirir ve Türkçe karakterleri ASCII'ye dönüştürür."""
    if not text:
        return ""
    return str(text).lower().translate(_TR_MAP).strip()


def load_analysis_data(xlsx_path):
    """
    Excel dosyasından anahtar kelime → açıklama eşleştirmelerini yükler.
    İlk sütun: anahtar kelime, İkinci sütun: açıklama
    """
    if not xlsx_path or not exists(xlsx_path):
        return {}

    try:
        df = pd.read_excel(xlsx_path, header=None)

        if df.shape[1] < 2:
            return {}

        analysis_dict = {}
        for _, row in df.iterrows():
            keyword = str(row.iloc[0]).strip() if pd.notnull(row.iloc[0]) else ""
            explanation = str(row.iloc[1]).strip() if pd.notnull(row.iloc[1]) else ""
            if keyword and explanation:
                analysis_dict[_normalize(keyword)] = explanation

        return analysis_dict

    except Exception:
        return {}


def find_matching_analysis(description, analysis_data):
    """
    Verilen açıklama metninde anahtar kelimeleri arar.
    Eşleşme bulursa karşılık gelen açıklamayı, bulamazsa '#KONTROL' döndürür.
    """
    if not description or not analysis_data:
        return "#KONTROL"

    description_norm = _normalize(description)

    for keyword, explanation in analysis_data.items():
        if keyword in description_norm:
            return explanation

    return "#KONTROL"
