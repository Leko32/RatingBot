from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def Main():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить баланс")],
        ],
        resize_keyboard=True,
    )
    return keyboard


def RegShift():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="00:00-06:00")],
            [KeyboardButton(text="06:00-12:00")],
            [KeyboardButton(text="12:00-18:00")],
            [KeyboardButton(text="18:00-00:00")],
        ],
        resize_keyboard=True,
    )
    return keyboard


def RegShiftLF():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="00:00-08:00")],
            [KeyboardButton(text="08:00-16:00")],
            [KeyboardButton(text="16:00-00:00")],
        ],
        resize_keyboard=True,
    )
    return keyboard


def RegSecond():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Следующий шаг")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )
    return keyboard


def RegThree(page=1):
    buttons_page1 = [
        "Tanos",
        "Leviks",
        "Guts",
        "Griffit",
        "Mysterion",
        "Scarlett",
        "Eterial",
        "Warden",
        "Butcher",
    ]

    buttons_page2 = [
        "Valkyrie",
        "Gallileo",
        "Ultimatum",
        "Unique",
        "Hunter",
        "Kuber",
        "Jaconda",
        "Quiettt",
        "Alien",
        "Merch",
    ]

    if page == 1:
        buttons = buttons_page1[:] + [
            "➡ Далее"
        ]  # Используем копию, чтобы избежать дублирования
    else:
        buttons = ["⬅ Назад"] + buttons_page2

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=buttons[i]), KeyboardButton(text=buttons[i + 1])]
            for i in range(0, len(buttons) - 1, 2)
        ]
        + (
            [[KeyboardButton(text=buttons[-1])]] if len(buttons) % 2 != 0 else []
        ),  # Избегаем дублирования последней кнопки
        resize_keyboard=True,
    )

    return keyboard


def RegFive():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="LF")], [KeyboardButton(text="MV")]],
        resize_keyboard=True,
    )
    return keyboard
