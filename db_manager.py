"""
SQLite veritabanı ile işlem geçmişi yönetimi.
"""

import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'islem_gecmisi.db')


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Veritabanı tablolarını oluşturur."""
    conn = _get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS islem_gecmisi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT NOT NULL,
            fatura_turu TEXT NOT NULL,
            dosya_sayisi INTEGER NOT NULL,
            basarili INTEGER NOT NULL,
            hatali INTEGER NOT NULL,
            csv_dosyasi TEXT,
            durum TEXT NOT NULL DEFAULT 'Tamamlandı'
        )
    ''')
    conn.commit()
    conn.close()


def kayit_ekle(fatura_turu, dosya_sayisi, basarili, hatali, csv_dosyasi, durum='Tamamlandı'):
    """İşlem geçmişine yeni kayıt ekler."""
    conn = _get_connection()
    conn.execute(
        '''INSERT INTO islem_gecmisi (tarih, fatura_turu, dosya_sayisi, basarili, hatali, csv_dosyasi, durum)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (datetime.now().strftime('%d.%m.%Y %H:%M'), fatura_turu, dosya_sayisi, basarili, hatali, csv_dosyasi, durum)
    )
    conn.commit()
    conn.close()


def gecmisi_getir(limit=100):
    """Son işlem kayıtlarını döndürür."""
    conn = _get_connection()
    rows = conn.execute(
        'SELECT * FROM islem_gecmisi ORDER BY id DESC LIMIT ?', (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def gecmisi_temizle():
    """Tüm işlem geçmişini siler."""
    conn = _get_connection()
    conn.execute('DELETE FROM islem_gecmisi')
    conn.commit()
    conn.close()


# Uygulama başlatıldığında tabloyu oluştur
init_db()
