from datetime import datetime
import uuid
from unittest import TestCase
from pyramid import testing
from pyramid.exceptions import Forbidden
from pytz import utc
from eecologysmsreciever.models import RawMessage, Message
from eecologysmsreciever.models import dump_ddl


class RawMessageTest(TestCase):

    def setUp(self):
        self.settings = {
            'secret_key': 'supersecretkey',
        }
        self.config = testing.setUp(settings=self.settings)
        self.body = {
            'from': u'1234567890',
            'message': u'1608,4108,0000,014023,019,00820202020204020200,3,842,14261,45780,49842689,524984249,14261,45480,49841742,524983380,14261,45300,49842004,524983903',
            'message_id': u'7ba817ec-0c78-41cd-be10-7907ff787d39',
            'sent_to': u'0987654321',
            'secret': u'supersecretkey',
            'device_id': u'a gateway id',
            'sent_timestamp': u'1424873155000'
        }

    def tearDown(self):
        testing.tearDown()

    def test_from_request(self):
        request = testing.DummyRequest(post=self.body)

        message = RawMessage.from_request(request)

        self.assertEqual(message.message_id, uuid.UUID('7ba817ec-0c78-41cd-be10-7907ff787d39'))
        self.assertEqual(message.sent_from, '1234567890')
        self.assertEqual(message.body, '1608,4108,0000,014023,019,00820202020204020200,3,842,14261,45780,49842689,524984249,14261,45480,49841742,524983380,14261,45300,49842004,524983903')
        self.assertEqual(message.sent_to, '0987654321')
        self.assertEqual(message.gateway_id, 'a gateway id')
        self.assertEqual(message.sent_timestamp, datetime(2015, 2, 25, 14, 5, 55))

    def test_from_request_wrongSecret_InvalidException(self):
        self.body['secret'] = 'the wrong secret'
        request = testing.DummyRequest(post=self.body)

        with self.assertRaises(Forbidden) as e:
            RawMessage.from_request(request)

        self.assertEqual(e.exception.message, 'Invalid secret')


