# Telegram Rating Bot

This **Telegram bot** is designed for user registration, tracking operator balances, and generating rankings (for operators, administrators, and top administrators). The bot provides the following features:

* Register users by collecting their nickname, site, shift, and administrator.
* Accept balance entries via messages.
* Delete the latest balance entries.
* Send ranking messages (daily and weekly) based on balance calculations.
* Periodically clean up outdated entries using a scheduler (APScheduler).
* Log bot activity to `bot.log` (general information) and `detailed.log` (detailed information and errors).

## Technologies

* **Python 3.8+**
* [aiogram](https://docs.aiogram.dev/) — Library for creating Telegram bots.
* [SQLAlchemy](https://www.sqlalchemy.org/) — ORM for database interaction.
* [APScheduler](https://apscheduler.readthedocs.io/) — Task scheduler.
* [python-dotenv](https://github.com/theskumar/python-dotenv) — For loading environment variables from the `.env` file.

## Features

### **User Registration and Deletion:**

* Upon `/start`, the bot prompts for the nickname and guides the user through the registration process (selecting a site, shift, and administrator).

### **Balance Tracking:**

* Users can send their balance in formats like `112.50` or `20.50 + CS 100.43`. The bot records this balance in the database and sends a notification to the group.

### **Balance Deletion:**

* The `/rbalance` command allows users to delete the last balance entry (for registered users).

### **Rankings:**

* The bot generates rankings for operators, administrators, and top administrators based on the cumulative balance, and sends them to a specified chat (daily and weekly).

### **Scheduler:**

* APScheduler is used to periodically delete outdated balance entries (e.g., entries older than 9 days).

### **Logging:**

* Bot activity is logged to `bot.log` and `detailed.log` files, with details of errors and activity.

## Project Structure

```
├── main.py            # Main bot execution file
├── database.py        # Database handling (models, connection, functions)
├── keyboards.py       # Defining keyboards for bot interaction
├── sendrating.py      # Module for sending different rankings
├── send_logs.py       # Logging bot restarts and errors
├── notify_group.py    # Group notifications (e.g., new balance entries)
├── .env               # Environment variables (should not be pushed to the repository)
├── .gitignore         # File to exclude from version control (e.g., .env, pycache)
├── requirements.txt   # Project dependencies
└── README.md          # This file
```

## Setup

### 1. Clone the repository:

```bash
git clone https://github.com/yourusername/RatingBot.git
```

### 2. Install dependencies:

Make sure **Python 3.x** is installed. Install the required dependencies using:

```bash
pip install -r requirements.txt
```

### 3. Set up the bot:

* Create a `.env` file and insert your **Telegram Bot API Token**.
* Example:

  ```env
  TELEGRAM_API_TOKEN=your_telegram_bot_api_token
  ```

### 4. Run the bot:

```bash
python main.py
```

Your bot should now be up and running! 🎉

---

## Contributing

Feel free to fork the repository and submit pull requests for improvements or new features. If you encounter any bugs or issues, please report them in the **Issues** section.

---

### 🚀 Keep your users' ratings high! Enjoy coding and managing your bot! 😎


