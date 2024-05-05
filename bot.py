import asyncio
import os, re, logging, time
from dotenv import dotenv_values
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from datetime import datetime
from pytube import YouTube
from pytube.exceptions import VideoUnavailable, PytubeError
from moviepy.editor import *

logging.basicConfig(level=logging.INFO)

CONFIG = dotenv_values()

bot = Bot(CONFIG['API_TOKEN'])
dp = Dispatcher()
dp["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    """Стартовая команда."""
    start_message = '''
    Hi! I can download videos from Youtube and convert them to .mp3 format.\n
    It is useful for podcasts and audiobooks, which are not available on special services.\n
    Send me the link to the YouTube video.
    '''
    cleaned_text = '\n'.join(line.strip() for line in start_message.split('\n'))
    await message.answer(cleaned_text)

@dp.message(Command('info'))
async def cmd_info(message: types.Message, started_at: str):
    """Команда для просмтра uptime бота."""
    await message.answer(f"Bot started at {started_at}.")

@dp.message()
async def message_handler(msg: types.Message):
    """Обработчик входящего текста на наличие ссылки на видео 
    на Youtube и последующего преобразования в формат mp3."""
    yt_link_pattern = r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
    match = re.search(yt_link_pattern, msg.text)

    if not match:
        print(f"Some error with matching Youtube video link.")
        return
    try:
        video_link = match.group(0)
        video_id = match.group(4)
        if os.path.exists(f"{video_id}.mp3"):
            video = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            print(f"[User {msg.chat.id}] We have video '{video_id}' in cache, sending...")
            await msg.answer_audio(audio=types.FSInputFile(f"cache/{video_id}.mp3"), caption="from cache", title=video.title)
            return
        print(f"[User {msg.chat.id}] Downloading video...")
        video = YouTube(video_link)
        if video.length > 10800:
            print(f"Video too long (>3h). We will not download it.")
            return
        stream = video.streams.filter(only_audio=True).first()
        audio = AudioFileClip(stream.url)
        audio.write_audiofile(f"cache/{video_id}.mp3")
        print(f"[User {msg.chat.id}] '{video.title}' downloaded successfully!")
    except (VideoUnavailable, PytubeError) as e:
        await msg.answer(f"Error: {e}")
        return
    await msg.answer_audio(audio=types.FSInputFile(f"cache/{video_id}.mp3"), caption="caption", title=video.title)

def delete_old_files(directory_path):
    """Удаляет файлы старше 7 дней в указанной директории."""
    current_time = datetime.now()
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if (current_time - file_mod_time).days > 7:
            os.remove(file_path)
            print(f"File {filename} was deleted because it was created more than 7 days ago.")

async def schedule_deletion(directory_path, interval=604800):  # interval в секундах (7 дней)
    """Запускает функцию удаления каждые 7 дней."""
    logging.info("Schedule_deletion started.")
    while True:
        delete_old_files(directory_path)
        await asyncio.sleep(interval)

async def main():
    deletion_task = asyncio.create_task(schedule_deletion('cache/'))
    await dp.start_polling(bot)
    await deletion_task

if __name__ == "__main__":
    asyncio.run(main())