import datetime
import uuid
from pyramid.exceptions import Forbidden
from sqlalchemy import (
    Column,
    Unicode,
    Integer,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref,
)
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID


DBSession = scoped_session(sessionmaker())
Base = declarative_base()
SMS_SCHEMA = 'sms'


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value)
            else:
                # hexstring
                return "%.32x" % value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class RawMessage(Base):
    __tablename__ = 'raw_messages'
    __table_args__ = {'schema': SMS_SCHEMA}
    # message_id -- the unique ID of the SMS
    message_id = Column(GUID(), primary_key=True)
    # from -- the number that sent the SMS
    sender = Column(Unicode)
    # message -- the SMS sent
    body = Column(Unicode)
    # sent_to -- the phone number registered on the SIM card otherwise
    # it's the value set on the app as device ID
    sent_to = Column(Unicode)
    # device_id -- the unique id set on the device to be used by the server to
    # identify which device is communicating with it.
    device_id = Column(Unicode)
    # sent_timestamp -- the timestamp the SMS was sent. In the UNIX timestamp
    # format
    sent_timestamp = Column(DateTime(timezone=True))

    @classmethod
    def from_request(cls, request):
        server_secret = request.registry.settings['secret_key']
        client_secret = request.POST.get('secret')
        if client_secret != server_secret:
            raise Forbidden('Invalid secret')
        raw_message = RawMessage()
        raw_message.message_id = uuid.UUID(request.POST['message_id'])
        raw_message.sender = request.POST['from']
        raw_message.body = request.POST['message']
        raw_message.sent_to = request.POST['sent_to']
        raw_message.device_id = request.POST['device_id']
        raw_message.sent_timestamp = datetime.datetime.utcfromtimestamp(int(request.POST['sent_timestamp'])/1000)
        raw_message.message = Message.from_raw(raw_message)
        return raw_message

class Message(Base):
    __tablename__ = 'messages'
    __table_args__ = {'schema': SMS_SCHEMA}
    # message_id -- the unique ID of the SMS
    message_id = Column(GUID(), ForeignKey(SMS_SCHEMA+'.raw_messages.message_id'), primary_key=True)
    device_info_serial = Column(Integer)
    date_time = Column(DateTime(timezone=True))
    battery_voltage = Column(Float(precision=3))
    memory_usage = Column(Float(precision=1))
    debug_info = Column(Integer())
    raw = relationship('RawMessage', backref=backref('parsed'))
    positions = relationship('Position', backref=backref('message'))

    @classmethod
    def from_raw(cls, raw_message):
        body = raw_message.body
        message = cls.from_body(body)
        message.date_time = raw_message.sent_timestamp
        return message

    @classmethod
    def from_body(cls, body):
        cols = body.split(',')
        message = Message()
        message.device_info_serial = int(cols.pop(0).lstrip('ID'))
        message.battery_voltage = float(cols.pop(0)) / 1000
        message.memory_usage = float(cols.pop(0)) / 10
        has_debug = len(cols[0]) == 8
        if has_debug:
            message.debug_info = cols.pop(0) + ',' + cols.pop(0) + ',' + cols.pop(0)
        return message

class Position(Base):
    __tablename__ = 'positions'
    __table_args__ = {'schema': SMS_SCHEMA}
    message_id = Column(GUID(), ForeignKey(SMS_SCHEMA+'.messages.message_id'), primary_key=True)
    device_info_serial = Column(Integer)
    date_time = Column(DateTime(timezone=True), primary_key=True)
    lon = Column(Float())
    lat = Column(Float())
