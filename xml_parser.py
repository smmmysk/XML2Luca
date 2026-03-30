"""
e-Fatura XML dosyalarını parse eden modül.
4 fatura türünü destekler:
  1. Giden e-Arşiv Fatura (Gelir/Satış)
  2. Giden e-Fatura (Gelir/Satış)
  3. Gelen e-Fatura (Gider/Alış)
  4. İstisna Fatura (Gider/Alış - KDV İstisnalı)
"""

import re
import xml.etree.ElementTree as ET
from number_formatter import format_number
from analysis_matcher import find_matching_analysis

# UBL 2.0 XML namespace tanımları
NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
}


# ──────────────────────────────────────────────
# Ortak yardımcı fonksiyonlar
# ──────────────────────────────────────────────

# Türkçe karakter → ASCII dönüşüm tablosu
_TR_CHAR_MAP = str.maketrans(
    'çÇğĞıİöÖşŞüÜâÂîÎûÛ',
    'cCgGiIoOsSuUaAiIuU'
)


def _clean_text(text):
    """Türkçe özel karakterleri ASCII karşılıklarına çevirir ve özel karakterleri temizler."""
    if not text:
        return text
    # Türkçe karakterleri dönüştür
    text = text.translate(_TR_CHAR_MAP)
    # Sadece harf, rakam, boşluk, nokta, virgül, tire, eğik çizgi kalsın
    text = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', text)
    # Birden fazla boşluğu teke indir
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _get_text(element, xpath):
    """XML elementinden metin değeri alır, yoksa boş string döner."""
    el = element.find(xpath, NAMESPACES)
    return el.text.strip() if el is not None and el.text else ''


def _parse_date(date_str):
    """YYYY-MM-DD formatını DD.MM.YYYY'ye çevirir."""
    if not date_str:
        return ''
    parts = date_str.split('-')
    if len(parts) == 3:
        return f"{parts[2]}.{parts[1]}.{parts[0]}"
    return date_str


def _parse_kdv_orani(value_str):
    """KDV oranını düzgün formata çevirir (20.00 → 20)."""
    if not value_str:
        return ''
    try:
        cleaned = value_str.strip().replace(',', '.')
        kdv = float(cleaned)
        return str(int(kdv)) if kdv.is_integer() else str(kdv).replace('.', ',')
    except (ValueError, TypeError):
        return value_str


def _extract_party_info(party_element):
    """Bir Party elementinden TCKN/VKN, ad/soyad/unvan, adres bilgilerini çıkarır."""
    info = {
        'tckn_vkn': '',
        'soyadi_unvan': '',
        'adi_devami': '',
        'adres': '',
        'vergi_dairesi': ''
    }

    if party_element is None:
        return info

    party = party_element.find('.//cac:Party', NAMESPACES)
    if party is None:
        return info

    # TCKN kontrolü
    tckn = party.find('.//cbc:ID[@schemeID="TCKN"]', NAMESPACES)
    vkn = party.find('.//cbc:ID[@schemeID="VKN"]', NAMESPACES)

    if tckn is not None and tckn.text:
        info['tckn_vkn'] = tckn.text.strip()
        # Kişi adı soyadı
        person = party.find('.//cac:Person', NAMESPACES)
        if person is not None:
            family_name = _get_text(person, './/cbc:FamilyName')
            first_name = _get_text(person, './/cbc:FirstName')
            if family_name:
                info['soyadi_unvan'] = _clean_text(family_name.upper())
            if first_name:
                info['adi_devami'] = _clean_text(first_name.upper())
    elif vkn is not None and vkn.text:
        info['tckn_vkn'] = vkn.text.strip()
        # Şirket adı
        party_name = _get_text(party, './/cac:PartyName/cbc:Name')
        if party_name:
            info['soyadi_unvan'] = _clean_text(party_name.upper())
        else:
            reg_name = _get_text(party, './/cac:PartyLegalEntity/cbc:RegistrationName')
            if reg_name:
                info['soyadi_unvan'] = _clean_text(reg_name.upper())

    # Vergi dairesi
    tax_scheme_name = _get_text(party, './/cac:PartyTaxScheme/cac:TaxScheme/cbc:Name')
    if tax_scheme_name:
        info['vergi_dairesi'] = tax_scheme_name

    # Adres
    address = party.find('.//cac:PostalAddress', NAMESPACES)
    if address is not None:
        parts = []
        for tag in ['cbc:StreetName', 'cbc:CitySubdivisionName', 'cbc:CityName']:
            val = _get_text(address, f'.//{tag}')
            if val:
                parts.append(val)
        country = _get_text(address, './/cac:Country/cbc:Name')
        if country:
            parts.append(country)
        info['adres'] = _clean_text(' '.join(parts))

    return info


