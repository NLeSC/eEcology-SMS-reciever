import logging
from datetime import datetime
from datetime import timedelta

from pyramid.view import view_config
from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPServerError
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError, SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from .version import __version__

from .models import DBSession, RawMessage, Message, Position

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
    except SQLAlchemyError as e:
        # Catches:
        # StatementError: Can't reconnect until invalid transaction is rolled back
        # (original cause: InvalidRequestError: Can't reconnect until invalid transaction is rolled back)
        DBSession.rollback()
        LOGGER.warn(e)
        return {'payload': {'success': False, 'error': 'Database ORM error'}}
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
                    DBSession.merge(position)
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
    except IntegrityError as e:
        DBSession.rollback()
        LOGGER.warn(e)
        return {'payload': {'success': False, 'error': 'Database error'}}
    except DBAPIError as e:
        DBSession.rollback()
        LOGGER.warn(e)
        return {'payload': {'success': False, 'error': 'Database error'}}
    except SQLAlchemyError as e:
        # Catches:
        # StatementError: Can't reconnect until invalid transaction is rolled back
        # (original cause: InvalidRequestError: Can't reconnect until invalid transaction is rolled back)
        DBSession.rollback()
        LOGGER.warn(e)
        return {'payload': {'success': False, 'error': 'Database ORM error'}}
    return {'payload': {'success': True, 'error': None}}


def utcnow():
    """Now

    :return: (datetime.datetime)
    """
    return datetime.utcnow()


@view_config(route_name='status', request_method='GET', renderer='json')
def status(request):
    try:
        DBSession.execute("SET TIME ZONE 'UTC'")
        alert_too_old = request.registry.settings['alert_too_old']
        latest_dt = utcnow() - timedelta(hours=alert_too_old)
        last_position = DBSession.query(Position.date_time).filter(Position.date_time >= latest_dt).limit(1).scalar()
        DBSession.commit()
        if last_position is None:
            raise HTTPServerError('Positions have not been received recently')
        return {'version': __version__}
    except DBAPIError as e:
        DBSession.rollback()
        LOGGER.warn(e)
        raise e
    except NoResultFound:
        raise HTTPServerError('Positions have not been received recently')
