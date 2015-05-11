import logging
from pyramid.view import view_config
from pyramid.exceptions import Forbidden
from sqlalchemy.exc import DBAPIError
from .version import __version__

from .models import (
    DBSession,
    Message,
    Position,
    RawMessage,
    )

LOGGER = logging.getLogger('eecologysmsreciever')


@view_config(route_name='messages', request_method='POST', renderer='json')
def recieve_message(request):
    try:
        raw_message = RawMessage.from_request(request)
        DBSession.add(raw_message)
        DBSession.commit()
        DBSession.begin()
        message = Message.from_raw(raw_message)
        DBSession.add(message)
        DBSession.commit()
        try:
            for position in Position.from_message(message):
                DBSession.begin()
                DBSession.add(position)
                DBSession.commit()
        except DBAPIError as e:
          # same positions (tracker/timestamp combi) 
          # can be given in multiple messages
          # so leave the already stored position alone
          # and skip the new one
          LOGGER.warn(e)
    except DBAPIError as e:
        DBSession.rollback()
        LOGGER.warn(e)
        return {'payload': {'success': False, 'error': 'Database error'}}
    except Forbidden as e:
        LOGGER.debug(e)
        return {'payload': {'success': False, 'error': 'Forbidden'}}
    return {'payload': {'success': True, 'error': None}}


@view_config(route_name='status', request_method='GET', renderer='json')
def status(request):
    DBSession.execute('SELECT TRUE').scalar()
    return {'version': __version__}
