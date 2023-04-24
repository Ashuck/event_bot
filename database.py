from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
print(BASE_DIR)

def create_db():
    Base.metadata.create_all(engine)


DB_NAME = BASE_DIR / 'db.sqlite'

engine = create_engine(f'sqlite:///{DB_NAME}?check_same_thread=false', echo=False)
Session = sessionmaker(bind=engine)

Base = declarative_base()