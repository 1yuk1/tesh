import os
import sys
import random
import telebot
import os.path
import time
import datetime
import threading
from importlib import reload
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from importlib import import_module
from telebot import apihelper
from concurrent.futures import ThreadPoolExecutor
from telegram_keyboards import create_del_inline_keyboard  # Импорт функции создания клавиатуры

YOUR_USER_ID = 1162285167

def is_allowed(user_id):
    return user_id == YOUR_USER_ID

def reload_bot(bot):
    bot.stop_polling()
    python = sys.executable
    os.execl(python, python, *sys.argv)

MAX_IMAGE_COUNT = 1000000
IMAGE_SEND_COUNTS = {}
TIMEOUT_DURATION_SEC = 300
USER_TIMEOUTS = {}
USER_TIMEOUT_NOTIFICATIONS = {}

def is_user_in_timeout(user_id):
    if user_id in USER_TIMEOUTS and USER_TIMEOUTS[user_id] > time.time():
        return True
    return False

def update_image_paths(module_name):
    global image_paths
    module_obj = import_module(module_name)
    image_paths = module_obj.image_paths
    return image_paths

class UpdateImagePathsHandler(FileSystemEventHandler):
    def __init__(self, module_name):
        super(UpdateImagePathsHandler, self).__init__()
        self.module_name = module_name

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(self.module_name + '.py'):
            reload_module()

def reload_module():
    global image_paths
    try:
        import image_paths
        reload(image_paths)
        image_paths = image_paths.image_paths
        print("image_paths был успешно обновлен")
    except Exception as e:
        print(f"При обновлении image_paths возникла ошибка: {e}")

def watch_module(module_name, interval=None):
    path = os.path.dirname(os.path.abspath(module_name))
    event_handler = UpdateImagePathsHandler(module_name)
    observer = Observer()
    observer.schedule(event_handler, path)
    observer.start()

    print(f"Начинаю наблюдать за файлом {module_name}.py")
    try:
        while True:
            time.sleep(interval if interval is not None else 1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

bot = telebot.TeleBot('6575718071:AAHBMfdC-7DLWB6Xu17JpOn2cmSjVvKTLX4')

def send_media_file(chat_id, media_path):
    try:
        with open(media_path, 'rb') as file:
            media_ext = os.path.splitext(media_path)[1].lower()
            if media_ext.endswith('.mp4'):
                sent_media = bot.send_video(chat_id, file)
            elif media_ext.endswith('.gif'):
                sent_media = bot.send_document(chat_id, file)
            elif media_ext.endswith('.webm'):
                sent_media = bot.send_video(chat_id, file, supports_streaming=True)
            else:
                sent_media = bot.send_photo(chat_id, file)
            try:
                if hasattr(sent_media, 'photo'):
                    sent_media_id = sent_media.photo[-1].file_id
                else:
                    sent_media_id = 'unknown'
            except TypeError:
                sent_media_id = 'unknown'
            return sent_media_id
    except apihelper.ApiTelegramException as e:
        print(f"Ошибка при отправке медиафайла: {e}")

@bot.message_handler(commands=['image'])
def send_image(message):
    user_id = message.chat.id
    args = message.text.split()
    num_images = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1

    if user_id not in IMAGE_SEND_COUNTS:
        IMAGE_SEND_COUNTS[user_id] = 0

    if is_user_in_timeout(user_id):
        if not USER_TIMEOUT_NOTIFICATIONS.get(user_id, False):
            remaining_time = round(USER_TIMEOUTS[user_id] - time.time())
            bot.send_message(user_id, f"Вы находитесь в тайм-ауте, подождите {remaining_time} секунд.")
            USER_TIMEOUT_NOTIFICATIONS[user_id] = True
        return

    max_images = 1000
    num_images = min(num_images, max_images)

    sent_images = 0

    with ThreadPoolExecutor(max_workers=3) as executor:
        for i in range(num_images):
            if IMAGE_SEND_COUNTS[user_id] >= MAX_IMAGE_COUNT:
                break

            if is_user_in_timeout(user_id):
                break

            IMAGE_SEND_COUNTS[user_id] += 1

            while True:
                random_path = random.choice(image_paths)
                files = os.listdir(random_path)
                media_files = list(filter(lambda x: x.lower().endswith('.png') or x.lower().endswith('.jpg') or x.lower().endswith('.jpeg') or x.lower().endswith('.gif') or x.lower().endswith('.mp4'), files))
                if len(media_files) > 0:
                    break
            if len(media_files) > max_images:
                media_files = random.sample(media_files, max_images)
            media = random.choice(media_files)
            media_path = os.path.join(random_path, media)

            future = executor.submit(send_media_file, message.chat.id, media_path)
            image_id = future.result()
            sent_images += 1
            write_log(media_path, sent_images, image_id)
            time.sleep(1)

            if IMAGE_SEND_COUNTS[user_id] >= MAX_IMAGE_COUNT:
                USER_TIMEOUTS[user_id] = time.time() + TIMEOUT_DURATION_SEC
                USER_TIMEOUT_NOTIFICATIONS[user_id] = False
                bot.send_message(user_id, f"Вы достигли лимита в {MAX_IMAGE_COUNT} изображений. Вам необходимо подождать {TIMEOUT_DURATION_SEC} секунд.")

    if num_images >= 10 and IMAGE_SEND_COUNTS[user_id] < MAX_IMAGE_COUNT:
        bot.send_message(message.chat.id, f"Завершена отправка.")
    return

def ensure_log_directory(log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

log_directory = "log"
ensure_log_directory(log_directory)

def write_log(file_path, sent_images, image_id):
    log_filename = datetime.datetime.now().strftime("%d_%m_%Y_log.txt")
    log_file_path = os.path.join(log_directory, log_filename)
    log_time = datetime.datetime.now().strftime("[%H_%M_%S]")
    log_content = f"{log_time} - \"{file_path}\" (ID: {image_id})\n"
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(log_content)
    
    try:
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_content)
    except OSError as e:
        print(f"Произошла ошибка: {e}")

@bot.message_handler(commands=['reload'])
def handle_reload(message):
    user_id = message.chat.id
    if is_allowed(user_id):
        bot.send_message(user_id, "Перезагрузка бота...")
        reload_bot(bot)
    else:
        bot.send_message(user_id, "У вас нет прав для выполнения этой команды.")

image_paths = update_image_paths("image_paths")

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    user_id = message.chat.id
    USER_TIMEOUTS[user_id] = time.time() + 1  # Устанавливаем тайм-аут на 1 секунду
    USER_TIMEOUT_NOTIFICATIONS[user_id] = False

if __name__ == "__main__":
    try:
        t1 = threading.Thread(target=bot.polling, daemon=True)
        t2 = threading.Thread(target=watch_module, args=("image_paths", 1), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except Exception as e:
        print(f"Произошла ошибка: {e}")
