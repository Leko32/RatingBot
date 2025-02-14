import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from database import engine, User, Balance, add_user, top_admins

# Create a new session
Session = sessionmaker(bind=engine)
session = Session()


# Function to add test users and balances
def add_test_users_and_balances():
    yesterday = datetime.now() - timedelta(days=1)
    admins = list(top_admins.keys())
    users_data = [
        {
            "telegram_id": i+100,
            "nickname": f"User{i}",
            "admin_nickname": admins[i % len(admins)],  # Cycle through admins
            "site": "LF",
            "shift": "00:00-06:00",
        }
        for i in range(1, 31)
    ]

    for user_data in users_data:
        add_user(
            session,
            telegram_id=user_data["telegram_id"],
            nickname=user_data["nickname"],
            admin_nickname=user_data["admin_nickname"],
            site=user_data["site"],
            shift=user_data["shift"],
        )
        new_balance = Balance(
            user_id=session.query(User)
            .filter_by(telegram_id=user_data["telegram_id"])
            .first()
            .id,
            balance=100.0,
            draft="100.0",
            timestamp=yesterday.replace(
                hour=datetime.now().hour,
                minute=datetime.now().minute,
                second=0,
                microsecond=0,
            ),
        )
        session.add(new_balance)

    session.commit()
    print("Test users and balances added successfully.")


if __name__ == "__main__":
    add_test_users_and_balances()

