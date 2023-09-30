import telebot
from telebot import types
from images import send_image, send_media_file

bot = telebot.TeleBot('6575718071:AAHBMfdC-7DLWB6Xu17JpOn2cmSjVvKTLX4')

# Создаем клавиатуру с кнопками
def create_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    image_button = types.InlineKeyboardButton("Отправить изображение", callback_data="send_image")
    stop_button = types.InlineKeyboardButton("Остановить", callback_data="stop")
    menu_button = types.InlineKeyboardButton("Меню", callback_data="menu")
    markup.add(image_button, stop_button, menu_button)
    return markup

# Обработчик команды /start или /menu
@bot.message_handler(commands=['start', 'menu'])
def send_menu(message):
    chat_id = message.chat.id
    markup = create_menu_keyboard()
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id

    if call.data == "send_image":
        # Здесь добавьте код для отправки изображений (ваша текущая логика)
        bot.send_message(chat_id, "Вы выбрали отправку изображения.")
    elif call.data == "stop":
        # Здесь добавьте код для остановки текущей функциональности (если есть)
        bot.send_message(chat_id, "Вы выбрали остановить текущее действие.")
    elif call.data == "menu":
        # Отправляем меню снова, чтобы пользователь мог выбрать другую функцию
        markup = create_menu_keyboard()
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

if __name__ == "__main__":
    bot.polling(none_stop=True)