import os
import telebot
from datetime import datetime, date, timedelta
from telebot import custom_filters
from telebot.types import Message, CallbackQuery
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


from sql_models import User, Event, Registrations, Admins
from database import DB_NAME, Session
from email_woking import send_mail


phone_board = ReplyKeyboardMarkup(True)
phone_board.add(
    KeyboardButton("Предоставить номер телефона", request_contact=True)
)

main_board = ReplyKeyboardMarkup(True)
main_board.add(
    KeyboardButton("Список мероприятий")
)
main_board.add(
    KeyboardButton("Заполнить анкету заново")
)

admin_board = ReplyKeyboardMarkup(True)
admin_board.add(
    KeyboardButton("Список мероприятий"),
    KeyboardButton("Добавить")
)
admin_board.add(
    KeyboardButton("Заполнить анкету заново")
)

email_template = """Заявка на регистрацию от пользователя {username} на мероприятие {event}
Ссылка на телеграм аккаунт {tg_account}
Пользователь представился как {comment}
Телефон {phone}
Email {email}"""


def reg_user(message: Message):
    user = User(
        chat_id=message.chat.id,
        last_name=message.from_user.last_name,
        first_name=message.from_user.first_name,
        username=message.chat.username,
    )
    session.add(user)
    session.commit()
    return user


def check_user(func):
    def wrap(message: Message | CallbackQuery):

        if isinstance(message, Message):
            user: User = session.query(User).get(message.chat.id)
        else:
            user: User = session.query(User).get(message.message.chat.id)
            
        if not user:
            if isinstance(message, Message):
                user = reg_user(message)
            else:
                user = reg_user(message.message)

        if user.phone and user.email and user.comment:
            func(message, user)

        else:
            need_info[user.tg_id] = "comment"
            bot.send_message(
                chat_id=user.tg_id,
                text="Для продолжения необходимо представиться",
            )
    return wrap


TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="MARKDOWN")
session = Session()
need_info = {}


def add_event_from_msg(text: str):
    data = text.split("\n")
    if len(data) == 3:
        if data[1].lower() == "период":
            dates = data[2].split(" - ")
            time_start = datetime.strptime(dates[0], "%H:%M %d.%m.%Y")
            time_end = datetime.strptime(dates[1], "%H:%M %d.%m.%Y")
        elif data[1].lower() == "ко времени":
            dates = data[2].split(" - ")
            time_start = datetime.strptime(dates[0], "%H:%M %d.%m.%Y")
            time_end = time_start
        elif data[1].lower() == "дата":
            dates = data[2].split(" - ")
            time_start = datetime.strptime(dates[0], "%d.%m.%Y")
            time_end = time_start
        else:
            return "Не распознан режим мероприятия"

        event = Event()
        event.title = data[0]
        event.on_time = time_start
        event.end_time = time_end
        event.mode = event.modes[data[1].lower()]
        session.add(event)
        session.commit()
        return f"Мероприятие {event.title} добавлено"
    
    else:
        return "Ошибка, сообщение не состоит из 3х частей: название, режим, время"


@bot.message_handler(func=lambda msg: isinstance(msg, Message) and msg.chat.id in need_info)
def add_info(message: Message):
    user: User = session.query(User).get(message.chat.id)

    args = {
        "chat_id": user.tg_id,
    }
    if need_info[user.tg_id] == "phone":
        if message.text:
            user.phone = message.text
        session.commit()
        args['text'] = "Я запомнил Ваш номер телефона. Теперь Вы можете выбрать мероприятие."
        args['reply_markup'] = main_board
        need_info.pop(user.tg_id)

    elif need_info[user.tg_id] == "email":
        user.email = message.text
        session.commit()
        args['text'] = "Я запомнил Ваш email. Теперь предоставьте Ваш номер телефона."
        args['reply_markup'] = phone_board
        need_info[user.tg_id] = "phone"
    
    elif need_info[user.tg_id] == "comment":
        user.comment = message.text
        session.commit()
        args['text'] = "Теперь предоставьте Ваш email."
        need_info[user.tg_id] = "email"
    
    elif need_info[user.tg_id] == "add_event":
        try:
            args["text"] = add_event_from_msg(message.text)
        except:
            args["text"] = "Ошибка в датах"
        need_info.pop(user.tg_id)
    
    bot.send_message(**args)



@bot.message_handler(commands=['start'])
def start_message(message: Message):
    user: User = session.query(User).get(message.chat.id)

    if not user:
        user = reg_user(message)

    need_info[user.tg_id] = "comment"
    text = "Данный бот предназначен для регистрации пользователей на мероприятиях. Далее Вам необходимо представиться и предоставить номер телефона и email для регистрации и обратной связи."
    text += "\n\nПредставтесь, пожалуйста"
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
    )


