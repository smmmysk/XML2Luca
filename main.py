"""
YSK e-Fatura XML → CSV Dönüştürücü
Masaüstü Uygulaması — Metro / Fluent Design

Desteklenen fatura türleri:
  1. Giden e-Arşiv Fatura
  2. Giden e-Fatura
  3. Gelen e-Fatura
  4. İstisna Fatura
"""

import os
import threading
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

import customtkinter as ctk

# Modülleri import et
from csv_exporter import export_to_csv
from analysis_matcher import load_analysis_data
from db_manager import kayit_ekle, gecmisi_getir, gecmisi_temizle

# ──────────────────────────────────────────────
# Sabitler
# ──────────────────────────────────────────────

APP_TITLE = "YSK — XML → Luca CSV Dönüştürücü"
APP_VERSION = "2.0"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ANALYSIS_FILE = os.path.join(APP_DIR, 'data', 'analizle.xlsx')

FATURA_TURLERI = [
    ("Giden e-Arşiv Fatura", "earsiv",        "Gelir / Satış",  "#60CDFF"),
    ("Giden e-Fatura",       "efatura_giden",  "Gelir / Satış",  "#6CCB5F"),
    ("Gelen e-Fatura",       "efatura_gelen",  "Gider / Alış",   "#FCB827"),
    ("İstisna Fatura",       "istisna",        "Gider / Alış",   "#FF6B6B"),
]

# ──────────────────────────────────────────────
# Metro / Fluent Renk Paleti (Windows 11)
# ──────────────────────────────────────────────

METRO = {
    # Arka planlar
    'bg_base':        '#1C1C1C',
    'bg_card':        '#2D2D2D',
    'bg_card_hover':  '#383838',
    'bg_elevated':    '#3A3A3A',
    'bg_input':       '#1F1F1F',
    'bg_subtle':      '#252525',

    # Metin
    'fg_primary':     '#FFFFFF',
    'fg_secondary':   '#C5C5C5',
    'fg_tertiary':    '#8B8B8B',
    'fg_disabled':    '#5C5C5C',

    # Accent
    'accent':         '#0078D4',
    'accent_hover':   '#1A8FE8',
    'accent_pressed': '#006CBE',
    'accent_subtle':  '#0078D420',

    # Semantik
    'success':        '#6CCB5F',
    'warning':        '#FCB827',
    'error':          '#FF6B6B',
    'info':           '#60CDFF',

    # Kenarlıklar
    'border':         '#404040',
    'border_subtle':  '#333333',
    'divider':        '#2B2B2B',

    # Özel
    'overlay':        '#00000080',
    'tab_active':     '#0078D4',
    'tab_inactive':   '#2D2D2D',
    'row_alt':        '#252525',
    'row_hover':      '#333333',
}

FONT_FAMILY = "Segoe UI"


# ──────────────────────────────────────────────
# Yardımcı Widget'lar
# ──────────────────────────────────────────────

