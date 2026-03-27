import pandas as pd
from sqlalchemy.orm import Session
from app.models import Machine, MaintenanceLine, MaintenancePackage, TireCost 


def import_maintenance_lines(file_path: str, db: Session):

    df = pd.read_excel(file_path, sheet_name="bakimrecete")

    df.columns = df.columns.str.strip().str.lower()

    db.query(MaintenanceLine).delete()

    last_line_id = 0
    count = 0

    for _, row in df.iterrows():

        # recete_id boşsa geç
        if pd.isna(row["recete_id"]):
            continue

        # fiyat sayısal değilse satırı atla
        try:
            unit_price = float(row["fiyat_usd"])
            line_total = float(row["toplam_usd"])
        except:
            continue

        # line_id boşsa otomatik üret
        if pd.isna(row["line_id"]):
            last_line_id += 1
        else:
            last_line_id = int(row["line_id"])

        line = MaintenanceLine(
            recete_id=str(row["recete_id"]).strip().replace(" ", ""),
            line_id=last_line_id,
            part_code=str(row["kod"]).strip(),
            description=str(row["parca_tanimi"]).strip(),
            quantity=float(row["adet"]),
            unit=str(row["birim"]).strip(),
            unit_price=unit_price,
            line_total=line_total
        )

        db.add(line)
        count += 1

    db.commit()

    print("Bakım reçetesi satırları import edildi:", count)

    
def import_machines(file_path, db):

    db.query(Machine).delete()
    db.commit()

    df = pd.read_excel(file_path, sheet_name="MakineListesi")

    for _, row in df.iterrows():

        machine = Machine(
            id=int(row["id"]),
            model_code=str(row["model_code"]).strip(),
            model_name=str(row["model_name"]).strip(),
            type=str(row["type"]).strip(),
            price_usd=float(row["price_usd"]),
            name=str(row["model_code"]).strip()   # eski sistem kırılmasın
        )

        db.add(machine)

    db.commit()
    
    print("NEW MACHINE IMPORT RUNNING")


def import_maintenance_packages(file_path: str, db: Session):

    df = pd.read_excel(file_path, sheet_name="bakimpaket")

    df.columns = df.columns.str.strip().str.lower()

    db.query(MaintenancePackage).delete()

    for _, row in df.iterrows():

        package = MaintenancePackage(
            recete_id=str(row["recete_id"]),
            total_cost=float(row["toplam_usd"])
        )

        db.add(package)

    db.commit()

def import_tires(file_path, db):

    df = pd.read_excel(file_path, sheet_name="tire")

    df.columns = df.columns.str.strip()

    db.query(TireCost).delete()

    for _, row in df.iterrows():

        if pd.isna(row["model"]):
            continue

        tire = TireCost(
            machine_model=str(row["model"]).strip(),
            tire_price_usd=float(row["tire_price_usd"])
        )

        db.add(tire)

    db.commit()

    print("Tire import tamamlandı")


import pandas as pd

def import_excel(file_path, db):

    import_machines(file_path, db)
    import_maintenance_lines(file_path, db)
    import_maintenance_packages(file_path, db)
    import_tires(file_path, db)

    print("Excel import tamamlandı")