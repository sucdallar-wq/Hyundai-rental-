from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Railway'de DATABASE_URL otomatik gelir
# Local'de SQLite kullanmaya devam eder
DATABASE_URL = "postgresql://postgres:JqKQMrxDdVGgXAbsjkEqQMqvljugErKT@hopper.proxy.rlwy.net:34902/railway"

# Railway PostgreSQL URL'si "postgres://" ile başlar,
# SQLAlchemy "postgresql://" ister — otomatik düzeltiyoruz
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite için özel ayar gerekiyor, PostgreSQL için gerekmez
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()