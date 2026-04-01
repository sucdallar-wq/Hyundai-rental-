import os
import base64
import urllib.request
import urllib.error
import json
from dotenv import load_dotenv

load_dotenv()


def _send_email(to_email, subject, body, pdf_file):
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "onboarding@resend.dev"))

    if not api_key:
        raise ValueError("RESEND_API_KEY tanımlı değil")

    # PDF'i base64'e çevir
    with open(pdf_file, "rb") as f:
        pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

    filename = os.path.basename(pdf_file)

    payload = {
        "from": f"Hyundai Forklift <{from_email}>",
        "to": [to_email],
        "subject": subject,
        "text": body,
        "attachments": [
            {
                "filename": filename,
                "content": pdf_base64,
            }
        ],
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            response = json.loads(res.read().decode("utf-8"))
            print(f"MAIL SENT: {response}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"MAIL ERROR {e.code}: {error_body}")
        raise RuntimeError(f"Mail gönderilemedi: {error_body}")
    except Exception as e:
        print(f"MAIL ERROR: {e}")
        raise RuntimeError(f"Mail gönderilemedi: {e}")


def send_offer_email(to_email, pdf_file):
    _send_email(
        to_email=to_email,
        subject="Hyundai Forklift Bakım Teklifi",
        body="Bakım teklifiniz ektedir.",
        pdf_file=pdf_file,
    )


def send_rental_offer_email(to_email, pdf_file, customer=None, model=None):
    body = """Sayın Müşterimiz,

Talep etmiş olduğunuz forklift kiralama teklifiniz ekte sunulmuştur.

Sorularınız için bizimle iletişime geçebilirsiniz.

Saygılarımızla
Hyundai Yetkili Servis"""

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
