from pyramid.exceptions import Forbidden
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
SMS_SCHEMA = 'sms'


class RawMessage(Base):
    __tablename__ = 'raw_messages'
    __table_args__ = {'schema': SMS_SCHEMA}
    # message_id -- the unique ID of the SMS
    id = Column(Text, primary_key=True)
    # from -- the number that sent the SMS
    sender = Column(Text)
    # message -- the SMS sent
    message = Column(Text)
    # sent_to -- the phone number registered on the SIM card otherwise
    # it's the value set on the app as device ID
    sent_to = Column(Text)
    # device_id -- the unique id set on the device to be used by the server to
    # identify which device is communicating with it.
    device_id = Column(Text)
    # sent_timestamp -- the timestamp the SMS was sent. In the UNIX timestamp
    # format
    sent_timestamp = Column(Text)

    @classmethod
    def fromRequest(cls, request):
        server_secret = request.registry.settings['secret_key']
        client_secret = request.POST.get('secret')
        if client_secret != server_secret:
            raise Forbidden('Invalid secret')
        message = RawMessage()
        message.id = request.POST['message_id']
        message.sender = request.POST['from']
        message.message = request.POST['message']
        message.sent_to = request.POST['sent_to']
        message.device_id = request.POST['device_id']
        message.sent_timestamp = request.POST['sent_timestamp']
        return message