def _base_invoice_data():
    """Tüm fatura türleri için ortak boş veri yapısını döndürür."""
    return {
        'İŞLEM': '',
        'KATEGORİ': 'Defter Fişleri',
        'BELGE TURU': '',
        'EVRAK TARİHİ': '',
        'KAYIT TARİHİ': '',
        'SERİ NO': '',
        'EVRAK NO': '',
        'TCKN/VKN': '',
        'VERGİ DAİRESİ': '',
        'SOYADI ÜNVAN': '',
        'ADI DEVAMI': '',
        'ADRES': '',
        'CARİ HESAP': '',
        'KDV İSTİSNASI': '',
        'KOD': '',
        'BELGE TÜRÜ(DB)': '',
        'ALIŞ/SATIŞ TÜRÜ': '',
        'KAYIT ALT TÜRÜ': '',
        'MAL VE HİZMET KODU': '',
        'AÇIKLAMA': '',
        'MİKTAR': '',
        'B.FİYAT': '',
        'TUTAR': '',
        'TEVKİFAT': '',
        'KDV ORANI': '',
        'ÖZEL MATRAH İŞLEM BEDELİ': '',
        'MATRAHTAN DÜŞÜLECEK TUTAR': '',
        'MATRAHA DAHİL OLMAYAN BEDEL': '',
        'KDV TUTARI': '',
        'TOPLAM TUTAR': '',
        'KREDİLİ TUTAR': '',
        'STOPAJ KODU': '',
        'STOPAJ TUTARI': '',
        'DÖNEMSELLİK İLKESİ': '',
        'FAALIYET KODU': '479114',
        'ÖDEME TÜRÜ': ''
    }


def _extract_common_fields(root, data):
    """Fatura numarası, tarih, seri no gibi ortak alanları doldurur."""
    # Fatura numarası
    data['EVRAK NO'] = _get_text(root, './/cbc:ID')

    # Seri No
    serial = _get_text(root, './/cbc:ID[@schemeID="SERIE"]')
    if not serial:
        serial = _get_text(root, './/cbc:SeriesID')
    data['SERİ NO'] = serial

    # Tarih
    issue_date = _get_text(root, './/cbc:IssueDate')
    formatted = _parse_date(issue_date)
    if not formatted:
        order_date = _get_text(root, './/cac:OrderReference/cbc:IssueDate')
        formatted = _parse_date(order_date)
    data['EVRAK TARİHİ'] = formatted
    data['KAYIT TARİHİ'] = formatted

    return data


# ──────────────────────────────────────────────
# 1. Giden e-Arşiv Fatura
# ──────────────────────────────────────────────