@bot.message_handler(text=["Список мероприятий"])
@check_user
def get_event_list(message: Message, user):
    user: User = session.query(User).get(message.chat.id)
    admin: Admins = session.query(Admins).get(user.tg_id)

    events = session.query(Event).filter(
        Event.on_time > datetime.now()
    ).order_by(Event.on_time).all()
    
    if events:
        for event in events:
            event: Event
            text = f"Мероприятие \"{event.title}\"\n"
            if event.mode == "period":
                text += f"Состоится {event.on_time.strftime('%d.%m.%Y')} в {event.on_time.strftime('%H:%M')} до {event.end_time.strftime('%H:%M')}"
            elif event.mode == "on_time":
                text += f"Состоится {event.on_time.strftime('%d.%m.%Y')} в {event.on_time.strftime('%H:%M')}"
            else:
                text += f"Состоится {event.on_time.strftime('%d.%m.%Y')}"
            
            kbr = InlineKeyboardMarkup()
            kbr.add(
                InlineKeyboardButton("Записаться", callback_data=f"event_{event.id}")
            )
            if admin:
                kbr.add(
                    InlineKeyboardButton("Удалить", callback_data=f"remove_{event.id}")
                )
            bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=kbr
            )
    else:
        bot.send_message(
            chat_id=message.chat.id,
            text="Нет мероприятий"
        )


@bot.callback_query_handler(lambda call: call.data.startswith("event_"))
@check_user
def choose_event(calback: CallbackQuery, user: User):
    event_id = int(calback.data.split("_")[1])
    event: Event = session.query(Event).get(event_id)
    reg: Registrations = session.query(Registrations).filter_by(
        user=user.tg_id,
        event=event.id
    ).one_or_none()
    if not reg:

        reg = Registrations()
        reg.user = user.tg_id
        reg.event = event.id
        session.add(reg)
        session.commit()
        bot.send_message(
            chat_id=user.tg_id,
            text="Ваша заявка принята, мы свяжемся с вами в ближайшее время."
        )
        email_body = email_template.format(
            username=user.name,
            tg_account=user.url,
            phone=user.phone,
            email=user.email,
            comment=user.comment,
            title=event.title,
            on_date=event.on_time.strftime("%d.%m.%Y"),
            on_time=event.on_time.strftime("%H:%M"),
            event=event.title
        )
        
        
        send_mail(email_body, f"Регистрация на мероприятие {event.title}")
    else:
        bot.send_message(
            chat_id=user.tg_id,
            text=f"Вы уже отправляли заявку на мероприятие \"{event.title}\""
        )


@bot.message_handler(text=["Заполнить анкету заново"])
def refresh_user(message: Message):
    user: User = session.query(User).get(message.chat.id)
    user.email = ""
    user.phone = ""
    user.comment = ""
    session.commit()
    check_user(None)(message)


@bot.message_handler(content_types=['contact'])
def get_contact(message: Message):
    user: User = session.query(User).get(message.chat.id)
    user.phone = message.contact.phone_number
    session.commit()
    add_info(message)
    need_info.pop(user.tg_id)
    bot.send_message(
        chat_id=user.tg_id,
        text="Я запомнил Ваш номер телефона. Теперь Вы можете выбрать мероприятие.",
        reply_markup = main_board
    )


@bot.message_handler(text=[os.environ.get("ADMIN_SECRET")])
def add_admin(message: Message):
    user: User = session.query(User).get(message.chat.id)
    
    if user:
        admin: Admins = session.query(Admins).get(user.tg_id)
        if not admin:
            admin = Admins()
            admin.level = 1
            admin.user = user.tg_id
            session.add(admin)
            session.commit()
            text = "Вы теперь администратор"
        
        else:
            text = "Вы уже администратор"

        bot.send_message(
            chat_id=user.tg_id,
            text=text,
            reply_markup = admin_board
        )


@bot.message_handler(text=["Добавить"])
def add_event(message: Message):
    user: User = session.query(User).get(message.chat.id)
    admin: Admins = session.query(Admins).get(user.tg_id)
    print(admin)
    if admin:
        need_info[user.tg_id] = "add_event"
        bot.send_message(
            chat_id=user.tg_id,
            text="Пришлите информацию о новом мероприятии",
        )


@bot.callback_query_handler(lambda call: call.data.startswith("remove_"))
@check_user
def remove_event(calback: CallbackQuery, user: User):
    user: User = session.query(User).get(calback.message.chat.id)
    if user:
        admin: Admins = session.query(Admins).get(user.tg_id)
        if admin:
            event_id = int(calback.data.split("_")[1])
            event: Event = session.query(Event).get(event_id)
            if event:
                reg = session.query(Registrations).filter_by(
                    event=event.id
                ).delete()
                session.delete(event)
                session.commit()
                text = "Мероприятие удалено"
            else:
                text = "Мероприятие не найдено"
                
            bot.send_message(
                chat_id=user.tg_id,
                text=text,
            )


bot.add_custom_filter(custom_filters.TextMatchFilter())
bot.infinity_polling()