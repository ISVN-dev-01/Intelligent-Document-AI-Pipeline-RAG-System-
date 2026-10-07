from sqlalchemy import URL, create_engine, event, text
from sqlalchemy.orm import sessionmaker

from database.models import Base
from utils.errors import StorageError
from utils.logging_config import event as log_event


def create_database(settings):
    """Create an engine and short-lived sessions. The MySQL database must already exist."""
    if settings.db_backend == "sqlite":
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        engine = create_engine(URL.create("sqlite", database=str(settings.data_dir / "metadata.db")),
                               connect_args={"check_same_thread": False, "timeout": 30})

        @event.listens_for(engine, "connect")
        def sqlite_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    else:
        url = URL.create("mysql+mysqlconnector", username=settings.mysql_user,
                         password=settings.mysql_password.get_secret_value(),
                         host=settings.mysql_host, port=settings.mysql_port,
                         database=settings.mysql_database, query={"charset": "utf8mb4"})
        engine = create_engine(url, pool_pre_ping=True, pool_recycle=1800,
                               connect_args={"connection_timeout": 10})
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        if settings.auto_create_tables:
            Base.metadata.create_all(engine)
    except Exception as exc:
        engine.dispose()
        log_event("database_failure", error_type=type(exc).__name__)
        raise StorageError("Cannot connect to the database. Check MySQL service, database name and credentials.") from None
    return engine, sessionmaker(engine, expire_on_commit=False)
