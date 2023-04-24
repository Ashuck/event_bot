from database import create_db, Session

from sql_models import User, Event, Registrations


def create_database():
    create_db()


if __name__ == "__main__":
    create_database()