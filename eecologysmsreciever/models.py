from datetime import datetime
import uuid
from geoalchemy2 import Geometry
from pyramid.exceptions import Forbidden
from pytz import utc
from sqlalchemy import (
    Column,
    Unicode,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
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
    __tablename__ = 'raw_message'
    __table_args__ = {'schema': SMS_SCHEMA}
    id = Column(Integer, primary_key=True)
    # message_id -- the unique ID of the SMS
    message_id = Column(GUID(), unique=True)
    # from -- the number that sent the SMS
    sent_from = Column(Unicode)
    # message -- the SMS sent
    body = Column(Unicode)
    # sent_to -- the phone number registered on the SIM card otherwise
    # it's the value set on the app as device ID
    sent_to = Column(Unicode)
    # device_id -- the unique id set on the device to be used by the server to
    # identify which device is communicating with it.
    gateway_id = Column(Unicode)
    # sent_timestamp -- the timestamp the SMS was sent. In the UNIX timestamp
    # format
    sent_timestamp = Column(DateTime(timezone=True))
    message = relationship('Message', uselist=False, backref=backref('raw'))

    @classmethod
    def from_request(cls, request):
        server_secret = request.registry.settings['secret_key']
        client_secret = request.POST.get('secret')
        if client_secret != server_secret:
            raise Forbidden('Invalid secret')
        raw_message = RawMessage()
        raw_message.message_id = uuid.UUID(request.POST['message_id'])
        raw_message.sent_from = request.POST['from']
        raw_message.body = request.POST['message']
        raw_message.sent_to = request.POST['sent_to']
        raw_message.gateway_id = request.POST['device_id']
        raw_message.sent_timestamp = datetime.utcfromtimestamp(
            int(request.POST['sent_timestamp']) / 1000)
        raw_message.message = Message.from_raw(raw_message)
        return raw_message


class Message(Base):
    __tablename__ = 'message'
    __table_args__ = {'schema': SMS_SCHEMA}
    id = Column(Integer, ForeignKey(SMS_SCHEMA + '.raw_message.id'), primary_key=True)
    device_info_serial = Column(Integer)
    date_time = Column(DateTime(timezone=True))
    battery_voltage = Column(Float(precision=3))
    memory_usage = Column(Float(precision=1))
    debug_info = Column(Unicode())
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
        has_debug = len(cols) >= 1 and len(cols[0]) == 8
        if has_debug:
            message.debug_info = cols.pop(0) + u','
            message.debug_info += cols.pop(0) + u','
            message.debug_info += cols.pop(0) + u','
            message.debug_info += cols.pop(0) + u','
            message.debug_info += cols.pop(0)
        while len(cols):
            has_position = len(cols[0]) == 6
            if not has_position:
                break
            position = Position()
            position.device_info_serial = message.device_info_serial
            date = cols.pop(0)
            time = cols.pop(0)
            position.date_time = datetime(2000 + int(date[4:6]),
                                          int(date[2:4]),
                                          int(date[:2]),
                                          int(time[:2]),
                                          int(time[2:4]),
                                          tzinfo=utc)
            position.lon = float(cols.pop(0)) / 10000000
            position.lat = float(cols.pop(0)) / 10000000
            loc_tmpl = 'SRID=4326;POINT({lon} {lat})'
            position.location = loc_tmpl.format(lon=position.lon, lat=position.lat)
            message.positions.append(position)
        return message


class Position(Base):
    __tablename__ = 'position'
    __table_args__ = (UniqueConstraint('device_info_serial', 'date_time'),
                      {'schema': SMS_SCHEMA})
    id = Column(Integer, ForeignKey(SMS_SCHEMA + '.message.id'), primary_key=True)
    device_info_serial = Column(Integer)
    date_time = Column(DateTime(timezone=True), primary_key=True)
    lon = Column(Float())
    lat = Column(Float())
    location = Column(Geometry('POINT', srid=4326))


def dump_ddl():
    """
    Dumps create table postgresql SQL statements.

    See http://docs.sqlalchemy.org/en/rel_0_9/faq/metadata_schema.html#how-can-i-get-the-create-table-drop-table-output-as-a-string
    """
    from io import StringIO
    from sqlalchemy import create_engine
    out = StringIO()

    def dump(sql, *multiparams, **params):
        if type(sql) is unicode:
            pass
        else:
            sql = sql.compile(dialect=engine.dialect)
        out.write(unicode(sql))

    engine = create_engine('postgresql://', strategy='mock', executor=dump)
    Base.metadata.create_all(engine, checkfirst=False)
    ddl = out.getvalue()
    out.close()
    return ddl
