import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


# ⭐ ROOT BUL
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

# ⭐ FONT PATH
FONT_DIR = os.path.join(BASE_DIR, "fonts")

# ⭐ PDF PATH
PDF_DIR = os.path.join(BASE_DIR, "pdf")

# ⭐ PDF klasörü oluştur
os.makedirs(PDF_DIR, exist_ok=True)

# ⭐ FONT REGISTER
pdfmetrics.registerFont(
    TTFont("DejaVu", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
)

pdfmetrics.registerFont(
    TTFont("DejaVu-Bold", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
)

# =========================================================
# PATH AYARLARI
# app/services/pdf_service.py içinden:
# BASE_DIR => app klasörü
# PDF_DIR  => app/pdf
# =========================================================

os.makedirs(PDF_DIR, exist_ok=True)

FONT_NAME = "DejaVu"
FONT_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "hyundai_logo.png")


# =========================================================
# ORTAK YARDIMCI FONKSİYONLAR
# =========================================================
def _register_font():
    try:
        pdfmetrics.getFont(FONT_NAME)
    except KeyError:
        if os.path.exists(FONT_PATH):
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        else:
            raise FileNotFoundError(f"Font dosyası bulunamadı: {FONT_PATH}")


def _safe_str(value, default=""):
    if value is None:
        return default
    return str(value)


def _safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_money(value):
    return f"{_safe_float(value):,.2f} USD"


def _new_page(c):
    c.showPage()
    _register_font()


def _draw_header(c, title):
    width, height = A4
    y = height - 60

    try:
        if os.path.exists(LOGO_PATH):
            c.drawImage(LOGO_PATH, 40, y - 20, width=120, height=40, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    c.setFont(FONT_NAME, 18)
    c.drawString(180, y, "HYUNDAI FORKLIFT")

    y -= 28
    c.setFont(FONT_NAME, 14)
    c.drawString(180, y, title)

    return width, height, y


def _draw_footer(c, salesman=None):
    c.setFont(FONT_NAME, 9)
    c.drawString(40, 40, "Hyundai Yetkili Servis")
    c.drawString(40, 25, "servis@bayi.com")
    c.drawString(400, 25, "www.hyundai-forklift.com")
    if salesman:
        c.setFont(FONT_NAME, 9)
        c.drawString(400, 40, f"Teklifi Hazırlayan: {salesman}")

def _ensure_space(c, y, needed_space, title=None, salesman=None):
    if y < needed_space:
        _draw_footer(c, salesman)
        _new_page(c)
        _, height, y = _draw_header(c, title or "")
        y -= 30
    return y


# =========================================================
# MAINTENANCE PDF
# =========================================================
def create_maintenance_pdf(
    recete_id,
    lines,
    discount,
    customer,
    machine_model,
    hours,
    salesman,
):
    _register_font()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = _safe_str(machine_model, "MODEL").replace("/", "-").replace("\\", "-").replace(" ", "_")
    file_name = f"maintenance_offer_{safe_model}_{timestamp}.pdf"
    file_path = os.path.join(PDF_DIR, file_name)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height, y = _draw_header(c, "Bakım Teklifi")

    teklif_no = f"HYD-MNT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    c.setFont(FONT_NAME, 11)

    y -= 30
    c.drawString(40, y, f"Teklif No : {teklif_no}")
    c.drawString(350, y, f"Tarih : {datetime.today().strftime('%d.%m.%Y')}")

    y -= 25
    c.drawString(40, y, f"Müşteri : {_safe_str(customer, '-')}")
    y -= 20
    c.drawString(40, y, f"Makine Modeli : {_safe_str(machine_model, '-')}")
    y -= 20
    c.drawString(40, y, f"Bakım Paketi : {_safe_str(hours, '-')} Saat")

    if recete_id:
        y -= 20
        c.drawString(40, y, f"Reçete ID : {_safe_str(recete_id)}")

    y -= 35

    cell_style = ParagraphStyle(
        name="cell",
        fontName="DejaVu",
        fontSize=9,
        leading=11,
    )

    data = [["Kod", "Parça", "Adet", "Birim", "Toplam"]]

    total = 0
    for l in lines:
        line_total = round(l.line_total, 2)
        total += line_total

        data.append([
            Paragraph(str(l.part_code), cell_style),
            Paragraph(str(l.description), cell_style),
            Paragraph(str(l.quantity), cell_style),
            Paragraph(str(l.unit), cell_style),
            Paragraph(f"{line_total:,.2f} USD", cell_style),
        ])

    table = Table(data, colWidths=[80, 240, 50, 60, 90])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("ALIGN", (4, 1), (4, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    w, h = table.wrap(0, 0)

    if y - h < 140:
        _draw_footer(c, salesman)
        c.showPage()
        width, height, y = _draw_header(c, "Bakım Teklifi")
        y -= 40

    table.drawOn(c, 40, y - h)
    y = y - h - 25

    c.line(40, y, 550, y)
    y -= 20

    discount_amount = total * discount / 100
    final_total = total - discount_amount

    c.setFont("DejaVu", 11)
    c.drawRightString(545, y, f"Toplam: {total:,.2f} USD")

    y -= 18
    c.drawRightString(545, y, f"İndirim: {discount_amount:,.2f} USD")

    y -= 25
    c.setFont("DejaVu", 13)
    c.drawRightString(545, y, f"GENEL TOPLAM: {final_total:,.2f} USD")

    y -= 28
    c.setFont("DejaVu", 11)
    c.drawRightString(545, y, "Fiyatlara KDV dahil değildir")

    _draw_footer(c, salesman)
    c.save()

    return file_path


# =========================================================
# RENTAL PDF
# Müşteriye gösterilebilir sade format
# İç maliyet kırılımı YOK
# =========================================================


def create_rental_offer_pdf(
    customer,
    email,
    model,
    machine_count,
    yearly_hours,
    survey_score,
    usage_factor,
    residual_factor,
    scenarios,
    salesman=None
    ):

    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)

    teklif_no = datetime.now().strftime("HYD-RNT-%Y%m%d%H%M%S")
    file_name = f"rental_offer_{model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(PDF_DIR, file_name)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # ---------- HEADER BANNER ----------
    c.setFillColor(HexColor("#002c5f"))
    c.rect(0, height - 80, width, 80, fill=1)

    c.setFillColor(white)
    c.setFont("DejaVu-Bold", 24)
    c.drawString(40, height - 50, "HYUNDAI FORKLIFT")

    c.setFont("DejaVu", 14)
    c.drawString(40, height - 70, "Kiralama Teklifi")

    # ---------- BASIC INFO ----------
    c.setFillColor(black)
    c.setFont("DejaVu", 11)

    y = height - 120

    c.drawString(40, y, f"Teklif No : {teklif_no}")
    c.drawString(300, y, f"Tarih : {datetime.now().strftime('%d.%m.%Y')}")

    y -= 20
    c.drawString(40, y, f"Müşteri : {customer}")
    c.drawString(300, y, f"E-posta : {email}")

    y -= 20
    c.drawString(40, y, f"Makine Modeli : {model}")
    c.drawString(300, y, f"Adet : {machine_count}")

    y -= 20
    c.drawString(40, y, f"Yıllık Kullanım : {yearly_hours} saat")

    # ---------- RISK LEVEL ----------
    risk_label = "HAFİF"
    risk_color = HexColor("#27ae60")

    if survey_score > 25:
        risk_label = "ORTA"
        risk_color = HexColor("#f1c40f")

    if survey_score > 40:
        risk_label = "AĞIR"
        risk_color = HexColor("#e74c3c")

    y -= 40

    c.setFillColor(risk_color)
    c.roundRect(40, y, width - 80, 30, 8, fill=1)

    c.setFillColor(white)
    c.setFont("DejaVu-Bold", 13)
    c.drawCentredString(width / 2, y + 8, f"Kullanım Seviyesi : {risk_label}")

    # ---------- BEST SCENARIO ----------
    best = next((s for s in scenarios if s["months"] == 36), scenarios[0])

    y -= 60

    c.setFillColor(HexColor("#002c5f"))
    c.roundRect(40, y, width - 80, 40, 10, fill=1)

    c.setFillColor(white)
    c.setFont("DejaVu-Bold", 14)
    c.drawCentredString(
        width / 2,
        y + 14,
        f" Önerilen Plan : {best['months']} Ay   |   Aylık Kira : {best['monthly_per_machine']:.2f} USD"
    )

    # ---------- TABLE ----------
    y -= 80

    c.setFillColor(black)
    c.setFont("DejaVu-Bold", 12)

    c.drawString(60, y, "Vade")
    c.drawString(140, y, "Aylık / Makine")
    c.drawString(300, y, "Aylık Toplam")
    c.drawString(450, y, "Sözleşme Toplamı")

    y -= 20
    c.setFont("DejaVu", 11)

    for s in scenarios:

        if s["months"] == best["months"]:
            c.setFillColor(HexColor("#e8f0ff"))
            c.rect(50, y - 5, width - 100, 18, fill=1)
            c.setFillColor(black)

        monthly_total = s["monthly_per_machine"] * machine_count
        contract_total = monthly_total * s["months"]

        c.drawString(60, y, f"{s['months']} Ay")
        c.drawString(140, y, f"{s['monthly_per_machine']:.2f} USD")
        c.drawString(300, y, f"{monthly_total:.2f} USD")
        c.drawString(450, y, f"{contract_total:.2f} USD")

        y -= 20

    # ---------- FOOTER ----------
    y -= 30

    c.setFont("DejaVu", 9)
    c.drawString(40, y, "• Teklif belirtilen kullanım şartlarına göre hazırlanmıştır ve 15 gün için geçerlidir.")
    y -= 12
    c.drawString(40, y, "• Nihai ticari şartlar sipariş ve sözleşme aşamasında netleşir.")
    y -= 12
    c.drawString(40, y, "• Fiyatlara aksi belirtilmedikçe KDV dahil değildir.")

    y -= 30
    c.setFont("DejaVu-Bold", 10)
    c.drawString(40, y, "Hyundai Yetkili Servis")

    if salesman:
        c.setFont("DejaVu", 9)
        c.drawString(400, y, f"Teklifi Hazırlayan: {salesman}")

    c.save()

    return file_path