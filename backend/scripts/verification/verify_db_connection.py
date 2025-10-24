
import sqlalchemy
from app.core.config import get_settings

def main():
    settings = get_settings()
    try:
        engine = sqlalchemy.create_engine(settings.database_url)
        with engine.connect() as connection:
            print("Successfully connected to the database.")
            inspector = sqlalchemy.inspect(engine)
            tables = inspector.get_table_names()
            print("Tables in the database:", tables)
    except Exception as e:
        print(f"Failed to connect to the database: {e}")

if __name__ == "__main__":
    main()
