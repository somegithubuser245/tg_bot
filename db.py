import aiosqlite
import config

#file_hash is actually the path of the file
#telegram already checks if the file is unique

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    async def create_tables(self):
        CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            total_file_size INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_hash TEXT UNIQUE,
            file_name TEXT,
            file_type TEXT,
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

    async def add_file(self, user_id, file_hash, file_name, file_type, file_size):
        #check if there's enough space
        storage_condition = await self.update_total_file_size(user_id, file_size)

        if storage_condition != 'Not enough storage space':
            # Add file details to the database
            ADD_FILE_SQL = """
            INSERT INTO files (user_id, file_hash, file_name, file_type)
            VALUES (?, ?, ?, ?)
            """
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(ADD_FILE_SQL, (user_id, file_hash, file_name, file_type))
                await db.commit()

        return storage_condition


    async def update_total_file_size(self, user_id, file_size, increase=True):
        # Get the current total size
        GET_SIZE_SQL = "SELECT total_file_size FROM users WHERE user_id = ?"
        UPDATE_SIZE_SQL = "UPDATE users SET total_file_size = ? WHERE user_id = ?"

        async with aiosqlite.connect(self.db_path) as db:
            current_size = 0
            async with db.execute(GET_SIZE_SQL, (user_id,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    current_size = result[0]

            # Update the total size
            new_size = current_size + file_size if increase else current_size - file_size
            if new_size < config.MAX_STORAGE_PER_USER:
                await db.execute(UPDATE_SIZE_SQL, (new_size, user_id))
                await db.commit()
                return f'Available storage: {round((config.MAX_STORAGE_PER_USER - new_size) / (1024 * 1024), 1)} / {round(config.MAX_STORAGE_PER_USER / (1024 * 1024), 1)} MB'
            else:
                return 'Not enough storage space'

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