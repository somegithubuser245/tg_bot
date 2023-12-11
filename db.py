import aiosqlite


def generate_readable_filename(file_type, count, file_extension):
    # Create a unique and readable file name
    filename = f"{file_type}_{count}{file_extension}"
    return filename


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    async def create_tables(self):
        CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_hash TEXT UNIQUE,
            file_name TEXT,
            file_type TEXT,
            file_size INTEGER,
            file_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(CREATE_TABLE_SQL)
            await db.commit()

    async def check_file_exists(self, file_hash):
        CHECK_FILE_EXISTS_SQL = """
        SELECT EXISTS(SELECT 1 FROM files WHERE file_hash = ?)
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(CHECK_FILE_EXISTS_SQL, (file_hash,)) as cursor:
                return (await cursor.fetchone())[0]

    async def get_next_file_counter(self, user_id, file_type):
        # Retrieve the highest file count for the user and file type, then increment by 1
        GET_COUNTER_SQL = """
        SELECT MAX(file_count) FROM files WHERE user_id = ? AND file_type = ?
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(GET_COUNTER_SQL, (user_id, file_type)) as cursor:
                result = await cursor.fetchone()
                next_count = (result[0] + 1) if result[0] is not None else 1
                return next_count

    async def add_file(self, user_id, file_hash, file_type, file_extension, file_size):
        next_count = await self.get_next_file_counter(user_id, file_type)
        file_name = generate_readable_filename(file_type, next_count, file_extension)

        # Add file details to the database
        ADD_FILE_SQL = """
        INSERT INTO files (user_id, file_hash, file_name, file_type, file_size, file_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(ADD_FILE_SQL, (user_id, file_hash, file_name, file_type, file_size, next_count))
            await db.commit()
        return file_name

    async def check_user_exists(self, user_id):
        CHECK_USER_EXISTS_SQL = "SELECT EXISTS(SELECT 1 FROM users WHERE user_id = ?)"
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(CHECK_USER_EXISTS_SQL, (user_id,)) as cursor:
                return (await cursor.fetchone())[0]

    async def add_user(self, user_id):
        ADD_USER_SQL = "INSERT INTO users (user_id) VALUES (?)"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(ADD_USER_SQL, (user_id,))
            await db.commit()

# Usage example:
# db_manager = DatabaseManager("telegram_bot.db")
# await db_manager.create_tables()
# user_exists = await db_manager.check_user_exists(12345)
# if not user_exists:
#     await db_manager.add_user(12345)
# await db_manager.add_file(12345, "example.txt", "text", 1024)
