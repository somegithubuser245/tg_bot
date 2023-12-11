from aiogram import Bot, types, F, Router, Dispatcher
import logging
from db import DatabaseManager
import os
import asyncio
import hashlib
import io

API_TOKEN = '6740161773:AAFmOI5e9YejkxQ4wOXtzGcGauE_iJtycAM'

dp = Dispatcher()
bot = Bot(API_TOKEN)
db_manager = DatabaseManager('file_storage.db')

async def main():
    await db_manager.create_tables()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

async def download_file(user_id, file_id, file_type):
    if not await db_manager.check_user_exists(user_id):
        downloads_dir = 'downloads'  # Specify the downloads directory
        main_folder = os.path.join(downloads_dir, str(user_id))
        subfolders = ["video", "photo", "voice", "doc"]

        # Create the main folder
        if not os.path.exists(main_folder):
            os.makedirs(main_folder)

        # Create subfolders
        for folder in subfolders:
            subfolder_path = os.path.join(main_folder, folder)
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)

        await db_manager.add_user(user_id)

        print(f"Folder structure created for user {user_id}")


    file = await bot.get_file(file_id)
    file_link = file.file_path
    print(file_link)

    if not await db_manager.check_file_exists(file_link):

        file_extension = ''
        if file_type == 'photo':
            file_extension = '.jpg'
        elif file_type == 'video':
            file_extension = '.mp4'
        elif file_type == 'voice':
            file_extension = '.ogg'

        file_name = await db_manager.add_file(user_id, file_link, file_type, file_extension, file.file_size)
        file_path = f'downloads/{user_id}/{file_type}/{file_name}'
        await bot.download_file(file_link, destination=file_path)
        return file_path

    else: # File already exists
        print(f"File already exists for user {user_id}")
        return "File already exists"

@dp.message(F.content_type == 'photo')
async def handle_photos(message: types.Message):
    user_id = message.from_user.id
    photo = message.photo[-1]
    file_path = await download_file(user_id, photo.file_id, "photo")
    await message.answer(file_path)

@dp.message(F.content_type == 'video')
async def handle_videos(message: types.Message):
    user_id = message.from_user.id
    video = message.video
    file_path = await download_file(user_id, video.file_id, "video")
    await message.answer(file_path)

@dp.message(F.content_type == 'voice')
async def handle_voices(message: types.Message):
    user_id = message.from_user.id
    voice = message.voice
    file_path = await download_file(user_id, voice.file_id, "voice")
    await message.answer(file_path)

@dp.message(F.content_type == 'document')
async def handle_documents(message: types.Message):
    user_id = message.from_user.id
    document = message.document
    file_path = await download_file(user_id, document.file_id, "doc")
    await message.answer(file_path)

if __name__ == "__main__":
    asyncio.run(main())