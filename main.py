from aiogram import Bot, types, F, Router, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.methods.send_document import SendDocument

import config
import keyboards
import logging
from db import DatabaseManager
import os
import asyncio

dp = Dispatcher()
bot = Bot(config.API_TOKEN)
db_manager = DatabaseManager(config.DATABASE)

@dp.message(F.text.in_({"Storage", "Download Files", "Delete Files"}))
async def handle_menu_actions(message: types.Message):
    text = message.text
    user_id = message.from_user.id
    if text == "Storage":
        answer = await db_manager.update_total_file_size(user_id, 0)
        await message.answer(f'You have {answer} left')
    elif text == "Download Files":
        await message.answer("Choose repository:", reply_markup=keyboards.secondary_menu("download"))
    elif text == "Delete Files":
        await message.answer("Choose repository:", reply_markup=keyboards.secondary_menu("delete"))

@dp.callback_query(keyboards.MenuCallback.filter())
async def handle_callback_query(query: types.CallbackQuery, callback_data: keyboards.MenuCallback):
    action = callback_data.action
    file_type = action.split('_')[-1]
    print(file_type)
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if action == "back":
        await bot.send_message(chat_id,"Choose an option:", reply_markup=keyboards.main_menu())
    elif file_type in ["voice", "documents", "photos", "videos"]:
        files = await db_manager.get_files_by_type(user_id, file_type)
        await query.message.edit_text("Tap on files you want to download. When you're"
                                      " done, press confirm:", reply_markup=keyboards.dynamic_buttons(files, action))

@dp.callback_query(keyboards.FilesCallback.filter())
async def handle_callback_query(query: types.CallbackQuery, callback_data: keyboards.MenuCallback):
    action = callback_data.action
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if action == "confirm":
        await bot.send_message(chat_id,"Alright", reply_markup=keyboards.main_menu())
        return 0

    server_file_path = action.split('_')[-2]  + '_' + action.split('_')[-1]
    operation = action.split('_')[0]

    if action.split('/')[0] == "download_all":
        file_type = action.split('/')[-1].split('_')[-1]
        print(file_type)
        files = await db_manager.get_files_by_type(user_id, file_type)
        for file in files:
            file_path = f'downloads/{user_id}/{file_type}/{file}'
            file_to_send = FSInputFile(file_path)
            await bot.send_document(chat_id, file_to_send)

        await bot.send_message(chat_id, "Downloaded successfully", reply_markup=keyboards.main_menu())

    elif action.split('/')[0] == "delete_all":
        file_type = action.split('/')[-1].split('_')[-1]
        print(file_type)
        files = await db_manager.get_files_by_type(user_id, file_type)
        for file in files:
            file_path = f'downloads/{user_id}/{file_type}/{file}'
            size = os.path.getsize(file_path)
            os.remove(file_path)
            await db_manager.delete_file(user_id, f'{file_type}/{file}', size)

        await bot.send_message(chat_id, "Deleted successfully", reply_markup=keyboards.main_menu())

    elif operation == "download":
        file_path = f'downloads/{user_id}/{server_file_path}'
        file_to_send = FSInputFile(file_path)
        await bot.send_document(chat_id, file_to_send)

    elif operation == "delete":
        file_path_to_remove = f'downloads/{user_id}/{server_file_path}'
        size = os.path.getsize(file_path_to_remove)
        os.remove(file_path_to_remove)
        await db_manager.delete_file(user_id, server_file_path, size)


@dp.message(F.text == '/start')
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if not await db_manager.check_user_exists(user_id):
        downloads_dir = 'downloads'  # Specify the downloads directory
        main_folder = os.path.join(downloads_dir, str(user_id))
        subfolders = ["videos", "photos", "voice", "documents"]

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


    await bot.send_message(message.chat.id, f"Hello, {message.from_user.username}!"
                                            f"\n I'm a bot that can help you manage your files. "
                                            f"I can store files up to {config.MAX_STORAGE_PER_USER / 1000000} MB. "
                                            f"I'm basically a little cloud storage. ")

    await message.answer("Choose an option:", reply_markup=keyboards.main_menu())

async def download_file(user_id, file_id):
    file = await bot.get_file(file_id)
    file_link = file.file_path
    file_name = file_link.split("/")[-1]
    file_type = file_link.split('/')[0]

    if not await db_manager.check_file_exists(file_link):

        storage_state = await db_manager.add_file(user_id, file_link, file_name, file_type, file.file_size)

        file_path = f'downloads/{user_id}/{file_type}/{file_name}'
        await bot.download_file(file_link, destination=file_path)

        return storage_state

    else: # File already exists
        print(f"File already exists for user {user_id}")
        return "File already exists"

@dp.message(F.content_type.in_({'document', 'photo', 'video', 'voice'}))
async def handle_files(message: types.Message):
    user_id = message.from_user.id
    file = message.document or message.video or message.voice or message.photo[-1]
    file_path = await download_file(user_id, file.file_id)
    await message.answer(file_path)

async def main():
    await db_manager.create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())