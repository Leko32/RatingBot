import os
from aiogram import Bot
from sqlalchemy.orm import sessionmaker
from database import engine, User, Balance
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=API_TOKEN)

Session = sessionmaker(bind=engine)
session = Session()


def format_draft(draft):
    parts = draft.split("+")
    formatted_parts = []
    for part in parts:
        part = part.strip()
        if "кс" in part.lower():
            part = part.replace("кс", "КС").replace(".", ",")
            formatted_parts.append(part + "$")
        else:
            part = part.replace(".", ",")
            formatted_parts.append(part + "$")
    return " + ".join(formatted_parts)


async def notify_group(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            balance = (
                session.query(Balance)
                .filter_by(user_id=user_id)
                .order_by(Balance.id.desc())
                .first()
            )
            if balance:
                formatted_draft = format_draft(balance.draft)
                message = (
                    f"✅ <b>Смена завершена!</b>\n"
                    f"<b>- Имя:</b> {user.nickname}\n"
                    f"<b>- Смена:</b> {user.shift} ({user.site})\n"
                    f"<b>- Администратор:</b> {user.admin_nickname}\n"
                    f"<b>- Баланс:</b> {formatted_draft}"
                )
                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
                print("Notification sent successfully.")
            else:
                print("No balance found for the user.")
        else:
            print("User not found.")
    except Exception as e:
        print(f"Failed to send notification: {e}")


if __name__ == "__main__":
    import asyncio

    user_id = 1  # Replace with the actual user ID for testing
    asyncio.run(notify_group(user_id))
