import telebot
import os
import yt_dlp
from flask import Flask
from threading import Thread

# --- НАСТРОЙКИ ---
TOKEN = '9153264392:AAGEo9mavHzPrOl17oJz134XlHiizjxjlN4'
bot = telebot.TeleBot(TOKEN)

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Downloader bot is working!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ЛОГИКА БОТА ---
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Кинь мне ссылку на видео из TikTok, Instagram Reels или YouTube Shorts, и я скачаю его без водяных знаков.\n\n⚠️ Лимит размера видео: 50 МБ.")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('http'))
def download_video(message):
    url = message.text
    msg = bot.reply_to(message, "⏳ Скачиваю видео, подожди...")
    
    # Создаем временную папку для скачивания
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # Настройки yt-dlp (скачиваем mp4, ограничиваем размер)
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'format': 'best[ext=mp4]/best', # Качаем лучшее качество в mp4
        'max_filesize': 50 * 1024 * 1024, # Лимит 50МБ
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Получаем информацию о видео и скачиваем
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id', None)
            ext = info.get('ext', 'mp4')
            filename = f"downloads/{video_id}.{ext}"
        
        # Проверяем, скачалось ли
        if os.path.exists(filename):
            bot.edit_message_text("📤 Отправляю видео...", message.chat.id, msg.message_id)
            
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption="Держи! Скачано через @ТвойБот")
            
            # УДАЛЯЕМ ФАЙЛ С СЕРВЕРА (чтобы не забить память Render)
            os.remove(filename)
            bot.delete_message(message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("❌ Не удалось скачать видео. Возможно, оно больше 50 МБ или ссылка битая.", message.chat.id, msg.message_id)

    except Exception as e:
        print(f"Ошибка: {e}")
        bot.edit_message_text("❌ Ошибка при скачивании. Скорее всего, видео больше 50 МБ (лимит Telegram) или сервис запретил скачивание.", message.chat.id, msg.message_id)
        
        # Чистим папку на случай сбоя
        for f in os.listdir('downloads'):
            os.remove(os.path.join('downloads', f))

# --- ЗАПУСК ---
if __name__ == "__main__":
    keep_alive()
    print("Бот-скачиватель запущен!")
    bot.polling(none_stop=True)