def parse_earsiv(xml_path, analysis_data=None):
    """Giden e-Arşiv fatura XML'ini parse eder."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    data = _base_invoice_data()
    data['İŞLEM'] = 'Gelir'
    data['BELGE TURU'] = 'Satış'
    data['BELGE TÜRÜ(DB)'] = 'e-Arşiv Fatura'
    data['ALIŞ/SATIŞ TÜRÜ'] = 'Normal Satışlar'
    data['KAYIT ALT TÜRÜ'] = 'Mal Satışı'

    _extract_common_fields(root, data)

    # Müşteri (alıcı) bilgileri
    customer = root.find('.//cac:AccountingCustomerParty', NAMESPACES)
    info = _extract_party_info(customer)
    data['TCKN/VKN'] = info['tckn_vkn']
    data['SOYADI ÜNVAN'] = info['soyadi_unvan']
    data['ADI DEVAMI'] = info['adi_devami']
    data['ADRES'] = info['adres']

    # Tutar bilgileri
    quantity = _get_text(root, './/cbc:InvoicedQuantity')
    data['MİKTAR'] = quantity if quantity else ''

    tax_exclusive = _get_text(root, './/cbc:TaxExclusiveAmount')
    if tax_exclusive:
        try:
            amount = format_number(float(tax_exclusive.replace(',', '.')))
        except ValueError:
            amount = tax_exclusive
        data['B.FİYAT'] = amount
        data['TUTAR'] = amount

    tax_percent = _get_text(root, './/cac:TaxSubtotal/cbc:Percent')
    data['KDV ORANI'] = _parse_kdv_orani(tax_percent)

    tax_amount = _get_text(root, './/cac:TaxTotal/cbc:TaxAmount')
    if tax_amount:
        try:
            data['KDV TUTARI'] = format_number(float(tax_amount.replace(',', '.')))
        except ValueError:
            data['KDV TUTARI'] = tax_amount

    payable = _get_text(root, './/cbc:PayableAmount')
    if payable:
        try:
            data['TOPLAM TUTAR'] = format_number(float(payable.replace(',', '.')))
        except ValueError:
            data['TOPLAM TUTAR'] = payable

    item_name = _get_text(root, './/cac:Item/cbc:Name')
    data['AÇIKLAMA'] = _clean_text(item_name)

    return data


# ──────────────────────────────────────────────
# 2. Giden e-Fatura
# ──────────────────────────────────────────────

def parse_efatura_giden(xml_path, analysis_data=None):
    """Giden e-Fatura XML'ini parse eder."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    data = _base_invoice_data()
    data['İŞLEM'] = 'Gelir'
    data['BELGE TURU'] = 'Satış'
    data['BELGE TÜRÜ(DB)'] = 'e-Fatura'
    data['ALIŞ/SATIŞ TÜRÜ'] = 'Normal Satışlar'
    data['KAYIT ALT TÜRÜ'] = 'Mal Satışı'

    _extract_common_fields(root, data)

    # Müşteri (alıcı) bilgileri
    customer = root.find('.//cac:AccountingCustomerParty', NAMESPACES)
    info = _extract_party_info(customer)
    data['TCKN/VKN'] = info['tckn_vkn']
    data['SOYADI ÜNVAN'] = info['soyadi_unvan']
    data['ADI DEVAMI'] = info['adi_devami']
    data['ADRES'] = info['adres']

    # Fatura kalemleri
    invoice_lines = root.findall('.//cac:InvoiceLine', NAMESPACES)
    if invoice_lines:
        line = invoice_lines[0]

        item_name = _get_text(line, './/cac:Item/cbc:Name')
        item_desc = _get_text(line, './/cac:Item/cbc:Description')
        data['AÇIKLAMA'] = _clean_text(item_name or item_desc)

        quantity = _get_text(line, './/cbc:InvoicedQuantity')
        data['MİKTAR'] = quantity if quantity else '1'

        price = _get_text(line, './/cac:Price/cbc:PriceAmount')
        if price:
            try:
                data['B.FİYAT'] = format_number(float(price.replace(',', '.')))
            except ValueError:
                data['B.FİYAT'] = price

        line_amount = _get_text(line, './/cbc:LineExtensionAmount')
        if line_amount:
            try:
                data['TUTAR'] = format_number(float(line_amount.replace(',', '.')))
            except ValueError:
                data['TUTAR'] = line_amount

        # KDV bilgileri
        tax_subtotal = line.find('.//cac:TaxTotal/cac:TaxSubtotal', NAMESPACES)
        if tax_subtotal is not None:
            percent = _get_text(tax_subtotal, './/cbc:Percent')
            data['KDV ORANI'] = _parse_kdv_orani(percent)

        tax_amt = _get_text(line, './/cac:TaxTotal/cbc:TaxAmount')
        if tax_amt:
            try:
                data['KDV TUTARI'] = format_number(float(tax_amt.replace(',', '.')))
            except ValueError:
                data['KDV TUTARI'] = tax_amt

    # Toplam tutar
    if data['TUTAR'] and data['KDV TUTARI']:
        try:
            net = float(data['TUTAR'].replace(',', '.'))
            tax = float(data['KDV TUTARI'].replace(',', '.'))
            data['TOPLAM TUTAR'] = format_number(net + tax)
        except (ValueError, TypeError):
            payable = _get_text(root, './/cac:LegalMonetaryTotal/cbc:PayableAmount')
            if payable:
                try:
                    data['TOPLAM TUTAR'] = format_number(float(payable.replace(',', '.')))
                except ValueError:
                    pass
    else:
        payable = _get_text(root, './/cbc:PayableAmount')
        if payable:
            try:
                data['TOPLAM TUTAR'] = format_number(float(payable.replace(',', '.')))
            except ValueError:
                data['TOPLAM TUTAR'] = payable

    # Notlar
    if not data['AÇIKLAMA']:
        notes = root.findall('.//cbc:Note', NAMESPACES)
        if notes:
            data['AÇIKLAMA'] = _clean_text(' | '.join([n.text for n in notes if n.text]))

    return data


