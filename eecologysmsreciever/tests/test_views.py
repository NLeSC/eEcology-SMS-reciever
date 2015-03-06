from unittest import TestCase
from mock import patch
from pyramid import testing
from sqlalchemy.exc import DBAPIError
from ..models import DBSession
from ..views import recieve_message, status


class recieve_messageTest(TestCase):

    def setUp(self):
        self.settings = {
            'secret_key': 'supersecretkey',
        }
        self.config = testing.setUp(settings=self.settings)
        self.body = {
            'from': u'1234567890',
            'message': u'ID1608,4108,0000,10101719,25,00820202020204020200,180914,1243,49842689,524984249,180914,1238,49841742,524983380,180914,1235,49842004,524983903',
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
    def test_returnsSuccess(self, mocked_DBSession):
        request = testing.DummyRequest(post=self.body)

        response = recieve_message(request)

        expected = {'payload': {'success': True, 'error': None}}
        self.assertEquals(response, expected)

    @patch('eecologysmsreciever.views.DBSession')
    def test_insertsRawMessage(self, mocked_DBSession):
        request = testing.DummyRequest(post=self.body)

        recieve_message(request)

        assert mocked_DBSession.add.called
        assert mocked_DBSession.commit.called
        # TODO assert what add() was called with

    def test_badSecret_returnsUnsuccess(self):
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


class StatusTest(TestCase):

    @patch('eecologysmsreciever.views.DBSession')
    def test_it(self, mocked_DBSession):

        response = status(testing.DummyRequest())

        self.assertTrue('version' in response)
        mocked_DBSession.execute.assert_called_once_with('SELECT TRUE')

    @patch('eecologysmsreciever.views.DBSession')
    def test_baddbconnection(self, mocked_DBSession):
        mocked_DBSession.execute.side_effect = DBAPIError(1, 2, 3, 4)

        with self.assertRaises(DBAPIError):
            status(testing.DummyRequest())
