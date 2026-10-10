import os
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

def generate_certificate(output_path: str, name: str, course: str, email: str) -> None:
    output_parent = os.path.dirname(os.fspath(output_path))
    if output_parent:
        os.makedirs(output_parent, exist_ok=True)

    page = landscape(A4)
    c = canvas.Canvas(output_path, pagesize=page)
    width, height = page
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#1D4ED8"))
    c.setLineWidth(5)
    c.rect(24, 24, width - 48, height - 48, fill=0, stroke=1)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 105, "CERTIFICATE OF COMPLETION")
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 145, "This certificate is presented to")
    c.setFillColor(colors.HexColor("#1D4ED8"))
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 195, name)
    c.setFillColor(colors.HexColor("#334155"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 230, "for successfully completing")
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 19)
    c.drawCentredString(width / 2, height - 265, course)
    c.setFillColor(colors.HexColor("#64748B"))
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 48, f"Issued to: {email}")
    c.line(width / 2 - 90, 90, width / 2 + 90, 90)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, 75, "Authorized Signature")
    c.save()
