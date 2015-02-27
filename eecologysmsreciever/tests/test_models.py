from datetime import datetime
import uuid
from unittest import TestCase
from pyramid import testing
from pyramid.exceptions import Forbidden
from pytz import utc
from ..models import RawMessage, Message, dump_ddl


class RawMessageTest(TestCase):

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
            'device_id': u'a device id',
            'sent_timestamp': u'1424873155000'
        }

    def tearDown(self):
        testing.tearDown()

    def test_from_request(self):
        request = testing.DummyRequest(post=self.body)

        message = RawMessage.from_request(request)

        self.assertEqual(message.message_id, uuid.UUID('7ba817ec-0c78-41cd-be10-7907ff787d39'))
        self.assertEqual(message.sender, '1234567890')
        self.assertEqual(
            message.body, 'ID1608,4108,0000,10101719,25,00820202020204020200,180914,1243,49842689,524984249,180914,1238,49841742,524983380,180914,1235,49842004,524983903')
        self.assertEqual(message.sent_to, '0987654321')
        self.assertEqual(message.device_id, 'a device id')
        self.assertEqual(message.sent_timestamp, datetime(2015, 2, 25, 14, 5, 55))

    def test_from_request_wrongSecret_InvalidException(self):
        self.body['secret'] = 'the wrong secret'
        request = testing.DummyRequest(post=self.body)

        with self.assertRaises(Forbidden) as e:
            RawMessage.from_request(request)

        self.assertEqual(e.exception.message, 'Invalid secret')


class MessageTest(TestCase):

    def test_fromBody_nodebugnogps(self):
        """Example 1 in api doc"""
        body = u'ID1608,4108,0000'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertIsNone(message.debug_info)
        self.assertEqual(len(message.positions), 0)

    def test_fromBody_nogps(self):
        """Example 2 in api doc"""
        body = u'ID1608,4108,0000,10101719,25,00820202020204020200'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'10101719,25,00820202020204020200')
        self.assertEqual(len(message.positions), 0)

    def test_fromBody_nogpsyet(self):
        """Example 3 in api doc"""
        body = u'ID1608,4108,0000,10101719,25,00820202020204020200,,,,'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'10101719,25,00820202020204020200')
        self.assertEqual(len(message.positions), 0)


    def test_fromBody_debug1gps(self):
        """Example 4 in api doc"""
        body = u'ID1608,4108,0000,10101719,25,00820202020204020200,180914,1243,49842689,524984249'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'10101719,25,00820202020204020200')
        self.assertEqual(len(message.positions), 1)
        self.assertEqual(message.positions[0].date_time, datetime(2014, 9, 18, 12, 43, tzinfo=utc))
        self.assertEqual(message.positions[0].lon, 4.9842689)
        self.assertEqual(message.positions[0].lat, 52.4984249)


    def test_fromBody_debug3gps(self):
        """Example 5 in api doc"""
        body = u'ID1608,4108,0000,10101719,25,00820202020204020200,180914,1243,49842689,524984249,180914,1238,49841742,524983380,180914,1235,49842004,524983903'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'10101719,25,00820202020204020200')
        self.assertEqual(len(message.positions), 3)
        self.assertEqual(message.positions[0].date_time, datetime(2014, 9, 18, 12, 43, tzinfo=utc))
        self.assertEqual(message.positions[0].lon, 4.9842689)
        self.assertEqual(message.positions[0].lat, 52.4984249)
        self.assertEqual(message.positions[1].date_time, datetime(2014, 9, 18, 12, 38, tzinfo=utc))
        self.assertEqual(message.positions[1].lon, 4.9841742)
        self.assertEqual(message.positions[1].lat, 52.4983380)
        self.assertEqual(message.positions[2].date_time, datetime(2014, 9, 18, 12, 35, tzinfo=utc))
        self.assertEqual(message.positions[2].lon, 4.9842004)
        self.assertEqual(message.positions[2].lat, 52.4983903)

    def test_fromBody_4gps(self):
        """Example 6 in api doc"""
        body = u'ID1608,4108,0000,180914,1243,49842689,524984249,180914,1238,49841742,524983380,180914,1235,49842004,524983903,180914,1232,49842014,524983503'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertIsNone(message.debug_info)
        self.assertEqual(len(message.positions), 4)
        self.assertEqual(message.positions[0].date_time, datetime(2014, 9, 18, 12, 43, tzinfo=utc))
        self.assertEqual(message.positions[0].lon, 4.9842689)
        self.assertEqual(message.positions[0].lat, 52.4984249)
        self.assertEqual(message.positions[1].date_time, datetime(2014, 9, 18, 12, 38, tzinfo=utc))
        self.assertEqual(message.positions[1].lon, 4.9841742)
        self.assertEqual(message.positions[1].lat, 52.4983380)
        self.assertEqual(message.positions[2].date_time, datetime(2014, 9, 18, 12, 35, tzinfo=utc))
        self.assertEqual(message.positions[2].lon, 4.9842004)
        self.assertEqual(message.positions[2].lat, 52.4983903)
        self.assertEqual(message.positions[3].date_time, datetime(2014, 9, 18, 12, 32, tzinfo=utc))
        self.assertEqual(message.positions[3].lon, 4.9842014)
        self.assertEqual(message.positions[3].lat, 52.4983503)

    def test_fromBody_noId(self):
        body = u'Meet you at the bar tonight'
        with self.assertRaises(ValueError):
            Message.from_body(body)

    def test_fromBody_zeropadded(self):
        """Example 1 in api doc"""
        body = u'ID0001,0002,0003'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1)
        self.assertEqual(message.battery_voltage, 2)
        self.assertEqual(message.memory_usage, 0.3)
        self.assertIsNone(message.debug_info)
        self.assertEqual(len(message.positions), 0)


class DumpDDLTest(TestCase):
    def test_it(self):
        output = dump_ddl()
        self.assertIn('sms.messages', output)
        self.assertIn('sms.positions', output)
