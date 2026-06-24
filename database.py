# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Шлях до вашого файлу бази даних (пам'ятаємо про правильний шлях)
SQLALCHEMY_DATABASE_URL = "sqlite:///./conference.db"

# Створюємо двигун для роботи з SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Потрібно суто для SQLite
)

# Створюємо фабрику сесій
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Функція-залежність (Dependency) для отримання доступу до БД в ендпоінтах
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()