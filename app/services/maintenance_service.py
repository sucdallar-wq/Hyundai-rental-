from sqlalchemy.orm import Session
from app.models import MaintenanceLine, MaintenancePackage


# ------------------------------------
# Servis bakım reçetesi
# ------------------------------------

def get_maintenance_lines(db: Session, model: str, hours: int):

    recete_id = f"{model}_{hours}"

    lines = db.query(MaintenanceLine).filter(
        MaintenanceLine.recete_id == recete_id
    ).order_by(MaintenanceLine.line_id).all()

    return lines


# ------------------------------------
# Servis bakım toplam maliyet
# ------------------------------------

def get_maintenance_cost(db: Session, model: str, hours: int):

    recete_id = f"{model}_{hours}"

    package = db.query(MaintenancePackage).filter(
        MaintenancePackage.recete_id == recete_id
    ).first()

    if not package:
        return None

    return package.total_cost


# ------------------------------------
# Kiralama için paket seçimi
# ------------------------------------

def pick_maintenance_package_hours(total_hours):

    packages = [2000, 3000, 4000, 6000, 9000]

    for p in packages:
        if total_hours <= p:
            return p

    return 9000


# ------------------------------------
# Kiralama bakım maliyeti
# ------------------------------------

def get_rental_maintenance_cost(db, model, total_hours, usage_factor):

    packages = [2000, 3000, 6000, 9000]

    selected = None

    for p in packages:
        if total_hours <= p:
            selected = p
            break

    if selected is None:
        selected = 9000

    recete_id = f"{model}_{selected}"

    pkg = (
        db.query(MaintenancePackage)
        .filter(MaintenancePackage.recete_id == recete_id)
        .first()
    )

    if not pkg:
        raise ValueError(f"Bakım paketi bulunamadı: {recete_id}")

    # ⭐⭐⭐ ORANSAL BAKIM MALİYETİ
    hourly_cost = float(pkg.total_cost) / selected

    real_cost = hourly_cost * total_hours

    real_cost = real_cost * usage_factor

    return real_cost, selected