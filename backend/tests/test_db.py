from sqlalchemy import text

from db.database import engine


with engine.connect() as connection:
    result = connection.execute(text("SELECT version()"))

    print("Database connected successfully!")
    print(result.scalar())
