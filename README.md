# Telegram Cloud Storage Bot

A Telegram bot that serves as a personal cloud storage solution, allowing users to store and manage various types of files directly through Telegram. The bot supports multiple file types including documents, photos, videos, and voice messages.

## Features

- Personal cloud storage for each user
- Support for multiple file types:
  - Documents
  - Photos
  - Videos
  - Voice messages
- File management operations:
  - Upload files
  - Download files
  - Delete files
  - View available storage space
- Storage quota management (500MB per user)
- Organized file storage in separate directories
- User-friendly keyboard interface
- Duplicate file detection

## Prerequisites

- Python 3.7+
- SQLite database
- Telegram Bot Token

## Required Python Packages

```
aiogram
aiosqlite
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/somegithubuser245/tg_bot/
cd telegram-storage-bot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Configure the bot:
   - Create a `config.py` file with the following content:
```python
API_TOKEN = 'your_telegram_bot_token'
DATABASE = 'path_to_your_database.db'
MAX_STORAGE_PER_USER = 500*1024*1024  # 500 MB
```

4. Create the `downloads` directory:
```bash
mkdir downloads
```

## Usage

1. Start the bot:
```bash
python main.py
```

2. In Telegram, start a chat with your bot and send `/start`

3. Use the keyboard menu to:
   - Check available storage space
   - Upload files by simply sending them to the bot
   - Download your stored files
   - Delete files you no longer need

## Bot Commands

- `/start` - Initialize the bot and create user storage
- Main menu options:
  - "Available storage" - Check remaining storage space
  - "Download Files" - Access stored files for download
  - "Delete Files" - Remove stored files

## Project Structure

```
telegram-storage-bot/
├── main.py           # Main bot logic
├── config.py         # Configuration settings
├── keyboards.py      # Keyboard layouts and callbacks
├── db.py            # Database management
└── downloads/        # File storage directory
    └── [user_id]/   # User-specific directories
        ├── documents/
        ├── photos/
        ├── videos/
        └── voice/
```

## Database Structure

The bot uses SQLite with two main tables:
- `users`: Stores user information and total storage usage
- `files`: Stores file metadata and locations

## Security Features

- Individual storage spaces for each user
- File deduplication
- Storage quota enforcement
- Secure file handling

## Limitations

- Maximum storage per user: 500MB (Can be updated as you wish)
- File size limits according to Telegram's restrictions
- Supported file types are limited to what Telegram allows

## Error Handling

- Storage space checks before file uploads
- Duplicate file detection
- Invalid file type protection
- Database connection error handling

## Contributing

Feel free to fork the project and submit pull requests for any improvements.
