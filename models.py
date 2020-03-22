import peewee
from playhouse.postgres_ext import DateTimeTZField

from config import DATABASE, SOURCES


class BaseModel(peewee.Model):
    class Meta:
        database = DATABASE


class BaseChoices:
    @classmethod
    def choices(cls):
        choices = []
        for name in dir(cls):
            value = getattr(cls, name)
            choices.append((value, value))
        return choices

    @classmethod
    def values(cls):
        return [getattr(cls, name) for name in dir(cls)]


class VolunteerStatuses(BaseChoices):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class Volunteer(BaseModel):
    id = peewee.AutoField()
    source = peewee.CharField(choices=[(x, x) for x in SOURCES.keys()])
    id_at_source = peewee.CharField()
    postal_code = peewee.CharField()
    status = peewee.CharField(choices=VolunteerStatuses.choices())

    class Meta:
        indexes = (
            (('id_at_source', 'source'), True),  # unique together index
        )


class HelpRequestStatuses(BaseChoices):
    OPEN = 'open'
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    FULFILLED = 'fulfilled'


class HelpRequest(BaseModel):
    id = peewee.AutoField()
    created_at = DateTimeTZField()
    phone_number = peewee.CharField()
    postal_code = peewee.CharField()
    volunteer = peewee.ForeignKeyField(Volunteer, null=True, backref='help_requests')
    status = peewee.CharField(choices=HelpRequestStatuses.choices())
    status_changed_at = DateTimeTZField()

    def find_volunteer(self):
        declined = (VolunteerAction
                    .select(VolunteerAction.volunteer_id)
                    .where(
                        VolunteerAction.help_request == self,
                        VolunteerAction.action == VolunteerActionTypes.DECLINE)
                    )
        volunteer = (Volunteer
                     .select()
                     .where(
                        Volunteer.status == VolunteerStatuses.ACTIVE,
                        Volunteer.postal_code == self.postal_code,
                        Volunteer.id.not_in(declined))
                     .order_by(peewee.fn.Random())
                     .first()
                     )
        return volunteer


class VolunteerActionTypes(BaseChoices):
    ACCEPT = 'accept'
    DECLINE = 'decline'
    FULFILL = 'fulfill'


class VolunteerAction(BaseModel):
    id = peewee.AutoField()
    help_request = peewee.ForeignKeyField(HelpRequest)
    volunteer = peewee.ForeignKeyField(Volunteer, backref='actions')
    action = peewee.CharField(choices=VolunteerActionTypes.choices())
    happened_at = DateTimeTZField()
