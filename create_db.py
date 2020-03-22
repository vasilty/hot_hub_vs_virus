from config import DATABASE
from models import HelpRequest, Volunteer, VolunteerAction


def create_db():
    DATABASE.connect()
    DATABASE.create_tables([HelpRequest, Volunteer, VolunteerAction], safe=True)
    DATABASE.close()


if __name__ == '__main__':
    create_db()
