import os
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    old_url = settings.get('sqlalchemy.url')
    settings['sqlalchemy.url'] = os.environ.get('DB_URL', old_url)
    old_secret = settings.get('secret_key')
    settings['secret_key'] = os.environ.get('SECRET_KEY', old_secret)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.add_route('messages', '/messages')
    config.add_route('status', '/status')
    config.scan()
    return config.make_wsgi_app()
