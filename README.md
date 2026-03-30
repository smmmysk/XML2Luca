# YSK XML to Luca CSV Converter

Türkiye'deki yaygın e-fatura XML formatlarını (Giden e-Arşiv, Giden e-Fatura, Gelen e-Fatura ve İstisna Faturaları) Luca Muhasebe Programı'nın Hızlı Fiş Aktarım standartlarına %100 uyumlu CSV dosyalarına dönüştüren, modern arayüzlü masaüstü Python uygulamasıdır.

## Özellikler

🎨 Modern Arayüz
🧠 Akıllı Anahtar Kelime Eşleştirme

data/analizle.xlsx üzerinden dinamik kural yönetimi

Ürün/hizmet açıklamalarından otomatik muhasebe sınıflandırması

Türkçe karakter toleranslı eşleşme (ü → u, ş → s)

NLP benzeri yaklaşım ile yüksek doğruluk

📊 Luca ile %100 Uyumluluk

⚡ Toplu İşlem

🗃️ İşlem Geçmişi


  
## Gereksinimler

- Python 3.8+
- Aşağıdaki Python kütüphaneleri:
  - pandas
  - openpyxl
  - customtkinter
## Kurulum/Kullanım

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

