from sqlalchemy import Column, Integer, String, DATETIME, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from database import Base



class User(Base):
    __tablename__ = "users"

    tg_id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    comment = Column(String)
    email = Column(String, server_default="")
    phone = Column(String)


    def __init__(self, chat_id, last_name, first_name, username, phone="", comment=""):
        self.tg_id = chat_id

        if last_name:
            self.name = first_name + " " + last_name
        else:
            self.name = first_name

        self.name = self.name.strip()

        if username:
            self.url = f"https://t.me/{username}"
        else:
            self.url = "У пользователя не указан никнейм"

        self.phone = phone
        self.comment = comment
    
    def __repr__(self) -> str:
        return f"User: {self.name} {self.url}"


class Admins(Base):
    __tablename__ = "admins"

    user = Column(Integer, ForeignKey("users.tg_id"), primary_key=True,)
    level = Column(Integer, autoincrement=True)

    def __repr__(self) -> str:
        return f"User: {self.user}"


class Event(Base):
    __tablename__ = "events"
    modes = {
        "период": "period",
        "ко времени": "on_time",
        "дата": "on_date"
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    mode = Column(String)
    on_time = Column(DateTime)
    end_time = Column(DateTime)


    def __repr__(self) -> str:
        return f"Event: {self.title} {self.on_time}"


class Registrations(Base):
    __tablename__ = 'registrations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Integer, ForeignKey("users.tg_id"))
    event = Column(Integer, ForeignKey("events.id"))

    def __repr__(self) -> str:
        return f"Reg {self.id}: {self.user} on {self.event}"
