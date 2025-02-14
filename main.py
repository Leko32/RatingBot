import asyncio
import logging
import os
import re
from datetime import datetime, time, timedelta
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from database import Balance, User, add_user, engine, top_admins
from keyboards import Main, RegFive, RegSecond, RegShift, RegShiftLF, RegThree
from notify_group import notify_group
from send_logs import log_restart
from sendrating import (send_admin_rating, send_rating, send_top_admin_rating,
                        send_weekly_admin_rating, send_weekly_rating,
                        send_weekly_top_admin_rating)

load_dotenv()

# bot.log - иформация детальная о боте
# detailed.log - информация о перезапуске бота

URL = os.getenv("URL") or ""
CHAT_ID = os.getenv("CHAT_ID") or ""
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN") or ""

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

Session = sessionmaker(bind=engine)
session = Session()

user_data = {}
scheduler = AsyncIOScheduler()

# Configure logging
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,  # Log INFO level
    format="%(asctime)s - %(message)s",
)

detailed_logger = logging.getLogger("detailed")
detailed_handler = logging.FileHandler("detailed.log")
detailed_handler.setLevel(logging.INFO)
detailed_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
detailed_logger.addHandler(detailed_handler)
detailed_logger.setLevel(logging.INFO)


def get_kyiv_time():
    return datetime.now(pytz.timezone("Europe/Kiev"))


def get_today_kyiv():
    return get_kyiv_time().date()


def get_previous_day_kyiv():
    return (get_kyiv_time() - timedelta(days=1)).date()


def get_week_start_kyiv():
    return (get_kyiv_time() - timedelta(days=7)).date()


def is_within_time_range(timestamp, start_time, end_time):
    return start_time <= timestamp.time() <= end_time


def delete_old_balances():
    try:
        nine_days_ago = get_kyiv_time() - timedelta(days=9)
        session.query(Balance).filter(Balance.timestamp < nine_days_ago).delete()
        session.commit()
        detailed_logger.info(
            "SQL query execution time: Old balances deleted successfully."
        )
    except SQLAlchemyError as e:
        session.rollback()
        detailed_logger.error(f"SQL query execution time: Database error: {e}")


async def send_rating_message(chat_id, message):
    try:
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        detailed_logger.error(f"Failed to send message: {e}")


"""Ситстеменые команды"""


