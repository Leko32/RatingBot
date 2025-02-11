from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv
from datetime import datetime
from pytz import timezone
from sqlalchemy import BigInteger

# Загружаем переменные окружения
load_dotenv()

# Подключение к базе данных с использованием SQLAlchemy
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

# Debugging: print the database connection URL
print("Подключение к базе данных:", engine.url)
print("Строка подключения:", os.getenv("DATABASE_URL"))

# Создаём базовый класс для моделей
Base = declarative_base()


# Определяем таблицу пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    nickname = Column(String, nullable=False)
    admin_nickname = Column(String, nullable=False)
    top_admin = Column(String, nullable=True)  # Добавлено поле для топ-админа
    site = Column(String, nullable=True)  # Добавлено поле для сайта
    shift = Column(String, nullable=True)  # Добавлено поле для смены


# Определяем таблицу балансов
class Balance(Base):
    __tablename__ = "balances"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # ID из таблицы users
    balance = Column(Float, nullable=False)
    draft = Column(String, nullable=False)  # Добавлено поле для полного баланса
    timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone("Europe/Kiev")).replace(
            second=0, microsecond=0
        ),
    )  # Новая колонка для даты и времени (только дата, часы и минуты)


# Словарь соответствий админов и топ-админов
top_admins = {
    "Tanos": "Deadpool",
    "Leviks": "Deadpool",
    "Guts": "Stern",
    "Griffit": "Creator",
    "Mysterion": "Stern",
    "Scarlett": "Stern",
    "Eterial": "Stern",
    "Warden": "Creator",
    "Butcher": "Deadpool",
    "Valkyrie": "Creator",
    "Gallileo": "Deadpool",
    "Ultimatum": "Creator",
    "Unique": "Stern",
    "Hunter": "Stern",
    "Kuber": "Deadpool",
    "Jaconda": "Deadpool",
    "Quiettt": "Stern",
    "Alien": "Stern",
}


# Функция для добавления пользователя
def add_user(session, telegram_id, nickname, admin_nickname, site, shift):
    top_admin = top_admins.get(admin_nickname)  # Получаем топ-админа из словаря
    new_user = User(
        telegram_id=telegram_id,
        nickname=nickname,
        admin_nickname=admin_nickname,
        top_admin=top_admin,  # Добавляем топ-админа
        site=site,  # Добавляем сайт
        shift=shift,  # Добавляем смену
    )

    session.add(new_user)
    session.commit()


# Создаём таблицы в базе (если их нет)
Base.metadata.create_all(engine)

# Создаём сессию для работы с базой
Session = sessionmaker(bind=engine)
session = Session()
