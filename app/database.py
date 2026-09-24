from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# 1. Önce Render panelindeki DATABASE_URL'i oku. 
# 2. Eğer sunucuda bulamazsa (yani lokal bilgisayarınızda çalışırken) sağdaki yedek adresi kullan.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://forklift_bakim_ve_kiralama_uygulamasi_user:e2zyfKhWDHFGnWJYzCFcUZLUgM71h2bk@://render.com"
)

# Render veya eski platformların PostgreSQL URL'si "postgres://" ile başlayabilir,
# SQLAlchemy "postgresql://" ister — otomatik düzeltiyoruz
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite için özel ayar gerekiyor, PostgreSQL için gerekmez
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()