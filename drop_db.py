from config import DATABASE
from models import HelpRequest, Volunteer, VolunteerAction


def drop_db():
    DATABASE.connect()
    VolunteerAction.drop_table()
    HelpRequest.drop_table()
    Volunteer.drop_table()
    DATABASE.close()


if __name__ == '__main__':
    drop_db()
