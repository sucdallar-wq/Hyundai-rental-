import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


def _get_smtp_settings():
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_user:
        raise ValueError("SMTP_USER tanımlı değil")
    if not smtp_pass:
        raise ValueError("SMTP_PASS tanımlı değil")

    return {
        "host": smtp_host,
        "port": smtp_port,
        "user": smtp_user,
        "password": smtp_pass,
        "from_email": smtp_from,
    }


def _send_email(to_email, subject, body, pdf_file):
    settings = _get_smtp_settings()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings["from_email"]
    msg["To"] = to_email
    msg.set_content(body)

    with open(pdf_file, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(pdf_file)
        )

    try:
        with smtplib.SMTP_SSL(settings["host"], settings["port"], timeout=20) as smtp:
            smtp.login(settings["user"], settings["password"])
            smtp.send_message(msg)

    except smtplib.SMTPAuthenticationError as e:
        raise Exception(
            "SMTP kimlik doğrulama hatası. Gmail adresi veya App Password yanlış."
        ) from e
    except Exception as e:
        raise Exception(f"Email gönderilemedi: {str(e)}") from e


def send_offer_email(to_email, pdf_file):
    _send_email(
        to_email=to_email,
        subject="Hyundai Forklift Bakım Teklifi",
        body="Bakım teklifiniz ektedir.",
        pdf_file=pdf_file,
    )


def send_rental_offer_email(to_email, pdf_file, customer=None, model=None):
    body = """
    Sayın Müşterimiz,

    Talep etmiş olduğunuz forklift bakım teklifiniz ekte sunulmuştur.

    Sorularınız için bizimle iletişime geçebilirsiniz.

    Saygılarımızla
    Hyundai Yetkili Servis
    """
    if customer or model:
        body += f"\n\nMüşteri: {customer or '-'}\nModel: {model or '-'}"

    if not os.path.exists(pdf_file):
        raise Exception("PDF dosyası bulunamadı")


    _send_email(
        to_email=to_email,
        subject="Hyundai Forklift Kiralama Teklifi",
        body=body,
        pdf_file=pdf_file,
    ) 