class MessageTest(TestCase):

    def test_fromRaw_nodebugnogps(self):
        """Example 1 in api doc"""
        raw_message = RawMessage()
        raw_message.id = 1234
        raw_message.body = u'1608,4108,0000'
        raw_message.sent_timestamp = datetime(2015, 2, 25, 14, 5, 55)

        message = Message.from_raw(raw_message)

        self.assertEqual(message.id, 1234)
        self.assertEqual(message.date_time, datetime(2015, 2, 25, 14, 5, 55))
        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertIsNone(message.debug_info)
        self.assertEqual(len(message.positions), 0)

    def test_fromBody_nodebugnogps(self):
        """Example 1 in api doc"""
        body = u'1608,4108,0000'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertIsNone(message.debug_info)
        self.assertEqual(len(message.positions), 0)

    def test_fromBody_nogps(self):
        """Example 2 in api doc"""
        body = u'1608,4108,0000,014023,019,00820202020204020200,3,842'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'014023,019,00820202020204020200,3,842')
        self.assertEqual(len(message.positions), 0)

    def test_fromBody_nogps2(self):
        """Example 2 in api doc 2"""
        body = u'1611,4011,0000,013022,011,00820202020204020200,3,15'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1611)
        self.assertEqual(message.battery_voltage, 4.011)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'013022,011,00820202020204020200,3,15')
        self.assertEqual(len(message.positions), 0)


    def test_fromBody_nogpsyet(self):
        """Example 3 in api doc"""
        body = u'1608,4108,0000,014023,019,00820202020204020200,3,842,,,,'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'014023,019,00820202020204020200,3,842')
        self.assertEqual(len(message.positions), 0)

    def test_fromBody_debug1gps(self):
        """Example 4 in api doc"""
        body = u'1608,4108,0000,014023,019,00820202020204020200,3,842,14261,45780,49842689,524984249'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'014023,019,00820202020204020200,3,842')
        self.assertEqual(len(message.positions), 1)
        self.assertEqual(message.positions[0].date_time, datetime(2014, 9, 18, 12, 43, tzinfo=utc))
        self.assertEqual(message.positions[0].lon, 4.9842689)
        self.assertEqual(message.positions[0].lat, 52.4984249)
        self.assertEqual(message.positions[0].location, 'SRID=4326;POINT(4.9842689 52.4984249)')

    def test_fromBody_debug3gps(self):
        """Example 5 in api doc"""
        body = u'1608,4108,0000,014023,019,00820202020204020200,3,842,14261,45780,49842689,524984249,14261,45480,49841742,524983380,14261,45300,49842004,524983903'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'014023,019,00820202020204020200,3,842')
        self.assertEqual(len(message.positions), 3)
        self.assertEqual(message.positions[0].date_time, datetime(2014, 9, 18, 12, 43, tzinfo=utc))
        self.assertEqual(message.positions[0].lon, 4.9842689)
        self.assertEqual(message.positions[0].lat, 52.4984249)
        self.assertEqual(message.positions[0].location, 'SRID=4326;POINT(4.9842689 52.4984249)')
        self.assertEqual(message.positions[1].date_time, datetime(2014, 9, 18, 12, 38, tzinfo=utc))
        self.assertEqual(message.positions[1].lon, 4.9841742)
        self.assertEqual(message.positions[1].lat, 52.4983380)
        self.assertEqual(message.positions[1].location, 'SRID=4326;POINT(4.9841742 52.498338)')
        self.assertEqual(message.positions[2].date_time, datetime(2014, 9, 18, 12, 35, tzinfo=utc))
        self.assertEqual(message.positions[2].lon, 4.9842004)
        self.assertEqual(message.positions[2].lat, 52.4983903)
        self.assertEqual(message.positions[2].location, 'SRID=4326;POINT(4.9842004 52.4983903)')

    def test_fromBody_debug3gps2(self):
        """Example 5 in api doc 2"""
        body = u'1607,4099,0000,014022,031,00820202020204020200,0,722,15133,52797,49561568,523572094,15133,53335,49694351,523804057,15133,53161,49624783,523701953'
        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1607)
        self.assertEqual(message.battery_voltage, 4.099)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'014022,031,00820202020204020200,0,722')
        self.assertEqual(len(message.positions), 3)
        self.assertEqual(message.positions[0].date_time, datetime(2015, 5, 13, 14, 39, 57, tzinfo=utc))
        self.assertEqual(message.positions[0].lon, 4.9561568)
        self.assertEqual(message.positions[0].lat, 52.3572094)
        self.assertEqual(message.positions[0].location, 'SRID=4326;POINT(4.9561568 52.3572094)')
        self.assertEqual(message.positions[1].date_time, datetime(2015, 5, 13, 14, 48, 55, tzinfo=utc))
        self.assertEqual(message.positions[1].lon, 4.9694351)
        self.assertEqual(message.positions[1].lat, 52.3804057)
        self.assertEqual(message.positions[1].location, 'SRID=4326;POINT(4.9694351 52.3804057)')
        self.assertEqual(message.positions[2].date_time, datetime(2015, 5, 13, 14, 46, 1, tzinfo=utc))
        self.assertEqual(message.positions[2].lon, 4.9624783)
        self.assertEqual(message.positions[2].lat, 52.3701953)
        self.assertEqual(message.positions[2].location, 'SRID=4326;POINT(4.9624783 52.3701953)')

    def test_fromBody_4gps(self):
        """Example 6 in api doc"""
        body = u'1608,4108,0000,14261,45780,49842689,524984249,14261,45480,49841742,524983380,14261,45300,49842004,524983903,14261,45120,49842014,524983503'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1608)
        self.assertEqual(message.battery_voltage, 4.108)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertIsNone(message.debug_info)
        self.assertEqual(len(message.positions), 4)
        self.assertEqual(message.positions[0].date_time, datetime(2014, 9, 18, 12, 43, tzinfo=utc))
        self.assertEqual(message.positions[0].lon, 4.9842689)
        self.assertEqual(message.positions[0].lat, 52.4984249)
        self.assertEqual(message.positions[0].location, 'SRID=4326;POINT(4.9842689 52.4984249)')
        self.assertEqual(message.positions[1].date_time, datetime(2014, 9, 18, 12, 38, tzinfo=utc))
        self.assertEqual(message.positions[1].lon, 4.9841742)
        self.assertEqual(message.positions[1].lat, 52.4983380)
        self.assertEqual(message.positions[1].location, 'SRID=4326;POINT(4.9841742 52.498338)')
        self.assertEqual(message.positions[2].date_time, datetime(2014, 9, 18, 12, 35, tzinfo=utc))
        self.assertEqual(message.positions[2].lon, 4.9842004)
        self.assertEqual(message.positions[2].lat, 52.4983903)
        self.assertEqual(message.positions[2].location, 'SRID=4326;POINT(4.9842004 52.4983903)')
        self.assertEqual(message.positions[3].date_time, datetime(2014, 9, 18, 12, 32, tzinfo=utc))
        self.assertEqual(message.positions[3].lon, 4.9842014)
        self.assertEqual(message.positions[3].lat, 52.4983503)
        self.assertEqual(message.positions[3].location, 'SRID=4326;POINT(4.9842014 52.4983503)')

    def test_fromBody_hour(self):
        """Regression test for wrong hour"""
        body = u'1610,4157,0000,012026,013,00820202020204020200,3,718,16055,43475,56715968,519871672,16055,69404,56719362,519869180,16055,61973,56716411,519868866'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1610)
        self.assertEqual(message.battery_voltage, 4.157)
        self.assertEqual(message.memory_usage, 0.0)
        self.assertEqual(message.debug_info, u'012026,013,00820202020204020200,3,718')
        self.assertEqual(len(message.positions), 3)
        self.assertEqual(message.positions[0].date_time, datetime(2016, 2, 24, 12, 4, 35, tzinfo=utc))
        self.assertEqual(message.positions[0].lon, 5.6715968)
        self.assertEqual(message.positions[0].lat, 51.9871672)
        self.assertEqual(message.positions[0].location, 'SRID=4326;POINT(5.6715968 51.9871672)')
        self.assertEqual(message.positions[1].date_time, datetime(2016, 2, 24, 19, 16, 44, tzinfo=utc))
        self.assertEqual(message.positions[1].lon, 5.6719362)
        self.assertEqual(message.positions[1].lat, 51.9869180)
        self.assertEqual(message.positions[1].location, 'SRID=4326;POINT(5.6719362 51.986918)')
        self.assertEqual(message.positions[2].date_time, datetime(2016, 2, 24, 17, 12, 53, tzinfo=utc))
        self.assertEqual(message.positions[2].lon, 5.6716411)
        self.assertEqual(message.positions[2].lat, 51.9868866)
        self.assertEqual(message.positions[2].location, 'SRID=4326;POINT(5.6716411 51.9868866)')

    def test_fromBody_noId(self):
        body = u'Meet you at the bar tonight'
        with self.assertRaises(ValueError):
            Message.from_body(body)

    def test_fromBody_zeropadded(self):
        """Example 1 in api doc"""
        body = u'0001,0002,0003'

        message = Message.from_body(body)

        self.assertEqual(message.device_info_serial, 1)
        self.assertEqual(message.battery_voltage, 0.002)
        self.assertEqual(message.memory_usage, 0.3)
        self.assertIsNone(message.debug_info)
        self.assertEqual(len(message.positions), 0)


class DumpDDLTest(TestCase):
    def test_it(self):
        output = dump_ddl()
        self.assertIn('sms.message', output)
        self.assertIn('sms.position', output)
