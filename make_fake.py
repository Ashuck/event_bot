from database import Session
from sql_models import User, Event, Registrations
from datetime import datetime


event = Event()
event.title = "Мероприятие №1"
event.on_time = datetime(2023, 5, 27)
session = Session()
session.add(event)
session.commit()
second_event = Event()
second_event.title = "Мероприятие №2"
second_event.on_time = datetime(2023, 5, 27, 12, 15)
session = Session()
session.add(second_event)
session.commit()