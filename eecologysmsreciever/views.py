import logging
from pyramid.view import view_config
from pyramid.exceptions import Forbidden
from sqlalchemy.exc import DBAPIError, IntegrityError
from .version import __version__

from .models import DBSession, RawMessage, Message

LOGGER = logging.getLogger('eecologysmsreciever')


@view_config(route_name='messages', request_method='POST', renderer='json')
def recieve_message(request):
    try:
        raw_message = RawMessage.from_request(request)
        DBSession.add(raw_message)
        DBSession.commit()
        message = Message.from_raw(raw_message)
        DBSession.add(message)
        DBSession.commit()
        positions = message.positions
        for position in positions:
            try:
                with DBSession.begin_nested():
                    DBSession.add(position)
            except IntegrityError as e:
                LOGGER.warn('Position already stored, skipping it')
                LOGGER.warn(e)
        DBSession.commit()
    except DBAPIError as e:
        DBSession.rollback()
        LOGGER.warn(e)
        return {'payload': {'success': False, 'error': 'Database error'}}
    except Forbidden as e:
        LOGGER.debug(e)
        return {'payload': {'success': False, 'error': 'Forbidden'}}
    except IndexError as e:
        LOGGER.debug(e)
        return {'payload': {'success': False, 'error': 'Invalid message'}}
    except ValueError as e:
        LOGGER.debug(e)
        return {'payload': {'success': False, 'error': 'Invalid message'}}
    return {'payload': {'success': True, 'error': None}}


@view_config(route_name='status', request_method='GET', renderer='json')
def status(request):
    DBSession.execute('SELECT TRUE').scalar()
    return {'version': __version__}
