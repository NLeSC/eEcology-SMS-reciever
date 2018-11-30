import datetime
import os
from nose.plugins.attrib import attr
from nose.tools import eq_
from nose.tools import assert_raises
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from webtest import TestApp, AppError

from eecologysmsreciever import main, DBSession


@attr('functional')
class TestFunctional(object):
    db_root_url = ''

    def setupDb(self):
        self.db_root_url = os.environ['DB_URL']
        connection = create_engine(self.db_root_url).raw_connection()
        cursor = connection.cursor()

        # Create sms db schema
        cursor.execute(open('sms.sql').read())
        connection.commit()

        # Create sms user
        cursor.execute('''
        CREATE USER smswriter WITH LOGIN PASSWORD 'smspw';
        GRANT USAGE ON SCHEMA sms TO smswriter;
        GRANT INSERT ON sms.raw_message TO smswriter;
        GRANT SELECT (id) ON sms.raw_message TO smswriter;
        GRANT SELECT (date_time) ON sms.position TO smswriter;
        GRANT INSERT ON sms.message TO smswriter;
        GRANT INSERT ON sms.position TO smswriter;
        GRANT USAGE on SEQUENCE sms.raw_message_id_seq TO smswriter;
        ''')
        connection.commit()

        connection.close()

    def teardownDb(self):
        connection = create_engine(self.db_root_url).raw_connection()
        cursor = connection.cursor()
        cursor.execute('DROP SCHEMA IF EXISTS sms CASCADE')
        cursor.execute('DROP ROLE IF EXISTS smswriter')
        connection.commit()

        connection.close()

    def setUp(self):
        self.setupDb()
        db_user_url = make_url(self.db_root_url)
        db_user_url.username = 'smswriter'
        db_user_url.password = 'smspw'

        self.settings = {
            'sqlalchemy.url': str(db_user_url),
            'sqlalchemy.echo': True,
            'secret_key': 'supersecretkey',
            'alert_too_old': '26',
        }
        app = main({}, **self.settings)
        self.testapp = TestApp(app)
        self.connection = create_engine(self.db_root_url).raw_connection()

    def tearDown(self):
        DBSession.expire_all()
        self.connection.close()
        self.teardownDb()

    def expected_sms(self, expected_raw_messages, expected_messages, expected_positions):
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT * FROM sms.raw_message')
            raw_messages = cursor.fetchall()
            eq_(raw_messages, expected_raw_messages)

            cursor.execute('SELECT * FROM sms.message')
            messages = cursor.fetchall()
            eq_(messages, expected_messages)

            cursor.execute('SELECT id, device_info_serial, date_time, lat, lon, ST_AsText(location) FROM sms.position')
            positions = cursor.fetchall()
            eq_(positions, expected_positions)

    def test_debugnogps(self):
        params = {
            'from': u'1234567890',
            'message': u'1607,4099,0000,014022,031,00820202020204020200,0,722',
            'message_id': u'7ba817ec-0c78-41cd-be10-7907ff787d39',
            'sent_to': u'0987654321',
            'secret': u'supersecretkey',
            'device_id': u'a gateway id',
            'sent_timestamp': u'1424873155000'
        }
        self.testapp.post('/messages', params)

        # assert rows inserted
        expected_raw_messages = [(1, '7ba817ec-0c78-41cd-be10-7907ff787d39', u'1234567890', u'1607,4099,0000,014022,031,00820202020204020200,0,722', u'0987654321', u'a gateway id', datetime.datetime(2015, 2, 25, 14, 5, 55))]
        expected_messages = [(1, 1607, datetime.datetime(2015, 2, 25, 14, 5, 55), 4.099, 0.0, u'014022,031,00820202020204020200,0,722')]
        expected_positions = []
        self.expected_sms(expected_raw_messages, expected_messages, expected_positions)

    def test_debug3gps(self):
        params = {
            'from': u'1234567890',
            'message': u'1607,4099,0000,014022,031,00820202020204020200,0,722,15133,52797,49561568,523572094,15133,53335,49694351,523804057,15133,53161,49624783,523701953',
            'message_id': u'7ba817ec-0c78-41cd-be10-7907ff787d39',
            'sent_to': u'0987654321',
            'secret': u'supersecretkey',
            'device_id': u'a gateway id',
            'sent_timestamp': u'1424873155000'
        }
        self.testapp.post('/messages', params)

        # assert rows inserted
        expected_raw_messages = [(1, '7ba817ec-0c78-41cd-be10-7907ff787d39', u'1234567890', u'1607,4099,0000,014022,031,00820202020204020200,0,722,15133,52797,49561568,523572094,15133,53335,49694351,523804057,15133,53161,49624783,523701953', u'0987654321', u'a gateway id', datetime.datetime(2015, 2, 25, 14, 5, 55))]
        expected_messages = [(1, 1607, datetime.datetime(2015, 2, 25, 14, 5, 55), 4.099, 0.0, u'014022,031,00820202020204020200,0,722')]
        expected_positions = [(1, 1607, datetime.datetime(2015, 5, 13, 14, 39, 57), 52.3572094, 4.9561568, u'POINT(4.9561568 52.3572094)'), (1, 1607, datetime.datetime(2015, 5, 13, 14, 48, 55), 52.3804057, 4.9694351, u'POINT(4.9694351 52.3804057)'), (1, 1607, datetime.datetime(2015, 5, 13, 14, 46, 1), 52.3701953, 4.9624783, u'POINT(4.9624783 52.3701953)')]
        self.expected_sms(expected_raw_messages, expected_messages, expected_positions)

    def test_duplicate_raw_message(self):
        params = {
            'from': u'1234567890',
            'message': u'1607,4099,0000,014022,031,00820202020204020200,0,722',
            'message_id': u'7ba817ec-0c78-41cd-be10-7907ff787d39',
            'sent_to': u'0987654321',
            'secret': u'supersecretkey',
            'device_id': u'a gateway id',
            'sent_timestamp': u'1424873155000'
        }
        self.testapp.post('/messages', params)

        response = self.testapp.post('/messages', params)
        assert response.json['payload']['success']

        # assert rows inserted
        expected_raw_messages = [(1, '7ba817ec-0c78-41cd-be10-7907ff787d39', u'1234567890', u'1607,4099,0000,014022,031,00820202020204020200,0,722', u'0987654321', u'a gateway id', datetime.datetime(2015, 2, 25, 14, 5, 55))]
        expected_messages = [(1, 1607, datetime.datetime(2015, 2, 25, 14, 5, 55), 4.099, 0.0, u'014022,031,00820202020204020200,0,722')]
        expected_positions = []
        self.expected_sms(expected_raw_messages, expected_messages, expected_positions)

    def test_status_empty_toooldalert(self):
        with assert_raises(AppError) as ex:
            self.testapp.get('/status')

        assert 'Positions have not been received recently' in ex.exception.message

    def test_status_filled(self):
        valid_pos_year = unicode(datetime.datetime.utcnow().year)[2:]
        params = {
            'from': u'1234567890',
            'message': u'1607,4099,0000,014022,031,00820202020204020200,0,722,' +
                       valid_pos_year + u'364,52797,49561568,523572094',
            'message_id': u'7ba817ec-0c78-41cd-be10-7907ff787d39',
            'sent_to': u'0987654321',
            'secret': u'supersecretkey',
            'device_id': u'a gateway id',
            'sent_timestamp': u'1424873155000'
        }
        self.testapp.post('/messages', params)

        response = self.testapp.get('/status')

        eq_(response.status_int, 200)
