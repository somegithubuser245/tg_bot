from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

class MenuCallback(CallbackData, prefix="menu"):
    action: str

class FilesCallback(CallbackData, prefix="files"):
    action: str

def main_menu():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Storage')],
            [KeyboardButton(text='Download Files')],
            [KeyboardButton(text='Delete Files')]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return markup


# Function to create the secondary menu
def secondary_menu(option):
    builder = InlineKeyboardBuilder()
    actions = ["voice", "documents", "photos", "videos"]
    for action in actions:
        text = action
        action = f"{option}_{action}"
        builder.button(text=text.capitalize(), callback_data=MenuCallback(action=action).pack())

    builder.button(text="Back", callback_data=MenuCallback(action="back").pack())
    return builder.adjust(1).as_markup()


# Function to create dynamic buttons
def dynamic_buttons(files_array, action):
    builder = InlineKeyboardBuilder()

    for file in files_array:
        builder.button(text=file, callback_data=FilesCallback(action=f'{action}/{file}').pack())

    builder.button(text="Confirm / Back", callback_data = FilesCallback(action="confirm").pack())
    text = action.split('_')[0]
    builder.button(text=f'{text.capitalize()} All', callback_data = FilesCallback(action=f"{text}_all/{action}").pack())

    return builder.adjust(1, True).as_markup()