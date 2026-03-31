from sqlalchemy import Column, Integer, String, Float ,Text
from app.database import Base
from sqlalchemy import DateTime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(Text, nullable=False)
    role = Column(String)


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)

    model_code = Column(String, index=True)
    model_name = Column(String)
    type = Column(String)
    price_usd = Column(Float)

    # eski alan (şimdilik duracak)
    name = Column(String)

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)

    interest_rate = Column(Float, default=18)
    insurance_rate = Column(Float, default=2.5)
    profit_margin = Column(Float, default=10)
    management_fee = Column(Float, default=50)



class MaintenancePackage(Base):
    __tablename__ = "maintenance_packages"

    id = Column(Integer, primary_key=True, index=True)
    machine_model = Column(String)
    recete_id = Column(String, index=True)
    hours = Column(Integer)
    total_cost = Column(Float)


class MaintenanceLine(Base):
    __tablename__ = "maintenance_lines"

    id = Column(Integer, primary_key=True, index=True)
    recete_id = Column(String, index=True)
    line_id = Column(Integer)
    part_code = Column(String)
    description = Column(String)
    quantity = Column(Float)
    unit = Column(String)
    unit_price = Column(Float)
    line_total = Column(Float)


class TireCost(Base):
    __tablename__ = "tire_costs"

    id = Column(Integer, primary_key=True, index=True)
    machine_model = Column(String)
    tire_price_usd = Column(Float)


class SecondHandValue(Base):
    __tablename__ = "second_hand_values"

    id = Column(Integer, primary_key=True, index=True)
    total_hours = Column(Integer)
    percentage = Column(Float)

from datetime import datetime
class RentalOffer(Base):

    __tablename__ = "rental_offers"

    id = Column(Integer, primary_key=True, index=True)

    customer = Column(String)
    email = Column(String)

    model = Column(String)

    machine_count = Column(Integer)

    yearly_hours = Column(Integer)

    survey_score = Column(Integer)

    usage_factor = Column(Float)

    residual_factor = Column(Float)

    monthly_rent = Column(Float)

    pdf_file = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)    