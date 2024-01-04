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

@dp.message(F.text == '/start')                                                                                                            # start handler
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
                                            f"\n I'm a bot that can help you manage your files."
                                            f"I can store files up to {config.MAX_STORAGE_PER_USER / (1024*1024)} MB. "
                                            f"I'm basically a little cloud storage."
                                            f"Send me any file you want. You can than download it or delete it.")

    await message.answer("Choose an option:", reply_markup=keyboards.main_menu())

@dp.message(F.text.in_({"Available storage", "Download Files", "Delete Files"}))                                                             # main handler
async def handle_menu_actions(message: types.Message):
    text = message.text
    user_id = message.from_user.id
    if text == "Available storage":
        answer = await db_manager.update_total_file_size(user_id, 0)
        await message.answer(f'You have {answer} left', reply_markup=keyboards.main_menu())
    elif text == "Download Files":
        await message.answer("Choose repository:", reply_markup=keyboards.secondary_menu("download"))
    elif text == "Delete Files":
        await message.answer("Choose repository:", reply_markup=keyboards.secondary_menu("delete"))

@dp.callback_query(keyboards.MenuCallback.filter())                                                                                          # folders handler
async def handle_callback_query(query: types.CallbackQuery, callback_data: keyboards.MenuCallback):
    action = callback_data.action
    file_type = action.split('_')[-1]
    file_action = action.split('_')[0]
    print(file_type)
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if action == "back":
        await query.message.delete()
        await bot.send_message(chat_id,"Choose an option:", reply_markup=keyboards.main_menu())
    elif file_type in ["voice", "documents", "photos", "videos"]:
        files = await db_manager.get_files_by_type(user_id, file_type)
        await query.message.edit_text(f"Tap on files you want to {file_action}. When you're"
                                      " done, press confirm:", reply_markup=keyboards.dynamic_buttons(files, file_action, file_type))

@dp.callback_query(keyboards.FilesCallback.filter())                                                                                          # files manager handler
async def handle_callback_query(query: types.CallbackQuery, callback_data: keyboards.MenuCallback):
    action = callback_data.action
    print(action)
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    splitted = action.split('/')
    operation = splitted[0]

    if operation == "confirm":
        action_beforehead = action.split('/')[-1]
        print(action)
        await query.message.delete()
        await bot.send_message(chat_id, f'Which files do you want to {action_beforehead}',
                               reply_markup=keyboards.secondary_menu(action_beforehead))

    elif operation == "download_all":
        file_type = action.split('/')[-1]
        print(file_type)
        files = await db_manager.get_files_by_type(user_id, file_type)
        for file in files:
            file_path = f'downloads/{user_id}/{file_type}/{file}'
            file_to_send = FSInputFile(file_path)
            await bot.send_document(chat_id, file_to_send)
        await query.message.delete()
        await bot.send_message(chat_id, "All files downloaded successfully")
        await bot.send_message(chat_id, "Which files do you want to download?"
                               , reply_markup=keyboards.secondary_menu("download"))

    elif action.split('/')[0] == "delete_all":
        file_type = action.split('/')[-1]
        print(file_type)
        files = await db_manager.get_files_by_type(user_id, file_type)
        for file in files:
            file_path = f'downloads/{user_id}/{file_type}/{file}'
            size = os.path.getsize(file_path)
            os.remove(file_path)
            await db_manager.delete_file(user_id, f'{file_type}/{file}', size)

        await query.message.delete()
        await bot.send_message(chat_id, "All files deleted successfully")
        await bot.send_message(chat_id, "Which files do you want to delete?"
                               , reply_markup=keyboards.secondary_menu("delete"))
    else:
        server_file_path = splitted[1] + '/' + splitted[2]
        if operation == "download":
            file_path = f'downloads/{user_id}/{server_file_path}'
            file_to_send = FSInputFile(file_path)
            await bot.send_document(chat_id, file_to_send)

        elif operation == "delete":
            file_path_to_remove = f'downloads/{user_id}/{server_file_path}'
            size = os.path.getsize(file_path_to_remove)
            os.remove(file_path_to_remove)
            await db_manager.delete_file(user_id, server_file_path, size)

@dp.message(F.content_type.in_({'document', 'photo', 'video', 'voice'}))                                                             # files handler
async def handle_files(message: types.Message):
    user_id = message.from_user.id
    file = message.document or message.video or message.voice or message.photo[-1]
    response = await download_file(user_id, file.file_id)
    await message.answer(response)

async def download_file(user_id, file_id):
    file = await bot.get_file(file_id)
    file_link = file.file_path
    file_name = file_link.split("/")[-1]
    file_type = file_link.split('/')[0]

    if not await db_manager.check_file_exists(file_link):

        storage_state = await db_manager.add_file(user_id, file_link, file_name, file_type, file.file_size)

        if storage_state == 'Not enough storage space':
            return storage_state

        file_path = f'downloads/{user_id}/{file_type}/{file_name}'
        await bot.download_file(file_link, destination=file_path)

        return f'File "{file_name}" added to {file_type} repository'

    else: # File already exists
        print(f"File already exists for user {user_id}")
        return "File already exists"

async def main():
    await db_manager.create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())