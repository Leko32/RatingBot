import logging
import os
from datetime import datetime, time, timedelta

import pytz
from aiogram import Bot
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from database import Balance, User, engine

URL = os.getenv("URL")
CHAT_ID = os.getenv("CHAT_ID")
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

bot = Bot(token=API_TOKEN)

Session = sessionmaker(bind=engine)
session = Session()


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


async def send_rating_message(chat_id, message):
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Failed to send message: {e}")


async def send_rating():
    start_time = datetime.now()
    users = session.query(User).all()
    rating_message = "<b>🔥Рейтинг операторов🔥</b>\n\n"
    user_balances = []
    start_time = time(9, 0)
    end_time = time(9, 0)
    previous_day = get_previous_day_kyiv()
    today = get_today_kyiv()

    for user in users:
        balances = session.query(Balance).filter_by(user_id=user.id).all()
        total_balance = round(
            sum(
                balance.balance
                for balance in balances
                if (
                    balance.timestamp.date() == previous_day
                    and is_within_time_range(
                        balance.timestamp, start_time, time(23, 59)
                    )
                )
                or (
                    balance.timestamp.date() == today
                    and is_within_time_range(balance.timestamp, time(0, 0), end_time)
                )
            ),
            2,
        )
        user_balances.append(
            (
                user.site,
                user.nickname,
                total_balance,
                user.admin_nickname,
                user.top_admin,
            )
        )

    user_balances.sort(key=lambda x: x[2], reverse=True)
    user_balances = user_balances[:10]  # Limit to top 10

    for i, (site, nickname, total_balance, admin_nickname, top_admin) in enumerate(
        user_balances, start=1
    ):
        emoji = ["🏆", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        if i <= 3:
            rating_message += f"<b>{emoji} {site} ~ {nickname.upper()} ({total_balance:.2f}$) - {admin_nickname} - {top_admin}</b>\n"
        else:
            rating_message += f"{emoji} {site} ~ {nickname} ({total_balance:.2f}$) - {admin_nickname} - {top_admin}\n"
        if i == 3:
            rating_message += "\n"

    await send_rating_message(CHAT_ID, rating_message)
    end_time = datetime.now()
    logging.warning(f"send_rating executed in {end_time - start_time}")


async def send_admin_rating():
    start_time = datetime.now()
    admins = (
        session.query(User.admin_nickname, User.top_admin, User.site).distinct().all()
    )
    admin_balances = {}
    start_time = time(9, 0)
    end_time = time(9, 0)
    previous_day = get_previous_day_kyiv()
    today = get_today_kyiv()

    for admin in admins:
        admin_nickname, top_admin, site = admin
        operators = session.query(User).filter_by(admin_nickname=admin_nickname).all()
        total_balance = sum(
            sum(
                balance.balance
                for balance in session.query(Balance)
                .filter_by(user_id=operator.id)
                .all()
                if (
                    balance.timestamp.date() == previous_day
                    and is_within_time_range(
                        balance.timestamp, start_time, time(23, 59)
                    )
                )
                or (
                    balance.timestamp.date() == today
                    and is_within_time_range(balance.timestamp, time(0, 0), end_time)
                )
            )
            for operator in operators
        )
        admin_balances[admin_nickname] = (site, total_balance, top_admin)

    sorted_admins = sorted(admin_balances.items(), key=lambda x: x[1][1], reverse=True)

    admin_rating_message = "<b>🎯Рейтинг админов🎯</b>\n\n"
    for i, (admin_nickname, (site, total_balance, top_admin)) in enumerate(
        sorted_admins, start=1
    ):
        emoji = ["🏆", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        if i <= 3:
            admin_rating_message += f"<b>{emoji} {site} ~ {admin_nickname} ({total_balance:.2f}$) - {top_admin}</b>\n"
        else:
            admin_rating_message += f"{emoji} {site} ~ {admin_nickname} ({total_balance:.2f}$) - {top_admin}\n"
        if i == 3:
            admin_rating_message += "\n"

    await send_rating_message(CHAT_ID, admin_rating_message)
    end_time = datetime.now()
    logging.warning(f"send_admin_rating executed in {end_time - start_time}")


async def send_top_admin_rating():
    start_time = datetime.now()
    top_admins = session.query(User.top_admin).distinct().all()
    top_admin_balances = {}
    start_time = time(9, 0)
    end_time = time(9, 0)
    previous_day = get_previous_day_kyiv()
    today = get_today_kyiv()

    for top_admin in top_admins:
        top_admin_name = top_admin[0]
        total_balance = 0

        admins = session.query(User).filter_by(top_admin=top_admin_name).all()
        for admin in admins:
            admin_balance = sum(
                balance.balance
                for balance in session.query(Balance).filter_by(user_id=admin.id).all()
                if (
                    balance.timestamp.date() == previous_day
                    and is_within_time_range(
                        balance.timestamp, start_time, time(23, 59)
                    )
                )
                or (
                    balance.timestamp.date() == today
                    and is_within_time_range(balance.timestamp, time(0, 0), end_time)
                )
            )
            admin_balance += sum(
                balance.balance
                for operator in session.query(User)
                .filter_by(admin_nickname=admin.nickname)
                .all()
                for balance in session.query(Balance)
                .filter_by(user_id=operator.id)
                .all()
                if (
                    balance.timestamp.date() == previous_day
                    and is_within_time_range(
                        balance.timestamp, start_time, time(23, 59)
                    )
                )
                or (
                    balance.timestamp.date() == today
                    and is_within_time_range(balance.timestamp, time(0, 0), end_time)
                )
            )
            total_balance += admin_balance

        top_admin_balances[top_admin_name] = total_balance

    sorted_top_admins = sorted(
        top_admin_balances.items(), key=lambda x: x[1], reverse=True
    )

    top_admin_rating_message = "<b>💎Рейтинг топ админов💎</b>\n\n"
    for i, (top_admin_name, total_balance) in enumerate(sorted_top_admins, start=1):
        emoji = ["🏆", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        if i == 1:
            top_admin_rating_message += (
                f"{emoji} <b>{top_admin_name.upper()} ({total_balance:.2f}$)</b>\n"
            )
        else:
            top_admin_rating_message += (
                f"{emoji} {top_admin_name.upper()} ({total_balance:.2f}$)\n"
            )

    await send_rating_message(CHAT_ID, top_admin_rating_message)
    end_time = datetime.now()
    logging.warning(f"send_top_admin_rating executed in {end_time - start_time}")


async def send_weekly_rating():
    start_time = datetime.now()
    users = session.query(User).all()
    rating_message = "<b>🔥Еженедельный рейтинг операторов🔥</b>\n\n"
    user_balances = []
    start_time = time(9, 0)
    end_time = time(9, 0)
    week_start = get_week_start_kyiv()
    today = get_today_kyiv()

    for user in users:
        balances = session.query(Balance).filter_by(user_id=user.id).all()
        total_balance = round(
            sum(
                balance.balance
                for balance in balances
                if (
                    balance.timestamp.date() == week_start
                    and is_within_time_range(
                        balance.timestamp, start_time, time(23, 59)
                    )
                )
                or (
                    balance.timestamp.date() > week_start
                    and balance.timestamp.date() < today
                )
                or (
                    balance.timestamp.date() == today
                    and is_within_time_range(balance.timestamp, time(0, 0), end_time)
                )
            ),
            2,
        )
        user_balances.append(
            (
                user.site,
                user.nickname,
                total_balance,
                user.admin_nickname,
                user.top_admin,
            )
        )

    user_balances.sort(key=lambda x: x[2], reverse=True)
    user_balances = user_balances[:10]  # Limit to top 10

    for i, (site, nickname, total_balance, admin_nickname, top_admin) in enumerate(
        user_balances, start=1
    ):
        emoji = ["🏆", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        if i <= 3:
            rating_message += f"<b>{emoji} {site} ~ {nickname.upper()} ({total_balance:.2f}$) - {admin_nickname} - {top_admin}</b>\n"
        else:
            rating_message += f"{emoji} {site} ~ {nickname} ({total_balance:.2f}$) - {admin_nickname} - {top_admin}\n"
        if i == 3:
            rating_message += "\n"

    await send_rating_message(CHAT_ID, rating_message)
    end_time = datetime.now()
    logging.warning(f"send_weekly_rating executed in {end_time - start_time}")


async def send_weekly_admin_rating():
    start_time = datetime.now()
    admins = (
        session.query(User.admin_nickname, User.top_admin, User.site).distinct().all()
    )
    admin_balances = {}
    start_time = time(9, 0)
    end_time = time(9, 0)
    week_start = get_week_start_kyiv()
    today = get_today_kyiv()

    for admin in admins:
        admin_nickname, top_admin, site = admin
        operators = session.query(User).filter_by(admin_nickname=admin_nickname).all()
        total_balance = sum(
            sum(
                balance.balance
                for balance in session.query(Balance)
                .filter_by(user_id=operator.id)
                .all()
                if (
                    balance.timestamp.date() == week_start
                    and is_within_time_range(
                        balance.timestamp, start_time, time(23, 59)
                    )
                )
                or (
                    balance.timestamp.date() > week_start
                    and balance.timestamp.date() < today
                )
                or (
                    balance.timestamp.date() == today
                    and is_within_time_range(balance.timestamp, time(0, 0), end_time)
                )
            )
            for operator in operators
        )
        admin_balances[admin_nickname] = (site, total_balance, top_admin)

    sorted_admins = sorted(admin_balances.items(), key=lambda x: x[1][1], reverse=True)

    admin_rating_message = "<b>🎯Еженедельный рейтинг админов🎯</b>\n\n"
    for i, (admin_nickname, (site, total_balance, top_admin)) in enumerate(
        sorted_admins, start=1
    ):
        emoji = ["🏆", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        if i <= 3:
            admin_rating_message += f"<b>{emoji} {site} ~ {admin_nickname} ({total_balance:.2f}$) - {top_admin}</b>\n"
        else:
            admin_rating_message += f"{emoji} {site} ~ {admin_nickname} ({total_balance:.2f}$) - {top_admin}\n"
        if i == 3:
            admin_rating_message += "\n"

    await send_rating_message(CHAT_ID, admin_rating_message)
    end_time = datetime.now()
    logging.warning(f"send_weekly_admin_rating executed in {end_time - start_time}")


async def send_weekly_top_admin_rating():
    start_time = datetime.now()
    top_admins = session.query(User.top_admin).distinct().all()
    top_admin_balances = {}
    start_time = time(9, 0)
    end_time = time(9, 0)
    week_start = get_week_start_kyiv()
    today = get_today_kyiv()

    for top_admin in top_admins:
        top_admin_name = top_admin[0]
        total_balance = 0

        admins = session.query(User).filter_by(top_admin=top_admin_name).all()
        for admin in admins:
            admin_balance = sum(
                balance.balance
                for balance in session.query(Balance).filter_by(user_id=admin.id).all()
                if (
                    balance.timestamp.date() == week_start
                    and is_within_time_range(
                        balance.timestamp, start_time, time(23, 59)
                    )
                )
                or (
                    balance.timestamp.date() > week_start
                    and balance.timestamp.date() < today
                )
                or (
                    balance.timestamp.date() == today
                    and is_within_time_range(balance.timestamp, time(0, 0), end_time)
                )
            )
            admin_balance += sum(
                balance.balance
                for operator in session.query(User)
                .filter_by(admin_nickname=admin.nickname)
                .all()
                for balance in session.query(Balance)
                .filter_by(user_id=operator.id)
                .all()
                if (
                    balance.timestamp.date() == week_start
                    and is_within_time_range(
                        balance.timestamp, start_time, time(23, 59)
                    )
                )
                or (
                    balance.timestamp.date() > week_start
                    and balance.timestamp.date() < today
                )
                or (
                    balance.timestamp.date() == today
                    and is_within_time_range(balance.timestamp, time(0, 0), end_time)
                )
            )
            total_balance += admin_balance

        top_admin_balances[top_admin_name] = total_balance

    sorted_top_admins = sorted(
        top_admin_balances.items(), key=lambda x: x[1], reverse=True
    )

    top_admin_rating_message = "<b>💎Еженедельный рейтинг топ админов💎</b>\n\n"
    for i, (top_admin_name, total_balance) in enumerate(sorted_top_admins, start=1):
        emoji = ["🏆", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        if i == 1:
            top_admin_rating_message += (
                f"{emoji} <b>{top_admin_name.upper()} ({total_balance:.2f}$)</b>\n"
            )
        else:
            top_admin_rating_message += (
                f"{emoji} {top_admin_name.upper()} ({total_balance:.2f}$)\n"
            )

    await send_rating_message(CHAT_ID, top_admin_rating_message)
    end_time = datetime.now()
    logging.warning(f"send_weekly_top_admin_rating executed in {end_time - start_time}")
