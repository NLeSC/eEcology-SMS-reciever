from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    RawMessage,
    )


@view_config(route_name='messages', method='POST', renderer='JSON')
def recieve_message(request):
    try:
        message = RawMessage.fromRequest(request)
        DBSession.add(message)
    except DBAPIError:
        return {'payload': {'success': True, 'error': 'Database error'}}
    return {'payload': {'success': True, 'error': None}}
