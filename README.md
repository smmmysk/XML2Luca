YSK XML to Luca CSV Converter

Türkiye'deki yaygın e-fatura XML formatlarını (Giden e-Arşiv, Giden e-Fatura, Gelen e-Fatura ve İstisna Faturaları) Luca Muhasebe Programı'nın Hızlı Fiş Aktarım standartlarına %100 uyumlu CSV dosyalarına dönüştüren, modern arayüzlü masaüstü Python uygulamasıdır.


✨ Özellikler
🎨 Modern Arayüz
CustomTkinter tabanlı
Fluent / Metro tasarım dili
Dark mode desteği
🧠 Akıllı Anahtar Kelime Eşleştirme
data/analizle.xlsx üzerinden dinamik kural yönetimi
Ürün/hizmet açıklamalarından otomatik muhasebe sınıflandırması
Türkçe karakter toleranslı eşleşme (ü → u, ş → s)
NLP benzeri yaklaşım ile yüksek doğruluk
📊 Luca ile %100 Uyumluluk
Binlik ayırıcı kaldırılır → 1.250,55 → 1250,55
Ondalık ayracı korunur → ,
CSV encoding: Windows-1254 (ANSI)
(Luca'nın doğru okuması için kritik)
⚡ Toplu İşlem
Klasör bazlı yüzlerce XML'i tek seferde dönüştürme
Yüksek performanslı parsing
🗃️ İşlem Geçmişi
SQLite tabanlı kayıt sistemi
Geçmiş işlemleri görüntüleme ve temizleme
📦 Kurulum
Gereksinimler
Python 3.8+
pandas
openpyxl
customtkinter


👉 Python indirmek için: https://www.python.org/downloads/

🔧 Kurulum Adımları
git clone <repo-url>
cd XML2Luca
⚡ Windows (Önerilen)
baslat.bat dosyasına çift tıklayın
➡️ Tüm bağımlılıklar otomatik kurulur ve uygulama başlar
🛠 Manuel Kurulum
pip install -r requirements.txt
pythonw main.py
🧪 Kullanım
Fatura tipini seçin:
Gelen e-Fatura
Giden e-Fatura
e-Arşiv vb.
(Opsiyonel ama önerilir)
Ayarlar → analizle.xlsx dosyasını tanımlayın
XML klasörünü seçin
CSV çıktı dizinini belirleyin
İşlemi Başlat butonuna tıklayın

✅ İşlem saniyeler içinde tamamlanır

📁 Proje Yapısı
XML2Luca/
│
├── main.py                # UI / uygulama giriş noktası
├── xml_parser.py         # XML parsing motoru
├── analysis_matcher.py   # Akıllı eşleştirme algoritması
├── csv_exporter.py       # CSV üretimi (ANSI)
├── number_formatter.py   # Luca uyumlu sayı formatlama
├── db_manager.py         # SQLite işlem geçmişi
├── data/
│   └── analizle.xlsx     # Kural dosyası
├── baslat.bat           # Tek tık çalıştırma (Windows)
└── requirements.txt
🎯 Kullanım Amacı

Bu proje özellikle:

SMMM'ler
Muhasebe ofisleri
E-fatura yoğun çalışan işletmeler

için günlük veri giriş yükünü minimize etmek amacıyla geliştirilmiştir.