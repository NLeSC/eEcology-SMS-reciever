import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.md')) as f:
    CHANGES = f.read()

requires = [
    'pyramid',
    'pyramid_debugtoolbar',
    'SQLAlchemy==0.9.8',
    'GeoAlchemy2',
    'psycopg2',
    'waitress',
    'paste',
    'nose',
    'mock',
    'coverage',
    'pytz',
    ]

exec(open('eecologysmsreciever/version.py').read())

setup(name='eEcology-SMS-reciever',
      version='0.0',
      description='eEcology-SMS-reciever',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Stefan Verhoeven',
      author_email='s.verhoeven@esciencecenter.nl',
      url='https://github.com/NLeSC/eEcology-SMS-reciever',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='eecologysmsreciever',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = eecologysmsreciever:main
      """,
      )
