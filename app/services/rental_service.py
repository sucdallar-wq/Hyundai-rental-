# app/services/rental_service.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

# Bu importlar sizde farklı isimlerde olabilir.
# Örn: Machine / MaintenancePackage / TireCost / SecondHandValue vb.
# Varsa kendi modellerinize göre düzeltin.
from app.models import Machine, MaintenancePackage,TireCost    # sizdeki gerçek isimler
from app.services.maintenance_service import get_rental_maintenance_cost
from app.services.tire_service import calculate_tire_cost

# -----------------------------
# Yardımcı: residual factor
# -----------------------------
def residual_factor_from_usage(usage_factor: float) -> float:
    """
    Kullanım ağırlaştıkça 2.el değeri düşer.
    usage_factor: 1.0 / 1.1 / 1.2
    """
    if usage_factor <= 1.0:
        return 1.0
    if usage_factor <= 1.1:
        return 0.95
    return 0.90

def residual_rate_from_hours(total_hours: float) -> float:

    if total_hours <= 2000:
        return 0.35
    elif total_hours <= 4000:
        return 0.30
    elif total_hours <= 6000:
        return 0.25
    elif total_hours <= 9000:
        return 0.20
    else:
        return 0.15

# -----------------------------
# Yardımcı: saat bazlı bakım paketi seçimi
# -----------------------------
def pick_maintenance_package_hours(total_hours: float) -> int:
    """
    bakimpaket sheet'inde sizde paketler 2000/3000/6000/9000 saat.
    Toplam saat hangi aralıktaysa EN YAKIN ÜST paketi seçiyoruz (ceiling).
    """
    packages = [2000, 3000, 6000, 9000]
    for h in packages:
        if total_hours <= h:
            return h
    return 9000


@dataclass
class RentalInputs:
    model: str
    machine_count: int
    yearly_hours: int
    months: int

    # finans parametreleri
    interest_rate: float           # % örn 18
    insurance_rate: float          # yıllık % örn 2.5 (makine bedeli üzerinden)
    profit_margin: float           # % örn 12
    management_fee_monthly: float  # USD/ay örn 50

    # anket katsayıları
    usage_factor: float            # 1.0 / 1.1 / 1.2
    residual_factor: Optional[float] = None  # verilmezse otomatik


