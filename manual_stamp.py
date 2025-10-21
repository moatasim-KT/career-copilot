import sqlalchemy
import os

# Define the database path relative to the script
DB_PATH = "backend/data/career_copilot.db"
DB_URL = f"sqlite:///{DB_PATH}"

# Ensure the directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Create a synchronous engine
engine = sqlalchemy.create_engine(DB_URL)

# Define the alembic_version table
meta = sqlalchemy.MetaData()
alembic_version_table = sqlalchemy.Table(
    'alembic_version',
    meta,
    sqlalchemy.Column('version_num', sqlalchemy.String(32), nullable=False, primary_key=True)
)

# The revision ID of the script I created
REVISION_ID = '79392a85c8a2'

with engine.connect() as connection:
    # Begin a single transaction for all operations
    trans = connection.begin()
    try:
        # Create the table
        meta.create_all(connection)
        # Clear any existing data and insert the new revision ID
        connection.execute(alembic_version_table.delete())
        connection.execute(alembic_version_table.insert().values(version_num=REVISION_ID))
        # Commit the transaction
        trans.commit()
        print(f"Successfully created database at {DB_PATH} and stamped with revision {REVISION_ID}")
    except Exception as e:
        # Rollback in case of error
        trans.rollback()
        print(f"An error occurred: {e}")
        raise