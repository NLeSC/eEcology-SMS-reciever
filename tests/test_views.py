from datetime import datetime
from unittest import TestCase
from mock import patch, DEFAULT, call
from pytz import utc

from pyramid import testing
from nose.tools import eq_
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from eecologysmsreciever.models import DBSession, Position
from eecologysmsreciever.views import recieve_message, status


class recieve_messageTest(TestCase):

    def setUp(self):
        self.settings = {
            'secret_key': 'supersecretkey',
        }
        self.config = testing.setUp(settings=self.settings)
        self.body = {
            'from': u'1234567890',
            'message': u'1607,4099,0000,014022,031,00820202020204020200,0,722,15133,52797,49561568,523572094,15133,53335,49694351,523804057,15133,53161,49624783,523701953',
            'message_id': u'7ba817ec-0c78-41cd-be10-7907ff787d39',
            'sent_to': u'0987654321',
            'secret': u'supersecretkey',
            'device_id': u'a gateway id',
            'sent_timestamp': u'1424873155000'
        }

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    @patch('eecologysmsreciever.views.DBSession')
    def test_sets_timezone2utc(self, mocked_DBSession):
        request = testing.DummyRequest(post=self.body)

        recieve_message(request)

        mocked_DBSession.execute.assert_called_once_with("SET TIME ZONE 'UTC'")

    @patch('eecologysmsreciever.views.DBSession')
    def test_returnsSuccess(self, mocked_DBSession):
        request = testing.DummyRequest(post=self.body)

        response = recieve_message(request)

        expected = {'payload': {'success': True, 'error': None}}
        self.assertEquals(response, expected)

    @patch('eecologysmsreciever.views.DBSession')
    def test_insertsRawMessage(self, mocked_DBSession):
        request = testing.DummyRequest(post=self.body)

        recieve_message(request)

        assert mocked_DBSession.add.times_called(5)
        assert mocked_DBSession.commit.times_called(2)
        assert mocked_DBSession.begin_nested.times_called(3)
        # TODO assert what add() was called with

    @patch('eecologysmsreciever.views.DBSession')
    def test_badSecret_returnsUnsuccess(self, mocked_DBSession):
        self.body['secret'] = 'the wrong secret'
        request = testing.DummyRequest(post=self.body)

        response = recieve_message(request)

        expected = {'payload': {'success': False, 'error': 'Forbidden'}}
        self.assertEquals(response, expected)

    @patch('eecologysmsreciever.views.DBSession')
    def test_dbError_returnsUnsuccess(self, mocked_DBSession):
        mocked_DBSession.add.side_effect = DBAPIError(1, 2, 3, 4)
        request = testing.DummyRequest(post=self.body)

        response = recieve_message(request)

        expected = {'payload': {'success': False, 'error': 'Database error'}}
        self.assertEquals(response, expected)

    @patch('eecologysmsreciever.views.DBSession')
    def test_badText_returnsUnsuccess(self, mocked_DBSession):
        self.body['message'] = u'hallo'
        request = testing.DummyRequest(post=self.body)

        response = recieve_message(request)

        expected = {'payload': {'success': False, 'error': 'Invalid message'}}
        self.assertEquals(response, expected)

    @patch('eecologysmsreciever.views.DBSession')
    def test_emptyText_returnsUnsuccess(self, mocked_DBSession):
        self.body['message'] = u''
        request = testing.DummyRequest(post=self.body)

        response = recieve_message(request)

        expected = {'payload': {'success': False, 'error': 'Invalid message'}}
        self.assertEquals(response, expected)

    @patch('eecologysmsreciever.views.DBSession')
    def test_halfText_returnsUnsuccess(self, mocked_DBSession):
        self.body['message'] = u'1608,4108,0000,10101719,25,00820202020'
        request = testing.DummyRequest(post=self.body)

        response = recieve_message(request)

        expected = {'payload': {'success': False, 'error': 'Invalid message'}}
        self.assertEquals(response, expected)

    @patch('eecologysmsreciever.views.DBSession')
    def test_integrationTestFromSMSSyncApp_returnsUnsuccess(self, mocked_DBSession):
        # In the SMS Sync app > edit custom web service there is a `test integration` button
        # this will send a request to the webservice with only the secret key, so it is missing a message
        body = {
            'secret': u'supersecretkey'
        }
        request = testing.DummyRequest(post=body)

        response = recieve_message(request)

        expected = {'payload': {'success': False, 'error': 'Invalid message'}}
        self.assertEquals(response, expected)

    @patch('eecologysmsreciever.views.DBSession')
    def test_rawmessagealreadyexists_returnsSuccess(self, mocked_DBSession):
        mocked_DBSession.add.side_effect = IntegrityError(1, 2, 3, 4)
        request = testing.DummyRequest(post=self.body)

        response = recieve_message(request)

        expected = {'payload': {'success': True, 'error': None}}
        self.assertEquals(response, expected)


    @patch('eecologysmsreciever.views.DBSession')
    def test_positionalreadyexists_returnsSuccess(self, mocked_DBSession):
        def side_effect(arg):
            if isinstance(arg, Position):
                return IntegrityError(1, 2, 3, 4)
            else:
                return DEFAULT

        mocked_DBSession.add.side_effect = side_effect

        request = testing.DummyRequest(post=self.body)

        response = recieve_message(request)

        expected = {'payload': {'success': True, 'error': None}}
        self.assertEquals(response, expected)


class StatusTest(TestCase):

    @patch('eecologysmsreciever.views.utcnow')
    @patch('eecologysmsreciever.views.DBSession')
    def test_it(self, mocked_DBSession, mocked_utcnow):
        mocked_utcnow.return_value = datetime(2014, 9, 18, 12, 43, tzinfo=utc)
        request = testing.DummyRequest()
        request.registry.settings = {'alert_too_old': 4}

        response = status(request)

        self.assertTrue('version' in response)
        mocked_DBSession.execute.assert_called_once_with("SET TIME ZONE 'UTC'")

    @patch('eecologysmsreciever.views.DBSession')
    def test_baddbconnection(self, mocked_DBSession):
        mocked_DBSession.execute.side_effect = DBAPIError(1, 2, 3, 4)

        with self.assertRaises(DBAPIError):
            status(testing.DummyRequest())

    @patch('eecologysmsreciever.views.utcnow')
    @patch('eecologysmsreciever.views.DBSession')
    def test_positiontooold(self, mocked_DBSession, mocked_utcnow):
        mocked_DBSession.execute.side_effect = NoResultFound()
        mocked_utcnow.return_value = datetime(2015, 9, 18, 12, 43, tzinfo=utc)
        request = testing.DummyRequest()
        request.registry.settings = {'alert_too_old': 4}

        with self.assertRaises(NoResultFound):
            status(request)

