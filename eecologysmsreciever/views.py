import logging
from pyramid.view import view_config
from pyramid.exceptions import Forbidden
from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    RawMessage,
    )

LOGGER = logging.getLogger('eecologysmsreciever')


@view_config(route_name='messages', request_method='POST', renderer='json')
def recieve_message(request):
    try:
        message = RawMessage.fromRequest(request)
        DBSession.add(message)
        DBSession.commit()
    except DBAPIError as e:
        LOGGER.warn(e)
        return {'payload': {'success': False, 'error': 'Database error'}}
    except Forbidden as e:
        LOGGER.debug(e)
        return {'payload': {'success': False, 'error': 'Forbidden'}}
    return {'payload': {'success': True, 'error': None}}
