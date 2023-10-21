import telebot
import sqlite3
import os
from telebot import types
from zipfile import ZipFile
from db import BotDB

KEY = '6740161773:AAFmOI5e9YejkxQ4wOXtzGcGauE_iJtycAM'
bot = telebot.TeleBot(KEY)

BotDB = BotDB('imgToZip.db')

@bot.message_handler(commands=['start'])
def welcome(message):

    bot.send_message(message.chat.id,
                     "Привет! Отправь мне файлы, а я выдам тебе зип")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    button1 = types.KeyboardButton("Сделай зипку")
    button2 = types.KeyboardButton("Удали все файлы")
    button3 = types.KeyboardButton('Сохраненные файлы')

    markup.add(button1, button2, button3)

    bot.send_message(message.chat.id,
                     "Привет! Отправь мне файлы, а я выдам тебе зип".format(
                         message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def lalala(message):
    dir = os.listdir('imgs')

    # Checking if the list is empty or not
    if len(dir) == 0:
        bot.send_message(message.chat.id, 'Директория пуста')
    elif len(dir) != 0:
        if message.chat.type == 'private':
            if message.text == 'Сделай зипку':
                zipit(message)
            elif message.text == 'Удали все файлы':
                dir = 'imgs'
                for f in os.listdir(dir):
                    os.remove(os.path.join(dir, f))
                    bot.send_message(message.chat.id, '{} удален'.format(f))
                print('gotovo')
            elif message.text == 'Сохраненные файлы':
                for f in os.listdir('imgs'):
                    bot.send_message(message.chat.id, '{}'.format(f))
    else:
        bot.send_message(message.chat.id, 'Я НЕ ВИКУПАЮ')



def zipit(message):
    bot.send_message(message.chat.id, 'Сжимаю...')
    # Create a ZipFile Object
    with ZipFile('zips/new.zip', 'w') as zip_object:
        # Traverse all files in directory
        for folder_name, sub_folders, file_names in os.walk('imgs'):
            for filename in file_names:
                # Create filepath of files in directory
                file_path = os.path.join(folder_name, filename)
                # Add files to zip file
                zip_object.write(file_path, os.path.basename(file_path))
    # Replace 'document_path' with the path to your document file
    document_path = 'zips/new.zip'

    # Replace 'chat_id' with the chat ID where you want to send the document
    chat_id = message.chat.id

    with open(document_path, 'rb') as document_file:
            bot.send_document(chat_id, document_file)

    os.remove('zips/new.zip')



@bot.message_handler(content_types=['audio', 'photo', 'voice', 'video', 'document',
                                    'text', 'location', 'contact', 'sticker'])
def addfile(message):
    try:
        file_name = message.document.file_name
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('imgs/' + file_name, 'xb') as new_file:
            new_file.write(downloaded_file)
    except:
        bot.send_message(message.chat.id, 'Ошибка. Я принимаю данные только в формате файлов')



#RUN
bot.polling()
