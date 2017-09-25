import logging
from pyramid.view import view_config
from pyramid.exceptions import Forbidden
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError
from .version import __version__

from .models import DBSession, RawMessage, Message

LOGGER = logging.getLogger('eecologysmsreciever')


@view_config(route_name='messages', request_method='POST', renderer='json')
def recieve_message(request):
    # Make sure db is set to UTC,
    # db.e-ecology.sara.nl has 'Europe/Amsterdam' as timezone causing date_time to be stored in that timezone
    try:
        DBSession.execute("SET TIME ZONE 'UTC'")
        raw_message = RawMessage.from_request(request)
        DBSession.add(raw_message)
        DBSession.commit()
    except IntegrityError as e:
        # when raw message already exists then return OK, so app will treat message as being transferred
        DBSession.rollback()
        LOGGER.warn(e)
        return {'payload': {'success': True, 'error': None}}
    except DBAPIError as e:
        DBSession.rollback()
        LOGGER.warn(e)
        return {'payload': {'success': False, 'error': 'Database error'}}
    except Forbidden as e:
        LOGGER.debug(e)
        return {'payload': {'success': False, 'error': 'Forbidden'}}
    except KeyError as e:
        LOGGER.debug(e)
        return {'payload': {'success': False, 'error': 'Invalid message'}}
    try:
        message = Message.from_raw(raw_message)
        DBSession.add(message)
        DBSession.commit()

        positions = []
        try:
            positions = message.positions
        except ProgrammingError as e:
            # when no positions where in message
            # then SQLalchemy tries to perform a SELECT
            # which the service is not allowed to do
            # so ignore any errors
            DBSession.rollback()
            LOGGER.warn(e)

        for position in positions:
            try:
                with DBSession.begin_nested():
                    DBSession.add(position)
            except IntegrityError as e:
                LOGGER.warn('Position already stored, skipping it')
                LOGGER.warn(e)
        DBSession.commit()

    except IndexError as e:
        LOGGER.debug(e)
        return {'payload': {'success': False, 'error': 'Invalid message'}}
    except ValueError as e:
        LOGGER.debug(e)
        return {'payload': {'success': False, 'error': 'Invalid message'}}
    return {'payload': {'success': True, 'error': None}}


@view_config(route_name='status', request_method='GET', renderer='json')
def status(request):
    try:
        DBSession.execute('SELECT TRUE').scalar()
    except DBAPIError as e:
        DBSession.rollback()
        LOGGER.warn(e)
        raise e
    return {'version': __version__}
