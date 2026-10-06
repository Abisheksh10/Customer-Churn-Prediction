from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = (
    "mysql+pymysql://root:root@localhost:3306/telecom"
)


engine = create_engine(
    DATABASE_URL
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()