def calculate_rental_offer(inp: RentalInputs, db: Session) -> Dict[str, Any]:
    """
    Filo kiralama hesaplar:
    Makine Bedeli (adet dahil)
    - Residual (2.el)
    + Bakım (anket usage_factor ile)
    + Lastik
    + Sigorta
    + Finansman
    + Yönetim gideri
    + Kar marjı
    = Toplam maliyet
    / Ay
    = Aylık kira (toplam + makine başı)
    """

    # -----------------------------
    # 1) Makine fiyatını DB’den çek
    # -----------------------------
    # Sizin Machine'de alanlar: name/type/price_usd idi.
    # model parametresi "30DN-9V" gibi görünüyor.
    machine = (
        db.query(Machine)
        .filter(Machine.model_code == inp.model)  # sizde type alanı model kodu gibi dönüyor
        .first()
    )
    if not machine:
        raise ValueError(f"Makine bulunamadı: {inp.model}")

    unit_price = float(machine.price_usd or 0)
    machine_price_total = unit_price * inp.machine_count

    # -----------------------------
    # 2) Anket faktörleri
    # -----------------------------
    usage_factor = float(inp.usage_factor or 1.0)
    residual_factor = float(inp.residual_factor) if inp.residual_factor is not None else residual_factor_from_usage(usage_factor)

    # -----------------------------
    # 3) Toplam saat (sözleşme süresince)
    # -----------------------------
    total_hours = float(inp.yearly_hours) * (float(inp.months) / 12.0)

    # -----------------------------
    # 4) Bakım maliyeti:
    # bakimpaket sheet → model + paket saatinden toplam USD
    # recete_id formatı: "{model}_{paket_saat}" örn 30DN-9V_3000
    # -----------------------------
    maintenance_one_machine, pkg_hours = get_rental_maintenance_cost(
        db,
        inp.model,
        total_hours,
        usage_factor
    )

    pkg_recete_id = f"{inp.model}_{pkg_hours}"

    maintenance_total = maintenance_one_machine * inp.machine_count

    # -----------------------------
    # 5) Lastik maliyeti:
    # Şimdilik en güvenli: sabit veya ileride Lastik sheet’inden çekilecek
    # Eğer DB’de lastik tablonuz varsa burada query yaparız.
    # -----------------------------
    
    tire = db.query(TireCost).filter(
        TireCost.machine_model == inp.model
    ).first()
    tire_price = tire.tire_price_usd if tire else 0

    tire_cost = calculate_tire_cost(
        inp.model,
        total_hours,
        tire_price
    )
    
    # ⭐ usage factor etkisi
    tire_cost = tire_cost * usage_factor

    tire_cost_total = tire_cost * inp.machine_count

    # -----------------------------
    # 6) Residual (2.el) değeri:saat ve survey etkili 
    base_residual_rate = residual_rate_from_hours(total_hours)

    residual_factor = residual_factor_from_usage(usage_factor)

    residual_value_total = machine_price_total * base_residual_rate * residual_factor
    
    


    # -----------------------------
    # 7) Sigorta:
    # yıllık: makine bedeli * insurance_rate%
    # sözleşme boyunca: * (months/12)
    # -----------------------------
    insurance_total = machine_price_total * (inp.insurance_rate / 100.0) * (inp.months / 12.0)

    # -----------------------------
    # 8) Ana maliyet (finans + kar öncesi)
    # -----------------------------
    base_cost = (
        machine_price_total
        - residual_value_total
        + maintenance_total
        + tire_cost_total
        + insurance_total
    )

    # -----------------------------
    # 9) Finansman:
    # Basit model: base_cost * interest_rate%
    # (İsterseniz bunu daha sonra IRR/PMT’ye çevirebiliriz)
    # -----------------------------
    finance_cost = base_cost * (inp.interest_rate / 100.0)

    # -----------------------------
    # 10) Yönetim gideri:
    # aylık sabit * ay sayısı
    # -----------------------------
    management_cost = float(inp.management_fee_monthly) * inp.months

    # -----------------------------
    # 11) Kâr marjı:
    # base_cost üzerinden
    # -----------------------------
    profit = base_cost * (inp.profit_margin / 100.0)

    # -----------------------------
    # 12) Toplam maliyet ve aylık kira
    # -----------------------------
    total_cost = base_cost + finance_cost + management_cost + profit
    risk_multiplier = 1 + (usage_factor - 1) * 0.5
    monthly_rent_total = (total_cost / inp.months) * risk_multiplier
    
    monthly_rent_per_machine = monthly_rent_total / inp.machine_count

    # raporlama için breakdown
    return {
        "inputs": {
            "model": inp.model,
            "machine_count": inp.machine_count,
            "yearly_hours": inp.yearly_hours,
            "months": inp.months,
            "interest_rate": inp.interest_rate,
            "insurance_rate": inp.insurance_rate,
            "profit_margin": inp.profit_margin,
            "management_fee_monthly": inp.management_fee_monthly,
            "usage_factor": usage_factor,
            "residual_factor": residual_factor,
            "total_hours": round(total_hours, 2),
            "selected_package_hours": pkg_hours,
            "selected_package_recete_id": pkg_recete_id,
        },
        "breakdown_usd": {
            "machine_price_total": round(machine_price_total, 2),
            "residual_value_total": round(residual_value_total, 2),
            "maintenance_total": round(maintenance_total, 2),
            "tire_cost_total": round(tire_cost_total, 2),
            "insurance_total": round(insurance_total, 2),
            "base_cost": round(base_cost, 2),
            "finance_cost": round(finance_cost, 2),
            "management_cost": round(management_cost, 2),
            "profit": round(profit, 2),
            "total_cost": round(total_cost, 2),
        },
        "result": {
            "monthly_rent_total": round(monthly_rent_total, 2),
            "monthly_rent_per_machine": round(monthly_rent_per_machine, 2),
            "contract_total": round(monthly_rent_total * inp.months, 2),
        }
    }