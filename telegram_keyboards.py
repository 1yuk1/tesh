from telebot import types

def create_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    image_button = types.KeyboardButton("/image")
    stop_button = types.KeyboardButton("/stop")

    keyboard.add(image_button, stop_button)

    return keyboard

def create_del_inline_keyboard(file_path):
    inline_keyboard = types.InlineKeyboardMarkup()
    file_del_button = types.InlineKeyboardButton(text="Удалить файл", callback_data=f"del_{file_path}")
    inline_keyboard.add(file_del_button)

    return inline_keyboard
