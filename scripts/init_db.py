from _common import cli_error

from config.settings import Settings
from database.connection import create_database

if __name__ == "__main__":
    try:
        settings = Settings(auto_create_tables=True)
        engine, _ = create_database(settings)
        engine.dispose()
        print(f"Tables initialized using {settings.db_backend}.")
    except Exception as exc:
        cli_error(exc)
