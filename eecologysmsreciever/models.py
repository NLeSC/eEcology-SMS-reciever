from sqlalchemy import (
    Column,
    Text,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

DBSession = scoped_session(sessionmaker())
Base = declarative_base()


class RawMessage(Base):
    __tablename__ = 'raw_messages'
    # message_id -- the unique ID of the SMS
    id = Column(Text, primary_key=True)
    # from -- the number that sent the SMS
    sender = Column(Text)
    # message -- the SMS sent
    message = Column(Text)
    # sent_to -- the phone number registered on the SIM card otherwise
    # it's the value set on the app as device ID
    send_to = Column(Text)
    # device_id -- the unique id set on the device to be used by the server to
    # identify which device is communicating with it.
    device_id = Column(Text)
    # sent_timestamp -- the timestamp the SMS was sent. In the UNIX timestamp
    # format
    sent_timestamp = Column(Text)

    @classmethod
    def fromRequest(request):
        # TODO validate request by checking secret
        message = RawMessage()
        # TODO fill it
        return message
