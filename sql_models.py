from sqlalchemy import Column, Integer, String, DATETIME, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from database import Base



class User(Base):
    __tablename__ = "users"

    tg_id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    comment = Column(String)
    phone = Column(String)


    def __init__(self, chat_id, last_name, first_name, username, phone="", comment=""):
        self.tg_id = chat_id
        self.name = first_name + " " + last_name
        self.name = self.name.strip()
        self.url = f"https://t.me/{username}"
        self.phone = phone
        self.comment = comment
    
    def __repr__(self) -> str:
        return f"User: {self.name} {self.url}"
    

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
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
        return f"Reg: {self.user} on {self.event.title}"
