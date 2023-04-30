from database import Session
from sql_models import User, Event, Registrations
import telebot, os
from datetime import datetime, timedelta


if __name__ == "__main__":
    TOKEN = os.environ.get("BOT_TOKEN")
    bot = telebot.TeleBot(TOKEN, parse_mode="MARKDOWN")
    session = Session()

    today = datetime.now().replace(hour=0, minute=0)

    tomorrow = today + timedelta(1) - timedelta(minutes=1)
    day_after_tomorrow = today + timedelta(2)

    events = session.query(Event).filter(
        Event.on_time >= tomorrow,
        Event.on_time < day_after_tomorrow
    ).all()

    for event in events:
        event: Event
        regs = session.query(Registrations).filter_by(event=event.id).all()
        for reg in regs:
            reg: Registrations
            user: User = session.query(User).get(reg.user)
            bot.send_message(
                chat_id=user.tg_id,
                text=f"Уведомляем Вас, что завтра состоится мероприятие \"{event.title}\""
            )