import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def _get_smtp_settings():
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
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

    # Önce port 587 (STARTTLS) dene, olmazsa 465 (SSL) dene
    try:
        with smtplib.SMTP(settings["host"], 587, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(settings["user"], settings["password"])
            smtp.send_message(msg)
            print("MAIL SENT via port 587")
            return
    except Exception as e:
        print(f"MAIL ERROR port 587: {e}")

    try:
        with smtplib.SMTP_SSL(settings["host"], 465, timeout=20) as smtp:
            smtp.login(settings["user"], settings["password"])
            smtp.send_message(msg)
            print("MAIL SENT via port 465")
            return
    except Exception as e:
        print(f"MAIL ERROR port 465: {e}")
        raise RuntimeError(f"Mail gönderilemedi: {e}")


def send_offer_email(to_email, pdf_file):
    try:
        _send_email(
            to_email=to_email,
            subject="Hyundai Forklift Bakım Teklifi",
            body="Bakım teklifiniz ektedir.",
            pdf_file=pdf_file,
        )
    except Exception as e:
        print(f"MAIL FAIL: {e}")
        raise


def send_rental_offer_email(to_email, pdf_file, customer=None, model=None):
    try:
        body = """
Sayın Müşterimiz,

Talep etmiş olduğunuz forklift kiralama teklifiniz ekte sunulmuştur.

Sorularınız için bizimle iletişime geçebilirsiniz.

Saygılarımızla
Hyundai Yetkili Servis
        """

        if customer or model:
            body += f"\n\nMüşteri: {customer or '-'}\nModel: {model or '-'}"

        if not os.path.exists(pdf_file):
            print("PDF yok, mail gönderilemedi")
            return

        _send_email(
            to_email=to_email,
            subject="Hyundai Forklift Kiralama Teklifi",
            body=body,
            pdf_file=pdf_file,
        )
    except Exception as e:
        print(f"RENTAL MAIL ERROR: {e}")
        raise
