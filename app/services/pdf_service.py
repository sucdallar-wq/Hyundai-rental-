import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONT_DIR = os.path.join(BASE_DIR, "fonts")
PDF_DIR = os.path.join(BASE_DIR, "pdf")
os.makedirs(PDF_DIR, exist_ok=True)

pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))

FONT_NAME = "DejaVu"
FONT_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo3.png")


def _register_font():
    try:
        pdfmetrics.getFont(FONT_NAME)
    except KeyError:
        if os.path.exists(FONT_PATH):
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))


def _safe_str(value, default=""):
    return str(value) if value is not None else default


def _safe_float(value, default=0.0):
    try:
        return float(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _draw_banner(c, subtitle):
    width, height = A4
    c.setFillColor(HexColor("#002c5f"))
    c.rect(0, height - 80, width, 80, fill=1)
    c.setFillColor(white)
    c.setFont("DejaVu-Bold", 22)
    c.drawString(40, height - 48, "HYUNDAI FORKLIFT")
    c.setFont("DejaVu", 13)
    c.drawString(40, height - 68, subtitle)
    try:
        if os.path.exists(LOGO_PATH):
            c.drawImage(LOGO_PATH, width - 160, height - 74, width=120, height=55,
                        preserveAspectRatio=True, mask='auto')
    except Exception:
        pass
    return height - 90


def _draw_footer(c, salesman=None):
    c.setFont(FONT_NAME, 9)
    c.drawString(40, 40, "Hyundai Yetkili Servis")
    c.drawString(40, 25, "servis@bayi.com")
    c.drawString(400, 25, "www.hyundai-forklift.com")
    if salesman:
        c.drawString(400, 40, f"Teklifi Hazırlayan: {salesman}")


# =========================================================
# MAINTENANCE PDF
# =========================================================
def create_maintenance_pdf(
    recete_id, lines, discount, customer,
    machine_model, hours, salesman,
    road_km=0, road_rate_usd=0,
):
    _register_font()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = _safe_str(machine_model, "MODEL").replace("/", "-").replace("\\", "-").replace(" ", "_")
    file_name = f"maintenance_offer_{safe_model}_{timestamp}.pdf"
    file_path = os.path.join(PDF_DIR, file_name)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = _draw_banner(c, "Bakım Teklifi")

    teklif_no = f"HYD-MNT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    c.setFillColor(black)
    c.setFont(FONT_NAME, 11)

    y -= 10
    c.drawString(40, y, f"Teklif No : {teklif_no}")
    c.drawString(350, y, f"Tarih : {datetime.today().strftime('%d.%m.%Y')}")
    y -= 22
    c.drawString(40, y, f"Müşteri : {_safe_str(customer, '-')}")
    y -= 20
    c.drawString(40, y, f"Makine Modeli : {_safe_str(machine_model, '-')}")
    y -= 20
    c.drawString(40, y, f"Bakım Paketi : {_safe_str(hours, '-')} Saat")
    if recete_id:
        y -= 20
        c.drawString(40, y, f"Reçete ID : {_safe_str(recete_id)}")

    y -= 30

    cell_style = ParagraphStyle(name="cell", fontName="DejaVu", fontSize=9, leading=11)

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

    road_km = _safe_float(road_km, 0)
    road_rate_usd = _safe_float(road_rate_usd, 0)
    road_total = road_km * road_rate_usd

    if road_km > 0 and road_rate_usd > 0:
        data.append([
            Paragraph("Yol", cell_style),
            Paragraph("Yol Ücreti", cell_style),
            Paragraph(f"{road_km:.0f}", cell_style),
            Paragraph("km", cell_style),
            Paragraph(f"{road_total:,.2f} USD", cell_style),
        ])
        total += road_total

    row_count = len(data)
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#002c5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("ALIGN", (4, 1), (4, -1), "RIGHT"),
        ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if road_km > 0 and road_rate_usd > 0:
        table_style.append(("BACKGROUND", (0, row_count - 1), (-1, row_count - 1), HexColor("#e8f0ff")))

    table = Table(data, colWidths=[80, 240, 50, 60, 90])
    table.setStyle(TableStyle(table_style))

    w, h = table.wrap(0, 0)

    if y - h < 140:
        _draw_footer(c, salesman)
        c.showPage()
        y = _draw_banner(c, "Bakım Teklifi")
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
    c.setFont("DejaVu-Bold", 13)
    c.drawRightString(545, y, f"GENEL TOPLAM: {final_total:,.2f} USD")
    y -= 28
    c.setFont("DejaVu", 11)
    c.drawRightString(545, y, "Fiyatlara KDV dahil değildir")

    _draw_footer(c, salesman)
    c.save()
    return file_path


# =========================================================
# RENTAL PDF
# =========================================================
def create_rental_offer_pdf(
    customer, email, model, machine_count, yearly_hours,
    survey_score, usage_factor, residual_factor, scenarios, salesman=None
):
    os.makedirs(PDF_DIR, exist_ok=True)

    teklif_no = datetime.now().strftime("HYD-RNT-%Y%m%d%H%M%S")
    file_name = f"rental_offer_{model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(PDF_DIR, file_name)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = _draw_banner(c, "Kiralama Teklifi")

    c.setFillColor(black)
    c.setFont("DejaVu", 11)

    y -= 10
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

    risk_label = "HAFİF"
    risk_color = HexColor("#27ae60")
    if survey_score > 25:
        risk_label = "ORTA"
        risk_color = HexColor("#f1c40f")
    if survey_score > 40:
        risk_label = "AĞIR"
        risk_color = HexColor("#e74c3c")

    y -= 35
    c.setFillColor(risk_color)
    c.roundRect(40, y, width - 80, 28, 8, fill=1)
    c.setFillColor(white)
    c.setFont("DejaVu-Bold", 12)
    c.drawCentredString(width / 2, y + 8, f"Kullanım Seviyesi : {risk_label}")

    best = next((s for s in scenarios if s["months"] == 36), scenarios[0])
    y -= 50
    c.setFillColor(HexColor("#002c5f"))
    c.roundRect(40, y, width - 80, 38, 10, fill=1)
    c.setFillColor(white)
    c.setFont("DejaVu-Bold", 13)
    c.drawCentredString(
        width / 2, y + 13,
        f" Önerilen Plan : {best['months']} Ay   |   Aylık Kira : {best['monthly_per_machine']:.2f} USD"
    )

    y -= 70
    c.setFillColor(black)
    c.setFont("DejaVu-Bold", 11)
    c.drawString(60, y, "Vade")
    c.drawString(160, y, "Aylık / Makine")
    c.drawString(300, y, "Aylık Toplam")
    c.drawString(440, y, "Sözleşme Toplamı")
    y -= 5
    c.line(50, y, width - 40, y)
    y -= 15

    c.setFont("DejaVu", 11)
    for s in scenarios:
        if s["months"] == best["months"]:
            c.setFillColor(HexColor("#e8f0ff"))
            c.rect(50, y - 5, width - 100, 18, fill=1)
            c.setFillColor(black)
        monthly_total = s["monthly_per_machine"] * machine_count
        contract_total = monthly_total * s["months"]
        c.drawString(60, y, f"{s['months']} Ay")
        c.drawString(160, y, f"{s['monthly_per_machine']:.2f} USD")
        c.drawString(300, y, f"{monthly_total:.2f} USD")
        c.drawString(440, y, f"{contract_total:.2f} USD")
        y -= 22

    y -= 20
    c.setFont("DejaVu", 9)
    c.drawString(40, y, "• Teklif belirtilen kullanım şartlarına göre hazırlanmıştır ve 15 gün için geçerlidir.")
    y -= 12
    c.drawString(40, y, "• Nihai ticari şartlar sipariş ve sözleşme aşamasında netleşir.")
    y -= 12
    c.drawString(40, y, "• Fiyatlara aksi belirtilmedikçe KDV dahil değildir.")

    _draw_footer(c, salesman)
    c.save()
    return file_path
