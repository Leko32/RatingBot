import os
from datetime import datetime
from aiogram import Bot
from dotenv import load_dotenv
import logging

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
MY_ID = os.getenv("MY_ID")

bot = Bot(token=API_TOKEN)

LOG_FILE_PATH = "bot.log"  # Log file inside the project directory


def filter_important_logs(logs):
    important_logs = []
    for line in logs.splitlines():
        if "INFO - Бот завершает работу" in line or "SQL query execution time" in line:
            important_logs.append(line)
    return "\n".join(important_logs)


def log_restart():
    logging.warning("Bot is restarting...")


async def send_logs():
    try:
        if os.path.exists(LOG_FILE_PATH):
            with open(LOG_FILE_PATH, "r") as log_file:
                logs = log_file.read()

            important_logs = filter_important_logs(logs)

            # Clear the log file after sending
            with open(LOG_FILE_PATH, "w") as log_file:
                log_file.write("")

            print("Logs sent and cleared successfully.")
        else:
            print(f"Log file {LOG_FILE_PATH} does not exist.")
    except Exception as e:
        print(f"Failed to send logs: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(send_logs())
