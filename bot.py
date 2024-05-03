import asyncio
import os, re, logging
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
    start_message = '''
    Hi! I can download videos from Youtube and convert them to .mp3 format.\n
    It is useful for podcasts and audiobooks, which are not available on special services.\n
    Send me the link to the YouTube video.
    '''
    cleaned_text = '\n'.join(line.strip() for line in start_message.split('\n'))
    await message.answer(cleaned_text)

@dp.message(Command('info'))
async def cmd_info(message: types.Message, started_at: str):
    await message.answer(f"Bot started at {started_at}.")

@dp.message()
async def message_handler(msg: types.Message):
    yt_link_pattern = r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
    match = re.search(yt_link_pattern, msg.text)
    video_link = match.group(0)
    video_id = match.group(4)

    if not match:
        print(f"Some error with matching Youtube video link.")
        return
    try:
        if os.path.exists(f"{video_id}.mp3"):
            video = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            print(f"[User {msg.chat.id}] We have video '{video_id}' in cache, sending...")
            await msg.answer_audio(audio=types.FSInputFile(f"{video_id}.mp3"), caption="from cache", title=video.title)
            return
        print(f"[User {msg.chat.id}] Downloading video...")
        video = YouTube(video_link)
        if video.length > 10800:
            print(f"Video too long (>3h)")
            return
        stream = video.streams.filter(only_audio=True).first()
        audio = AudioFileClip(stream.url)
        audio.write_audiofile(f"{video_id}.mp3")
        print(f"[User {msg.chat.id}] '{video.title}' downloaded successfully!")
    except (VideoUnavailable, PytubeError) as e:
        await msg.answer(f"Error: {e}")
        return
    
    await msg.answer_audio(audio=types.FSInputFile(f"{video_id}.mp3"), caption="caption", title=video.title)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# todo:
# del cache after 7 days