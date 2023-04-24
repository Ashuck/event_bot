import os
import telebot
from datetime import datetime, date, timedelta
from telebot import custom_filters
from telebot.types import Message, CallbackQuery
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


from sql_models import User, Event, Registrations
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

email_template = """Заявка от пользователя {username} на мероприятие {event} {on_date} в {on_time}
Ссылка на телеграм аккаунт {tg_account}
Телефон {phone}
Комментарий {comment}"""


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
            user = reg_user(message)

        if user.phone and user.comment:
            func(message, user)

        elif user.phone:
            need_comment.add(user.tg_id)
            bot.send_message(
                chat_id=user.tg_id,
                text="Укажите Ваш email и как к Вам обращаться (в одном сообщении)",
            )
        else:
            bot.send_message(
                chat_id=user.tg_id,
                text="Для продолжения необходимо предоставить номер телефона",
                reply_markup=phone_board
            )
    return wrap


TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="MARKDOWN")
session = Session()
need_comment = set()


@bot.message_handler(func=lambda msg: isinstance(msg, Message) and msg.chat.id in need_comment)
def add_comment(message: Message):
    user: User = session.query(User).get(message.chat.id)
    user.comment = message.text
    session.commit()
    bot.send_message(
        chat_id=user.tg_id,
        text="Информация обновлена",
        reply_markup=main_board
    )
    need_comment.remove(user.tg_id)


@bot.message_handler(commands=['start'])
def start_message(message: Message):
    user: User = session.query(User).get(message.chat.id)
    if not user:
        user = reg_user(message)

    bot.send_message(
        chat_id=message.chat.id,
        text="Данный бот предназначен для регистрации пользователей на мероприятиях. Далее Вам необходимо предоставить свой номер телефона и email для регистрации и обратной связи.",
        reply_markup=phone_board
    )


@bot.message_handler(text=["Список мероприятий"])
@check_user
def get_event_list(message: Message, user):

    events = session.query(Event).filter(
        Event.on_time > datetime.now()
    ).all()
    
    if events:
        for event in events:
            print(event)
            event: Event
            text = f"Мероприятие \"{event.title}\"\n"
            text += f"Состоится {event.on_time.strftime('%d.%m.%Y')} в {event.on_time.strftime('%H:%M')} до {event.end_time.strftime('%H:%M')}"
            kbr = InlineKeyboardMarkup()
            kbr.add(
                InlineKeyboardButton("Записаться", callback_data=f"event_{event.id}")
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
            text="Вы уже отправляли заявку на это мероприятие"
        )


@bot.message_handler(text=["Заполнить анкету заново"])
def refresh_user(message: Message):
    user: User = session.query(User).get(message.chat.id)
    user.phone = ""
    user.comment = ""
    session.commit()
    check_user(message)


@bot.message_handler(content_types=['contact'])
def get_contact(message: Message):
    user: User = session.query(User).get(message.chat.id)
    user.phone = message.contact.phone_number
    session.commit()
    need_comment.add(user.tg_id)
    bot.send_message(
        chat_id=user.tg_id,
        text="Теперь укажите Ваш email и как к Вам обращаться (в одном сообщении)",
    )




bot.add_custom_filter(custom_filters.TextMatchFilter())
bot.infinity_polling()