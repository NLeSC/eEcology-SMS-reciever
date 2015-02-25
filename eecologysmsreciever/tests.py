from unittest import TestCase
from mock import patch
from pyramid import testing
from pyramid.exceptions import Forbidden
from sqlalchemy.exc import DBAPIError
from .models import RawMessage, DBSession
from .views import recieve_message


class RawMessageTest(TestCase):

    def setUp(self):
        self.settings = {
            'secret_key': 'supersecretkey',
        }
        self.config = testing.setUp(settings=self.settings)
        self.body = {
            'from': '1234567890',
            'message': 'ID1608,4108,0000,10101719,25,00820202020204020200,180914,1243,49842689,524984249,180914,1238,49841742,524983380,180914,1235,49842004,524983903',
            'message_id': '7ba817ec-0c78-41cd-be10-7907ff787d39',
            'sent_to': '0987654321',
            'secret': 'supersecretkey',
            'device_id': 'a device id',
            'sent_timestamp': '1424873155000'
        }

    def tearDown(self):
        testing.tearDown()

    def test_fromRequest(self):
        request = testing.DummyRequest(post=self.body)

        message = RawMessage.fromRequest(request)

        self.assertEqual(message.id, '7ba817ec-0c78-41cd-be10-7907ff787d39')
        self.assertEqual(message.sender, '1234567890')
        self.assertEqual(
            message.message, 'ID1608,4108,0000,10101719,25,00820202020204020200,180914,1243,49842689,524984249,180914,1238,49841742,524983380,180914,1235,49842004,524983903')
        self.assertEqual(message.sent_to, '0987654321')
        self.assertEqual(message.device_id, 'a device id')
        self.assertEqual(message.sent_timestamp, '1424873155000')

    def test_fromRequest_wrongSecret_InvalidException(self):
        self.body['secret'] = 'the wrong secret'
        request = testing.DummyRequest(post=self.body)

        with self.assertRaises(Forbidden) as e:
            RawMessage.fromRequest(request)

        self.assertEqual(e.exception.message, 'Invalid secret')


def setUpDatabase():
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    # postgresql uses a schema, fake it with in-memory sqlite db
    engine.execute("ATTACH DATABASE ':memory:' AS sms")
    DBSession.configure(bind=engine)
    from .models import Base
    Base.metadata.create_all(engine)


class recieve_messageTest(TestCase):

    def setUp(self):
        self.settings = {
            'secret_key': 'supersecretkey',
        }
        self.config = testing.setUp(settings=self.settings)
        self.body = {
            'from': '1234567890',
            'message': 'ID1608,4108,0000,10101719,25,00820202020204020200,180914,1243,49842689,524984249,180914,1238,49841742,524983380,180914,1235,49842004,524983903',
            'message_id': '7ba817ec-0c78-41cd-be10-7907ff787d39',
            'sent_to': '0987654321',
            'secret': 'supersecretkey',
            'device_id': 'a device id',
            'sent_timestamp': '1424873155000'
        }
        setUpDatabase()

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_returnsSuccess(self):
        request = testing.DummyRequest(post=self.body)

        response = recieve_message(request)

        expected = {'payload': {'success': True, 'error': None}}
        self.assertEquals(response, expected)

    def test_insertsRawMessage(self):
        request = testing.DummyRequest(post=self.body)

        recieve_message(request)

        id = '7ba817ec-0c78-41cd-be10-7907ff787d39'
        inserted_row = DBSession.query(RawMessage).get(id)
        self.assertIsNotNone(inserted_row)

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