class MetroCard(ctk.CTkFrame):
    """Yükseltilmiş yüzey efektli kart widget'ı."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=METRO['bg_card'],
            corner_radius=8,
            border_width=1,
            border_color=METRO['border_subtle'],
            **kwargs
        )


class MetroSectionLabel(ctk.CTkLabel):
    """Bölüm başlığı — Metro tipografisi."""

    def __init__(self, master, text, **kwargs):
        super().__init__(
            master,
            text=text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=METRO['fg_primary'],
            anchor='w',
            **kwargs
        )


class FaturaTypeCard(ctk.CTkFrame):
    """Fatura türü seçim kartı — renkli aksan çizgili."""

    def __init__(self, master, label, description, accent_color, key, on_click):
        super().__init__(
            master,
            fg_color=METRO['bg_card'],
            corner_radius=8,
            border_width=1,
            border_color=METRO['border_subtle'],
            cursor='hand2'
        )
        self.key = key
        self.accent_color = accent_color
        self.on_click = on_click
        self.is_selected = False

        # Accent strip (üst kenar)
        self.accent_strip = ctk.CTkFrame(
            self, height=3, fg_color=accent_color,
            corner_radius=0
        )
        self.accent_strip.pack(fill='x', padx=8, pady=(8, 0))

        # İkon + Metin
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=12, pady=(8, 12))

        icon_label = ctk.CTkLabel(
            content,
            text="📄",
            font=ctk.CTkFont(size=22),
            text_color=accent_color,
        )
        icon_label.pack(anchor='w')

        title_label = ctk.CTkLabel(
            content,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=METRO['fg_primary'],
            anchor='w'
        )
        title_label.pack(anchor='w', pady=(4, 0))

        desc_label = ctk.CTkLabel(
            content,
            text=description,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=METRO['fg_tertiary'],
            anchor='w'
        )
        desc_label.pack(anchor='w', pady=(2, 0))

        # Tüm çocuklara tıklama etkinliği bağla
        for widget in [self, content, icon_label, title_label, desc_label,
                       self.accent_strip]:
            widget.bind('<Button-1>', lambda e: self._handle_click())
            widget.bind('<Enter>', lambda e: self._on_enter())
            widget.bind('<Leave>', lambda e: self._on_leave())

    def _handle_click(self):
        self.on_click(self.key)

    def _on_enter(self):
        if not self.is_selected:
            self.configure(fg_color=METRO['bg_card_hover'])

    def _on_leave(self):
        if not self.is_selected:
            self.configure(fg_color=METRO['bg_card'])

    def set_selected(self, selected):
        self.is_selected = selected
        if selected:
            self.configure(
                fg_color=METRO['bg_elevated'],
                border_color=self.accent_color
            )
        else:
            self.configure(
                fg_color=METRO['bg_card'],
                border_color=METRO['border_subtle']
            )


# ──────────────────────────────────────────────
# Ana Uygulama Sınıfı
# ──────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # CTk tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1040x740")
        self.minsize(860, 640)
        self.configure(fg_color=METRO['bg_base'])

        # İkon ayarla (varsa)
        icon_path = os.path.join(APP_DIR, 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # Analiz verilerini yükle
        self.analysis_file = DEFAULT_ANALYSIS_FILE
        self.analysis_data = {}
        self._load_analysis()

        # Seçilen dosyalar
        self.selected_files = []
        self.active_fatura_type = None

        # Treeview stilleri
        self._setup_treeview_style()

        # Arayüz bileşenleri
        self._build_ui()

        # Pencereyi ortala
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _load_analysis(self):
        if os.path.exists(self.analysis_file):
            self.analysis_data = load_analysis_data(self.analysis_file)

    def _setup_treeview_style(self):
        """Treeview (tkinter ttk) için Metro tarzı stil."""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Metro.Treeview',
                        background=METRO['bg_card'],
                        foreground=METRO['fg_primary'],
                        fieldbackground=METRO['bg_card'],
                        borderwidth=0,
                        rowheight=32,
                        font=(FONT_FAMILY, 10))

        style.configure('Metro.Treeview.Heading',
                        background=METRO['bg_elevated'],
                        foreground=METRO['accent'],
                        borderwidth=0,
                        font=(FONT_FAMILY, 10, 'bold'),
                        padding=(8, 6))

        style.map('Metro.Treeview',
                  background=[('selected', METRO['accent'])],
                  foreground=[('selected', '#FFFFFF')])

        style.map('Metro.Treeview.Heading',
                  background=[('active', METRO['bg_card_hover'])])

        # Treeview scrollbar
        style.configure('Metro.Vertical.TScrollbar',
                        background=METRO['bg_card'],
                        troughcolor=METRO['bg_subtle'],
                        borderwidth=0,
                        arrowsize=0,
                        width=8)
        style.map('Metro.Vertical.TScrollbar',
                  background=[('active', METRO['fg_tertiary']),
                              ('!active', METRO['fg_disabled'])])

    # ──────────────────────────────────────────
    # Arayüz Oluşturma
    # ──────────────────────────────────────────

    def _build_ui(self):
        # ── Başlık Çubuğu ──
        header = ctk.CTkFrame(self, fg_color=METRO['bg_subtle'], height=60, corner_radius=0)
        header.pack(fill='x')
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color='transparent')
        header_content.pack(fill='both', expand=True, padx=24)

        # Sol: Logo + Başlık
        left_header = ctk.CTkFrame(header_content, fg_color='transparent')
        left_header.pack(side='left', fill='y')

        ctk.CTkLabel(
            left_header,
            text="📄",
            font=ctk.CTkFont(size=24),
        ).pack(side='left', padx=(0, 10), pady=12)

        title_frame = ctk.CTkFrame(left_header, fg_color='transparent')
        title_frame.pack(side='left', fill='y', pady=8)

        ctk.CTkLabel(
            title_frame,
            text="XML → Luca CSV",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=METRO['fg_primary']
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Fatura dosyalarınızı Luca muhasebe programına uygun formata dönüştürün",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=METRO['fg_tertiary']
        ).pack(anchor='w')

        # Sağ: Versiyon badge
        version_badge = ctk.CTkFrame(
            header_content, fg_color=METRO['accent'],
            corner_radius=12, width=50, height=24
        )
        version_badge.pack(side='right', pady=18)
        version_badge.pack_propagate(False)
        ctk.CTkLabel(
            version_badge,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color='#FFFFFF'
        ).pack(expand=True)

        # ── Accent divider ──
        ctk.CTkFrame(
            self, height=2, fg_color=METRO['accent'], corner_radius=0
        ).pack(fill='x')

        # ── Ana İçerik: TabView ──
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=METRO['bg_base'],
            segmented_button_fg_color=METRO['bg_subtle'],
            segmented_button_selected_color=METRO['accent'],
            segmented_button_selected_hover_color=METRO['accent_hover'],
            segmented_button_unselected_color=METRO['bg_subtle'],
            segmented_button_unselected_hover_color=METRO['bg_card_hover'],
            text_color=METRO['fg_primary'],
            text_color_disabled=METRO['fg_disabled'],
            corner_radius=8,
            border_width=0,
        )
        self.tabview.pack(fill='both', expand=True, padx=20, pady=(12, 0))

        # Sekmeleri oluştur
        self.tab_process = self.tabview.add("  📄  Fatura İşle  ")
        self.tab_history = self.tabview.add("  📋  İşlem Geçmişi  ")
        self.tab_settings = self.tabview.add("  ⚙  Ayarlar  ")

        self._build_process_tab()
        self._build_history_tab()
        self._build_settings_tab()

        # ── Durum Çubuğu ──
        status_frame = ctk.CTkFrame(self, fg_color=METRO['bg_subtle'], height=32, corner_radius=0)
        status_frame.pack(fill='x', side='bottom')
        status_frame.pack_propagate(False)

        status_content = ctk.CTkFrame(status_frame, fg_color='transparent')
        status_content.pack(fill='both', expand=True, padx=16)

        # Sol: durum ikonu + mesaj
        self.status_icon = ctk.CTkLabel(
            status_content, text="●",
            font=ctk.CTkFont(size=10),
            text_color=METRO['success'],
            width=16
        )
        self.status_icon.pack(side='left')

        self.status_label = ctk.CTkLabel(
            status_content,
            text="Hazır",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=METRO['fg_tertiary']
        )
        self.status_label.pack(side='left', padx=(4, 0))

        # Sağ: analiz sayısı
        analysis_count = len(self.analysis_data)
        ctk.CTkLabel(
            status_content,
            text=f"📊 {analysis_count} analiz kuralı",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=METRO['fg_disabled']
        ).pack(side='right')

    # ──────────────────────────────────────────
    # FATURA İŞLE SEKMESİ
    # ──────────────────────────────────────────

    def _build_process_tab(self):
        parent = self.tab_process

        # Scrollable container
        scroll = ctk.CTkScrollableFrame(
            parent, fg_color='transparent',
            scrollbar_button_color=METRO['fg_disabled'],
            scrollbar_button_hover_color=METRO['fg_tertiary']
        )
        scroll.pack(fill='both', expand=True)

        # ── BÖLÜM 1: Fatura Türü Seçimi ──
        MetroSectionLabel(scroll, text="❶  Fatura Türünü Seçin").pack(
            anchor='w', padx=4, pady=(8, 8)
        )

        cards_frame = ctk.CTkFrame(scroll, fg_color='transparent')
        cards_frame.pack(fill='x', padx=4, pady=(0, 16))

        self.type_cards = {}
        for i, (label, key, desc, color) in enumerate(FATURA_TURLERI):
            card = FaturaTypeCard(
                cards_frame,
                label=label,
                description=desc,
                accent_color=color,
                key=key,
                on_click=self._select_type
            )
            card.grid(row=0, column=i, padx=(0, 10), sticky='nsew')
            cards_frame.columnconfigure(i, weight=1)
            self.type_cards[key] = card

        # ── BÖLÜM 2: Dosya Seçimi ──
        MetroSectionLabel(scroll, text="❷  XML Dosyalarını Seçin").pack(
            anchor='w', padx=4, pady=(0, 8)
        )

        file_card = MetroCard(scroll)
        file_card.pack(fill='x', padx=4, pady=(0, 16))

        file_content = ctk.CTkFrame(file_card, fg_color='transparent')
        file_content.pack(fill='x', padx=16, pady=14)

        # Dosya bilgi satırı
        file_info = ctk.CTkFrame(file_content, fg_color='transparent')
        file_info.pack(fill='x')

        self.file_icon = ctk.CTkLabel(
            file_info, text="📂",
            font=ctk.CTkFont(size=20), width=30
        )
        self.file_icon.pack(side='left')

        file_text_frame = ctk.CTkFrame(file_info, fg_color='transparent')
        file_text_frame.pack(side='left', fill='x', expand=True, padx=(8, 0))

        self.file_label = ctk.CTkLabel(
            file_text_frame,
            text="Henüz dosya seçilmedi",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=METRO['fg_tertiary'],
            anchor='w'
        )
        self.file_label.pack(anchor='w')

        self.file_detail = ctk.CTkLabel(
            file_text_frame,
            text="Dosya veya klasör seçerek XML faturalarınızı yükleyin",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=METRO['fg_disabled'],
            anchor='w'
        )
        self.file_detail.pack(anchor='w')

        # Butonlar
        btn_frame = ctk.CTkFrame(file_info, fg_color='transparent')
        btn_frame.pack(side='right')

        ctk.CTkButton(
            btn_frame,
            text="📁  Dosya Seç",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=METRO['bg_elevated'],
            hover_color=METRO['bg_card_hover'],
            text_color=METRO['fg_primary'],
            corner_radius=6,
            height=36,
            width=130,
            command=self._select_files
        ).pack(side='left', padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="📂  Klasör Seç",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=METRO['bg_elevated'],
            hover_color=METRO['bg_card_hover'],
            text_color=METRO['fg_primary'],
            corner_radius=6,
            height=36,
            width=130,
            command=self._select_folder
        ).pack(side='left')

        # ── BÖLÜM 3: İşlem Başlat ──
        MetroSectionLabel(scroll, text="❸  Dönüştür").pack(
            anchor='w', padx=4, pady=(0, 8)
        )

        action_card = MetroCard(scroll)
        action_card.pack(fill='x', padx=4, pady=(0, 16))

        action_content = ctk.CTkFrame(action_card, fg_color='transparent')
        action_content.pack(fill='x', padx=16, pady=14)

        action_row = ctk.CTkFrame(action_content, fg_color='transparent')
        action_row.pack(fill='x')

        self.btn_process = ctk.CTkButton(
            action_row,
            text="▶   İşlemi Başlat",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=METRO['accent'],
            hover_color=METRO['accent_hover'],
            text_color='#FFFFFF',
            corner_radius=6,
            height=42,
            width=180,
            command=self._start_processing
        )
        self.btn_process.pack(side='left')

        # Progress
        progress_frame = ctk.CTkFrame(action_row, fg_color='transparent')
        progress_frame.pack(side='left', fill='x', expand=True, padx=(16, 0))

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=METRO['fg_secondary'],
            anchor='w'
        )
        self.progress_label.pack(anchor='w')

        self.progress = ctk.CTkProgressBar(
            progress_frame,
            fg_color=METRO['bg_input'],
            progress_color=METRO['success'],
            height=6,
            corner_radius=3
        )
        self.progress.pack(fill='x', pady=(4, 0))
        self.progress.set(0)

        # ── BÖLÜM 4: İşlem Günlüğü ──
        MetroSectionLabel(scroll, text="İşlem Günlüğü").pack(
            anchor='w', padx=4, pady=(0, 8)
        )

        log_card = MetroCard(scroll)
        log_card.pack(fill='x', padx=4, pady=(0, 8))

        log_container = ctk.CTkFrame(log_card, fg_color='transparent')
        log_container.pack(fill='both', expand=True, padx=2, pady=2)

        self.log_text = ctk.CTkTextbox(
            log_container,
            fg_color=METRO['bg_input'],
            text_color=METRO['fg_secondary'],
            font=ctk.CTkFont(family="Cascadia Code", size=11),
            corner_radius=6,
            height=160,
            border_width=0,
            scrollbar_button_color=METRO['fg_disabled'],
            scrollbar_button_hover_color=METRO['fg_tertiary'],
            wrap='word',
            state='disabled'
        )
        self.log_text.pack(fill='both', expand=True, padx=8, pady=8)

        # Log temizle butonu
        log_toolbar = ctk.CTkFrame(log_card, fg_color='transparent', height=32)
        log_toolbar.pack(fill='x', padx=12, pady=(0, 8))

        ctk.CTkButton(
            log_toolbar,
            text="🗑  Günlüğü Temizle",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color='transparent',
            hover_color=METRO['bg_card_hover'],
            text_color=METRO['fg_tertiary'],
            corner_radius=4,
            height=28,
            width=140,
            command=self._clear_log
        ).pack(side='right')

    # ──────────────────────────────────────────
    # İŞLEM GEÇMİŞİ SEKMESİ
    # ──────────────────────────────────────────

    def _build_history_tab(self):
        parent = self.tab_history

        # Toolbar
        toolbar = ctk.CTkFrame(parent, fg_color='transparent')
        toolbar.pack(fill='x', padx=4, pady=(8, 12))

        MetroSectionLabel(toolbar, text="İşlem Geçmişi").pack(side='left')

        ctk.CTkButton(
            toolbar,
            text="🗑  Temizle",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=METRO['error'],
            hover_color='#E05555',
            text_color='#FFFFFF',
            corner_radius=6,
            height=32,
            width=100,
            command=self._clear_history
        ).pack(side='right', padx=(8, 0))

        ctk.CTkButton(
            toolbar,
            text="🔄  Yenile",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=METRO['bg_elevated'],
            hover_color=METRO['bg_card_hover'],
            text_color=METRO['fg_primary'],
            corner_radius=6,
            height=32,
            width=100,
            command=self._refresh_history
        ).pack(side='right')

        # Treeview kartı
        tree_card = MetroCard(parent)
        tree_card.pack(fill='both', expand=True, padx=4, pady=(0, 8))

        tree_inner = ctk.CTkFrame(tree_card, fg_color='transparent')
        tree_inner.pack(fill='both', expand=True, padx=2, pady=2)

        columns = ('tarih', 'fatura_turu', 'dosya_sayisi', 'basarili', 'hatali', 'durum', 'csv')

        self.history_tree = ttk.Treeview(
            tree_inner,
            columns=columns,
            show='headings',
            height=18,
            style='Metro.Treeview'
        )

        headings = {
            'tarih':        ('📅  Tarih', 140),
            'fatura_turu':  ('📄  Fatura Türü', 150),
            'dosya_sayisi': ('📦  Dosya', 70),
            'basarili':     ('✅  Başarılı', 80),
            'hatali':       ('❌  Hatalı', 70),
            'durum':        ('📊  Durum', 100),
            'csv':          ('💾  CSV Dosyası', 280)
        }

        for col, (heading, width) in headings.items():
            self.history_tree.heading(col, text=heading, anchor='w')
            self.history_tree.column(col, width=width, minwidth=50, anchor='w')

        # Scrollbar
        tree_scroll = ttk.Scrollbar(
            tree_inner, orient='vertical',
            command=self.history_tree.yview,
            style='Metro.Vertical.TScrollbar'
        )
        self.history_tree.configure(yscrollcommand=tree_scroll.set)

        tree_scroll.pack(side='right', fill='y', padx=(0, 4), pady=4)
        self.history_tree.pack(fill='both', expand=True, padx=(4, 0), pady=4)

        # Tag'ler: alternatif satır renkleri
        self.history_tree.tag_configure('odd', background=METRO['bg_card'])
        self.history_tree.tag_configure('even', background=METRO['row_alt'])
        self.history_tree.tag_configure('success_row', foreground=METRO['success'])
        self.history_tree.tag_configure('error_row', foreground=METRO['error'])

        self._refresh_history()

    # ──────────────────────────────────────────
    # AYARLAR SEKMESİ
    # ──────────────────────────────────────────

    def _build_settings_tab(self):
        parent = self.tab_settings

        scroll = ctk.CTkScrollableFrame(
            parent, fg_color='transparent',
            scrollbar_button_color=METRO['fg_disabled'],
            scrollbar_button_hover_color=METRO['fg_tertiary']
        )
        scroll.pack(fill='both', expand=True)

        # ── Analiz Dosyası Kartı ──
        MetroSectionLabel(scroll, text="⚙  Analiz Dosyası Ayarları").pack(
            anchor='w', padx=4, pady=(8, 8)
        )

        settings_card = MetroCard(scroll)
        settings_card.pack(fill='x', padx=4, pady=(0, 16))

        settings_content = ctk.CTkFrame(settings_card, fg_color='transparent')
        settings_content.pack(fill='x', padx=20, pady=16)

        # Açıklama
        ctk.CTkLabel(
            settings_content,
            text="Analiz Dosyası (analizle.xlsx)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=METRO['fg_primary'],
            anchor='w'
        ).pack(anchor='w')

        ctk.CTkLabel(
            settings_content,
            text="Gelen e-Fatura ve İstisna faturalarında KAYIT ALT TÜRÜ alanını\notomatik eşleştirmek için kullanılır.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=METRO['fg_tertiary'],
            anchor='w',
            justify='left'
        ).pack(anchor='w', pady=(4, 12))

        # Dosya yolu girişi
        file_row = ctk.CTkFrame(settings_content, fg_color='transparent')
        file_row.pack(fill='x')

        self.analysis_path_var = ctk.StringVar(value=self.analysis_file)

        self.analysis_entry = ctk.CTkEntry(
            file_row,
            textvariable=self.analysis_path_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=METRO['bg_input'],
            border_color=METRO['border'],
            text_color=METRO['fg_primary'],
            corner_radius=6,
            height=38
        )
        self.analysis_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))

        ctk.CTkButton(
            file_row,
            text="📁  Gözat",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=METRO['bg_elevated'],
            hover_color=METRO['bg_card_hover'],
            text_color=METRO['fg_primary'],
            corner_radius=6,
            height=38,
            width=110,
            command=self._browse_analysis_file
        ).pack(side='right')

        # Kaydet butonu
        ctk.CTkButton(
            settings_content,
            text="💾   Kaydet ve Yenile",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=METRO['accent'],
            hover_color=METRO['accent_hover'],
            text_color='#FFFFFF',
            corner_radius=6,
            height=38,
            width=180,
            command=self._save_analysis_settings
        ).pack(anchor='w', pady=(16, 0))

        # ── Bilgi Kartı ──
        MetroSectionLabel(scroll, text="ℹ  Kullanım Bilgisi").pack(
            anchor='w', padx=4, pady=(0, 8)
        )

        info_card = MetroCard(scroll)
        info_card.pack(fill='x', padx=4, pady=(0, 8))

        info_content = ctk.CTkFrame(info_card, fg_color='transparent')
        info_content.pack(fill='x', padx=20, pady=16)

        info_items = [
            ("📄", "Analiz dosyası bir Excel (.xlsx) dosyası olmalıdır"),
            ("🔑", "İlk sütun: Anahtar kelime  —  İkinci sütun: Eşleşecek açıklama"),
            ("🔍", "Fatura kalem açıklamasında anahtar kelime bulunursa ilgili açıklama\n    otomatik olarak KAYIT ALT TÜRÜ alanına yazılır"),
            ("📊", f"Yüklü eşleştirme sayısı: {len(self.analysis_data)}"),
        ]

        for icon, text in info_items:
            item_row = ctk.CTkFrame(info_content, fg_color='transparent')
            item_row.pack(fill='x', pady=3)

            ctk.CTkLabel(
                item_row, text=icon,
                font=ctk.CTkFont(size=14), width=24
            ).pack(side='left', padx=(0, 8))

            ctk.CTkLabel(
                item_row, text=text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=METRO['fg_secondary'],
                anchor='w', justify='left'
            ).pack(side='left', fill='x', expand=True)

        # ── Uygulama Hakkında ──
        MetroSectionLabel(scroll, text="ℹ  Hakkında").pack(
            anchor='w', padx=4, pady=(16, 8)
        )

        about_card = MetroCard(scroll)
        about_card.pack(fill='x', padx=4, pady=(0, 16))

        about_content = ctk.CTkFrame(about_card, fg_color='transparent')
        about_content.pack(fill='x', padx=20, pady=16)

        about_items = [
            ("Uygulama", APP_TITLE),
            ("Sürüm", f"v{APP_VERSION}"),
            ("Tasarım", "Metro / Fluent Design"),
            ("Desteklenen Türler", "e-Arşiv, e-Fatura (Giden/Gelen), İstisna"),
        ]

        for lbl, val in about_items:
            row = ctk.CTkFrame(about_content, fg_color='transparent')
            row.pack(fill='x', pady=2)

            ctk.CTkLabel(
                row, text=lbl,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                text_color=METRO['fg_tertiary'],
                width=160, anchor='w'
            ).pack(side='left')

            ctk.CTkLabel(
                row, text=val,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=METRO['fg_primary'],
                anchor='w'
            ).pack(side='left')

    # ──────────────────────────────────────────
    # Olaylar (Event Handlers)
    # ──────────────────────────────────────────

    def _select_type(self, key):
        """Fatura türü seçimini günceller."""
        self.active_fatura_type = key

        for k, card in self.type_cards.items():
            card.set_selected(k == key)

        label_map = {t[1]: t[0] for t in FATURA_TURLERI}
        self._set_status(f"Seçili: {label_map.get(key, key)}", 'info')

    def _select_files(self):
        """Dosya seçme dialogu."""
        files = filedialog.askopenfilenames(
            title="XML Dosyalarını Seçin",
            filetypes=[("XML Dosyaları", "*.xml"), ("Tüm Dosyalar", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            count = len(self.selected_files)
            self.file_label.configure(
                text=f"{count} dosya seçildi",
                text_color=METRO['fg_primary']
            )
            self.file_detail.configure(
                text=f"Son seçim: {os.path.basename(files[0])}{'  ve diğerleri...' if count > 1 else ''}"
            )
            self.file_icon.configure(text="✅")
            self._log(f"✓ {count} dosya seçildi.")

    def _select_folder(self):
        """Klasör seçme — içindeki tüm XML'leri alır."""
        folder = filedialog.askdirectory(title="XML Dosyalarının Bulunduğu Klasörü Seçin")
        if folder:
            xml_files = [
                os.path.join(folder, f) for f in os.listdir(folder)
                if f.lower().endswith('.xml')
            ]
            if xml_files:
                self.selected_files = xml_files
                count = len(xml_files)
                self.file_label.configure(
                    text=f"{count} dosya bulundu",
                    text_color=METRO['fg_primary']
                )
                self.file_detail.configure(
                    text=f"Klasör: {os.path.basename(folder)}"
                )
                self.file_icon.configure(text="✅")
                self._log(f"✓ {count} XML dosyası bulundu: {folder}")
            else:
                messagebox.showwarning("Uyarı", "Seçilen klasörde XML dosyası bulunamadı.")

    def _start_processing(self):
        """İşlemi başlatır (ayrı thread'de)."""
        if not self.active_fatura_type:
            messagebox.showwarning("Uyarı", "Lütfen önce bir fatura türü seçin.")
            return

        if not self.selected_files:
            messagebox.showwarning("Uyarı", "Lütfen en az bir XML dosyası seçin.")
            return

        # Kayıt yeri seç
        label_map = {t[1]: t[0] for t in FATURA_TURLERI}
        type_label = label_map.get(self.active_fatura_type, self.active_fatura_type)

        default_name = f"{self.active_fatura_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_path = filedialog.asksaveasfilename(
            title="CSV Dosyasını Kaydet",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV Dosyası", "*.csv")]
        )

        if not output_path:
            return

        # İşlemi başlat
        self.btn_process.configure(state='disabled')
        self.progress.set(0)
        self._log(f"\n{'━' * 50}")
        self._log(f"▶ İşlem başladı: {type_label}")
        self._log(f"  Dosya sayısı: {len(self.selected_files)}")
        self._set_status("İşleniyor...", 'warning')

        thread = threading.Thread(
            target=self._process_worker,
            args=(self.selected_files.copy(), self.active_fatura_type, output_path, type_label),
            daemon=True
        )
        thread.start()

    def _process_worker(self, files, fatura_turu, output_path, type_label):
        """Arka plan thread'inde dosyaları işler."""
        results = []
        errors = []

        for i, fpath in enumerate(files):
            try:
                from xml_parser import PARSER_MAP
                parser = PARSER_MAP.get(fatura_turu)
                data = parser(fpath, self.analysis_data)
                results.append(data)
            except Exception as e:
                errors.append(f"{os.path.basename(fpath)}: {str(e)}")

            # İlerlemeyi güncelle
            self.after(0, self._update_progress, i + 1, len(files))

        # CSV oluştur
        success = False
        if results:
            success = export_to_csv(results, output_path)

        # Veritabanına kaydet
        kayit_ekle(
            fatura_turu=type_label,
            dosya_sayisi=len(files),
            basarili=len(results),
            hatali=len(errors),
            csv_dosyasi=output_path if success else '',
            durum='Tamamlandı' if success else 'Hata'
        )

        # Sonuç bildir
        self.after(0, self._process_complete, results, errors, output_path, success, type_label)

    def _update_progress(self, current, total):
        """İlerleme çubuğunu günceller."""
        self.progress.set(current / total)
        self.progress_label.configure(text=f"İşleniyor... {current}/{total}")

    def _process_complete(self, results, errors, output_path, success, type_label):
        """İşlem tamamlandığında çağrılır."""
        self.btn_process.configure(state='normal')

        if errors:
            self._log(f"\n⚠ {len(errors)} hata:")
            for err in errors[:20]:
                self._log(f"  ✗ {err}")
            if len(errors) > 20:
                self._log(f"  ... ve {len(errors) - 20} hata daha")

        if success:
            self._log(f"\n✓ Tamamlandı: {len(results)} fatura işlendi.")
            self._log(f"  CSV: {output_path}")
            self._set_status(f"✓ {len(results)} fatura başarıyla CSV'ye dönüştürüldü.", 'success')
            messagebox.showinfo(
                "Başarılı",
                f"{len(results)} {type_label} başarıyla işlendi.\n\n"
                f"Hatalı: {len(errors)}\n"
                f"CSV: {os.path.basename(output_path)}"
            )
        else:
            self._log("\n✗ İşlem başarısız!")
            self._set_status("✗ İşlem başarısız", 'error')
            messagebox.showerror("Hata", "Hiçbir dosya işlenemedi.")

        self.progress_label.configure(text="")
        self._refresh_history()

    def _browse_analysis_file(self):
        """Analiz dosyası seçme dialogu."""
        path = filedialog.askopenfilename(
            title="Analiz Dosyasını Seçin",
            filetypes=[("Excel Dosyası", "*.xlsx"), ("Tüm Dosyalar", "*.*")]
        )
        if path:
            self.analysis_path_var.set(path)

    def _save_analysis_settings(self):
        """Analiz dosyası ayarını kaydeder ve verileri yeniden yükler."""
        path = self.analysis_path_var.get()
        if path and os.path.exists(path):
            self.analysis_file = path
            self._load_analysis()
            messagebox.showinfo("Başarılı",
                                f"Analiz dosyası güncellendi.\n{len(self.analysis_data)} eşleştirme yüklendi.")
        else:
            messagebox.showwarning("Uyarı", "Dosya bulunamadı. Geçerli bir dosya yolu girin.")

    def _refresh_history(self):
        """İşlem geçmişi tablosunu yeniler."""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        rows = gecmisi_getir()
        for i, row in enumerate(rows):
            csv_name = os.path.basename(row.get('csv_dosyasi', '')) if row.get('csv_dosyasi') else ''
            durum = row.get('durum', '')

            tags = ('even',) if i % 2 == 0 else ('odd',)
            if durum == 'Tamamlandı':
                tags = tags + ('success_row',)
            elif durum == 'Hata':
                tags = tags + ('error_row',)

            self.history_tree.insert('', 'end', values=(
                row.get('tarih', ''),
                row.get('fatura_turu', ''),
                row.get('dosya_sayisi', ''),
                row.get('basarili', ''),
                row.get('hatali', ''),
                durum,
                csv_name
            ), tags=tags)

    def _clear_history(self):
        """İşlem geçmişini temizler."""
        if messagebox.askyesno("Onay", "Tüm işlem geçmişi silinecek. Devam etmek istiyor musunuz?"):
            gecmisi_temizle()
            self._refresh_history()
            self._log("🗑️ İşlem geçmişi temizlendi.")

    # ──────────────────────────────────────────
    # Yardımcı Metodlar
    # ──────────────────────────────────────────

    def _log(self, message):
        """Log alanına mesaj ekler."""
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message + '\n')
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def _clear_log(self):
        """Log alanını temizler."""
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')

    def _set_status(self, text, status_type='info'):
        """Durum çubuğunu günceller."""
        color_map = {
            'success': METRO['success'],
            'warning': METRO['warning'],
            'error':   METRO['error'],
            'info':    METRO['info'],
        }
        self.status_icon.configure(text_color=color_map.get(status_type, METRO['info']))
        self.status_label.configure(text=text)


# ──────────────────────────────────────────────
# Uygulama Başlat
# ──────────────────────────────────────────────

if __name__ == '__main__':
    app = App()
    app.mainloop()