@dp.message(Command(commands=["rbalance"]))
async def remove_last_balance(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    try:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            last_balance = (
                session.query(Balance)
                .filter_by(user_id=user.id)
                .order_by(Balance.id.desc())
                .first()
            )
            if last_balance:
                session.delete(last_balance)
                session.commit()
                await message.answer("Последняя запись баланса удалена.")
            else:
                await message.answer("Записи баланса не найдены.")
        else:
            await message.answer(
                "Пользователь не найден. Пожалуйста, зарегистрируйтесь сначала."
            )
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Database error: {e}")
        await message.answer(
            "Произошла ошибка при удалении записи баланса. Попробуйте еще раз."
        )


"""Отправить баланс"""


@dp.message(lambda message: message.text == "Отправить баланс")
async def send_balance_prompt(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    await message.answer(
        "Напиши свой баланс в чат в формате - 112,50"
        "\nИли в формате - 20,50 + КС 100,43",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@dp.message(
    lambda message: re.match(
        r"^\d+([.,]\d{1,2})?(\s*\+\s*\w+\s*\d+([.,]\d{1,2})?)?$",
        message.text,
        re.IGNORECASE,
    )
)
async def catch_balance(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    try:
        draft_text = message.text.strip()  # Full balance string
        balance_text = re.match(
            r"^\d+([.,]\d{1,2})?", draft_text
        ).group()  # Extract first number
        balance_text = balance_text.replace(",", ".")  # Replace comma with dot
        balance = float(balance_text)  # Convert to float
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            new_balance = Balance(user_id=user.id, balance=balance, draft=draft_text)
            session.add(new_balance)
            session.commit()
            await message.answer(f"Баланс записан: ${balance}")
            await notify_group(user.id)  # Notify the group
        else:
            await message.answer(
                "Пользователь не найден. Пожалуйста, зарегистрируйтесь сначала."
            )
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Database error: {e}")
        await message.answer("Произошла ошибка при записи баланса. Попробуйте еще раз.")


"""Кнопка назад"""


@dp.message(lambda message: message.text == "Назад")
async def back(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    try:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            session.query(Balance).filter_by(user_id=user.id).delete()
            session.delete(user)
            session.commit()
        if message.from_user.id in user_data:
            del user_data[message.from_user.id]
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Database error: {e}")
    await message.answer(
        "\nОкей, напиши мне свой ник!",
        reply_markup=types.ReplyKeyboardRemove(),
    )


"""Ник"""


@dp.message(Command(commands=["start"]))
async def start_registration(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    try:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            session.query(Balance).filter_by(user_id=user.id).delete()
            session.delete(user)
            session.commit()
        if message.from_user.id in user_data:
            del user_data[message.from_user.id]
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Database error: {e}")
    await message.answer(
        "Привет! Введи свой ник, который будет отображаться в рейтинге!",
    )


@dp.message(lambda message: message.from_user.id not in user_data)
async def catch_nickname(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    try:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            await message.answer(
                "Нажмите на кнопку отправить баланс!",
                reply_markup=Main(),
            )
            return
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Database error: {e}")
    if message.from_user.id in user_data:
        return  # Ensure the handler is only called once
    nickname = message.text.strip()  # Извлекаем никнейм, убирая пробелы
    user_data[message.from_user.id] = {"nickname": nickname}  # Создаём запись в словаре
    await message.answer(
        f"Окей, твой ник: {nickname}\nТеперь выбери свой сайт!",
        reply_markup=RegFive(),
    )


@dp.message(lambda message: message.text in ["LF", "MV"])
async def catch_site(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    try:
        site = message.text  # Extract the site
        user_id = message.from_user.id
        if user_id in user_data:
            user_data[user_id]["site"] = site  # Save the site in user_data
            if site == "LF":
                await message.answer(
                    f"Вы выбрали сайт: {site}\nТеперь выберите свою смену!",
                    reply_markup=RegShiftLF(),
                )
            else:
                await message.answer(
                    f"Вы выбрали сайт: {site}\nТеперь выберите свою смену!",
                    reply_markup=RegShift(),
                )
        else:
            await message.answer(
                "Ошибка: Никнейм не найден. Пожалуйста, начните регистрацию сначала.",
                reply_markup=RegSecond(),
            )
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Database error: {e}")
        await message.answer(
            "Произошла ошибка при обработке сайта. Попробуйте еще раз."
        )


@dp.message(
    lambda message: message.text
    in [
        "00:00-06:00",
        "06:00-12:00",
        "12:00-18:00",
        "18:00-00:00",
        "00:00-08:00",
        "08:00-16:00",
        "16:00-00:00",
    ]
)
async def catch_shift(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    try:
        shift = message.text  # Extract the shift
        user_id = message.from_user.id
        if user_id in user_data:
            user_data[user_id]["shift"] = shift  # Save the shift in user_data
            await message.answer(
                f"Вы выбрали смену: {shift}\nТеперь нажмите на кнопку Следующий шаг",
                reply_markup=RegSecond(),
            )
        else:
            await message.answer(
                "Ошибка: Никнейм не найден. Пожалуйста, начните регистрацию сначала.",
                reply_markup=RegSecond(),
            )
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Database error: {e}")
        await message.answer(
            "Произошла ошибка при обработке смены. Попробуйте еще раз."
        )


@dp.message(lambda message: message.text == "Следующий шаг")
async def next_step(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    await message.answer("Выберите ник вашего администратора!", reply_markup=RegThree())


@dp.message(lambda message: message.text == "➡ Далее")
async def next_page(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    await message.answer("Страница 2", reply_markup=RegThree(page=2))


@dp.message(lambda message: message.text == "⬅ Назад")
async def previous_page(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    await message.answer("Страница 1", reply_markup=RegThree(page=1))


@dp.message(
    lambda message: message.text in top_admins.keys()
)  # Используем ключи top_admins
async def catch_admin_nickname(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    try:
        admin_nickname = message.text  # Извлекаем ник админа
        user_id = message.from_user.id
        if user_id in user_data:
            nickname = user_data[user_id].get("nickname")
            site = user_data[user_id].get("site")
            shift = user_data[user_id].get("shift")
            if nickname and site and shift:
                user_data[user_id][
                    "admin_nickname"
                ] = admin_nickname  # Сохраняем admin_nickname в словарь
                user = session.query(User).filter_by(telegram_id=user_id).first()
                if user:
                    await message.answer(
                        "У вас уже есть аккаунт. Вы не можете зарегистрироваться снова.",
                        reply_markup=Main(),
                    )
                else:
                    add_user(
                        session,
                        user_id,
                        nickname,
                        admin_nickname,
                        site,
                        shift,
                    )
                    await message.answer(
                        "Регистрация окончена!",
                        reply_markup=Main(),
                    )
            else:
                await message.answer(
                    "Ошибка: Никнейм, сайт или смена не найдены. Пожалуйста, начните регистрацию сначала.",
                    reply_markup=RegSecond(),
                )
        else:
            await message.answer(
                "Ошибка: Никнейм не найден. Пожалуйста, начните регистрацию сначала.",
                reply_markup=RegSecond(),
            )
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Database error: {e}")
        await message.answer(
            "Произошла ошибка при обработке администратора. Попробуйте еще раз."
        )


@dp.message(lambda message: message.chat.id == int(CHAT_ID))
async def ignore_group_messages(message: Message):
    return


@dp.message(lambda message: True)
async def check_registration(message: Message):
    if message.chat.id == int(CHAT_ID):
        return
    try:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            if message.text == "/start":
                await start_registration(message)
            elif message.text == "/rbalance":
                await remove_last_balance(message)
            elif re.match(
                r"^\d+([.,]\d{1,2})?(\s*\+\s*\w+\s*\d+([.,]\d{1,2})?)?$",
                message.text,
                re.IGNORECASE,
            ):
                await catch_balance(message)
            else:
                return  # Ignore other messages from registered users
        else:
            await start_registration(message)
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Database error: {e}")


async def handle_registration_steps(message: Message):
    if message.text == "Следующий шаг":
        await next_step(message)
    elif message.text == "➡ Далее":
        await next_page(message)
    elif message.text == "⬅ Назад":
        await previous_page(message)
    elif message.text in top_admins.keys():
        await catch_admin_nickname(message)
    elif message.text in ["LF", "MV"]:
        await catch_site(message)
    elif message.text in [
        "00:00-06:00",
        "06:00-12:00",
        "12:00-18:00",
        "18:00-00:00",
        "00:00-08:00",
        "08:00-16:00",
        "16:00-00:00",
    ]:
        await catch_shift(message)
    elif message.from_user.id not in user_data:
        await catch_nickname(message)


async def handle_registered_user_message(message: Message):
    # Handle messages from registered users here
    pass


# ВРЕМЯ ДЛЯ РЕЙТИНГА  Операторам


async def main():
    try:
        scheduler.add_job(
            send_rating, "cron", hour=9, minute=15, second=0, timezone="Europe/Kiev"
        )
        scheduler.add_job(
            send_admin_rating,
            "cron",
            hour=9,
            minute=16,
            second=20,
            timezone="Europe/Kiev",
        )
        scheduler.add_job(
            send_top_admin_rating,
            "cron",
            hour=9,
            minute=17,
            second=40,
            timezone="Europe/Kiev",
        )
        scheduler.add_job(
            send_weekly_rating,
            "cron",
            day_of_week="mon",
            hour=9,
            minute=2,
            second=0,
            timezone="Europe/Kiev",
        )
        scheduler.add_job(
            send_weekly_admin_rating,
            "cron",
            day_of_week="mon",
            hour=9,
            minute=5,
            second=20,
            timezone="Europe/Kiev",
        )
        scheduler.add_job(
            send_weekly_top_admin_rating,
            "cron",
            day_of_week="mon",
            hour=9,
            minute=10,
            second=40,
            timezone="Europe/Kiev",
        )
        scheduler.add_job(
            delete_old_balances,
            "cron",
            hour=12,
            minute=0,
            second=10,
            timezone="Europe/Kiev",
        )

        scheduler.start()
        detailed_logger.info("Start polling")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        detailed_logger.info("Бот завершает работу...")
    finally:
        detailed_logger.info("Сессия закрыта.")
        await bot.session.close()


if __name__ == "__main__":
    log_restart()
    asyncio.run(main())
