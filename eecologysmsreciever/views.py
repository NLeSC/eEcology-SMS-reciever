import logging
from pyramid.view import view_config
from pyramid.exceptions import Forbidden
from sqlalchemy.exc import DBAPIError
from .version import __version__

from .models import (
    DBSession,
    RawMessage,
    )

LOGGER = logging.getLogger('eecologysmsreciever')


@view_config(route_name='messages', request_method='POST', renderer='json')
def recieve_message(request):
    try:
        message = RawMessage.from_request(request)
        DBSession.add(message)
        DBSession.commit()
    except DBAPIError as e:
        LOGGER.warn(e)
        return {'payload': {'success': False, 'error': 'Database error'}}
    except Forbidden as e:
        LOGGER.debug(e)
        return {'payload': {'success': False, 'error': 'Forbidden'}}
    return {'payload': {'success': True, 'error': None}}

@view_config(route_name='status', request_method='GET', renderer='json')
def status(request):
    DBSession.query('SELECT 1')
    return {'version': __version__}