# ──────────────────────────────────────────────
# 3. Gelen e-Fatura
# ──────────────────────────────────────────────

def parse_efatura_gelen(xml_path, analysis_data=None):
    """Gelen e-Fatura XML'ini parse eder."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    data = _base_invoice_data()
    data['İŞLEM'] = 'Gider'
    data['BELGE TURU'] = 'Alış'
    data['BELGE TÜRÜ(DB)'] = 'e-Fatura'
    data['ALIŞ/SATIŞ TÜRÜ'] = 'Normal Alım'
    data['KAYIT ALT TÜRÜ'] = '#KONTROL'

    _extract_common_fields(root, data)

    # Satıcı (tedarikçi) bilgileri
    supplier = root.find('.//cac:AccountingSupplierParty', NAMESPACES)
    info = _extract_party_info(supplier)
    data['TCKN/VKN'] = info['tckn_vkn']
    data['SOYADI ÜNVAN'] = info['soyadi_unvan']
    data['ADI DEVAMI'] = info['adi_devami']
    data['ADRES'] = info['adres']

    # Fatura kalemleri
    invoice_lines = root.findall('.//cac:InvoiceLine', NAMESPACES)
    if invoice_lines:
        line = invoice_lines[0]

        item_name = _get_text(line, './/cac:Item/cbc:Name')
        item_desc = _get_text(line, './/cac:Item/cbc:Description')
        description = item_name or item_desc
        data['AÇIKLAMA'] = _clean_text(description)

        # Analiz eşleştirmesi
        if description and analysis_data:
            data['KAYIT ALT TÜRÜ'] = find_matching_analysis(description, analysis_data)

        data['MİKTAR'] = '1'

        # Birim fiyat
        price = _get_text(line, './/cac:Price/cbc:PriceAmount')
        if price:
            try:
                data['B.FİYAT'] = format_number(float(price.replace(',', '.')))
            except ValueError:
                data['B.FİYAT'] = format_number(price)

        # Tutar
        line_amount = _get_text(line, './/cbc:LineExtensionAmount')
        if line_amount:
            try:
                data['TUTAR'] = format_number(float(line_amount.replace(',', '.')))
            except ValueError:
                data['TUTAR'] = format_number(line_amount)

        # KDV bilgileri
        tax_subtotal = line.find('.//cac:TaxTotal/cac:TaxSubtotal', NAMESPACES)
        if tax_subtotal is not None:
            percent = _get_text(tax_subtotal, './/cbc:Percent')
            data['KDV ORANI'] = _parse_kdv_orani(percent)

        tax_amt = _get_text(line, './/cac:TaxTotal/cbc:TaxAmount')
        if tax_amt:
            try:
                data['KDV TUTARI'] = format_number(float(tax_amt.replace(',', '.')))
            except ValueError:
                data['KDV TUTARI'] = format_number(tax_amt)

    # Toplam tutar hesaplama
    if data['TUTAR'] and data['KDV TUTARI']:
        try:
            net = float(data['TUTAR'].replace(',', '.'))
            tax = float(data['KDV TUTARI'].replace(',', '.'))
            data['TOPLAM TUTAR'] = format_number(net + tax)
        except (ValueError, TypeError):
            payable = _get_text(root, './/cac:LegalMonetaryTotal/cbc:PayableAmount')
            if payable:
                try:
                    data['TOPLAM TUTAR'] = format_number(float(payable.replace(',', '.')))
                except ValueError:
                    pass

    # Notlar
    if not data['AÇIKLAMA']:
        notes = root.findall('.//cbc:Note', NAMESPACES)
        if notes:
            data['AÇIKLAMA'] = _clean_text(' | '.join([n.text for n in notes if n.text]))

    return data


# ──────────────────────────────────────────────
# 4. İstisna Fatura
# ──────────────────────────────────────────────

def parse_istisna(xml_path, analysis_data=None):
    """İstisna (KDV istisnalı) fatura XML'ini parse eder."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    data = _base_invoice_data()
    data['İŞLEM'] = 'Gider'
    data['BELGE TURU'] = 'Alış'
    data['BELGE TÜRÜ(DB)'] = 'e-Fatura'
    data['ALIŞ/SATIŞ TÜRÜ'] = 'İstisna'
    data['KAYIT ALT TÜRÜ'] = '#KONTROL'

    _extract_common_fields(root, data)

    # Satıcı bilgileri
    supplier = root.find('.//cac:AccountingSupplierParty', NAMESPACES)
    info = _extract_party_info(supplier)
    data['TCKN/VKN'] = info['tckn_vkn']
    data['SOYADI ÜNVAN'] = info['soyadi_unvan']
    data['ADI DEVAMI'] = info['adi_devami']
    data['ADRES'] = info['adres']

    # KDV İstisna kodu ve açıklaması
    tax_subtotal = root.find('.//cac:TaxTotal/cac:TaxSubtotal', NAMESPACES)
    if tax_subtotal is not None:
        tax_exemption_reason = _get_text(tax_subtotal, './/cbc:TaxExemptionReasonCode')
        tax_exemption_text = _get_text(tax_subtotal, './/cbc:TaxExemptionReason')
        if tax_exemption_reason:
            data['KDV İSTİSNASI'] = f"{tax_exemption_reason} - {tax_exemption_text}" if tax_exemption_text else tax_exemption_reason

    # Fatura kalemleri
    invoice_lines = root.findall('.//cac:InvoiceLine', NAMESPACES)
    if invoice_lines:
        line = invoice_lines[0]

        item_name = _get_text(line, './/cac:Item/cbc:Name')
        item_desc = _get_text(line, './/cac:Item/cbc:Description')
        description = item_name or item_desc
        data['AÇIKLAMA'] = _clean_text(description)

        if description and analysis_data:
            data['KAYIT ALT TÜRÜ'] = find_matching_analysis(description, analysis_data)

        data['MİKTAR'] = '1'

        price = _get_text(line, './/cac:Price/cbc:PriceAmount')
        if price:
            try:
                data['B.FİYAT'] = format_number(float(price.replace(',', '.')))
            except ValueError:
                data['B.FİYAT'] = format_number(price)

        line_amount = _get_text(line, './/cbc:LineExtensionAmount')
        if line_amount:
            try:
                data['TUTAR'] = format_number(float(line_amount.replace(',', '.')))
            except ValueError:
                data['TUTAR'] = format_number(line_amount)

        # KDV - İstisnalarda genellikle 0
        line_tax_subtotal = line.find('.//cac:TaxTotal/cac:TaxSubtotal', NAMESPACES)
        if line_tax_subtotal is not None:
            percent = _get_text(line_tax_subtotal, './/cbc:Percent')
            data['KDV ORANI'] = _parse_kdv_orani(percent)

        tax_amt = _get_text(line, './/cac:TaxTotal/cbc:TaxAmount')
        if tax_amt:
            try:
                data['KDV TUTARI'] = format_number(float(tax_amt.replace(',', '.')))
            except ValueError:
                data['KDV TUTARI'] = format_number(tax_amt)

    # Toplam
    payable = _get_text(root, './/cbc:PayableAmount')
    if payable:
        try:
            data['TOPLAM TUTAR'] = format_number(float(payable.replace(',', '.')))
        except ValueError:
            data['TOPLAM TUTAR'] = payable
    elif data['TUTAR']:
        data['TOPLAM TUTAR'] = data['TUTAR']

    if not data['AÇIKLAMA']:
        notes = root.findall('.//cbc:Note', NAMESPACES)
        if notes:
            data['AÇIKLAMA'] = _clean_text(' | '.join([n.text for n in notes if n.text]))

    return data

# ──────────────────────────────────────────────
# Farklı formatlardaki faturayı ayrıştıran fonksiyon eşleştiricisi
# ──────────────────────────────────────────────

PARSER_MAP = {
    'earsiv': parse_earsiv,
    'efatura_giden': parse_efatura_giden,
    'efatura_gelen': parse_efatura_gelen,
    'istisna': parse_istisna
}
