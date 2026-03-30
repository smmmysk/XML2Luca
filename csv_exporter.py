"""
CSV dışa aktarma modülü.
Muhasebe programlarına uygun formatta (noktalı virgül ayırıcılı, Windows-1254 ANSI) CSV oluşturur.
"""

import csv
import codecs


def export_to_csv(data_list, output_path):
    """
    Fatura verilerini CSV dosyasına yazar.
    - Ayırıcı: noktalı virgül (;)
    - Kodlama: Windows-1254 (Luca uyumluluğu için ANSI Türkçe)
    """
    if not data_list:
        return False

    try:
        with codecs.open(output_path, 'w', encoding='windows-1254', errors='replace') as csvfile:
            fieldnames = data_list[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for data in data_list:
                writer.writerow(data)
        return True
    except Exception:
        return False
