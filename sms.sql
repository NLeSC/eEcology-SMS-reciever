-- Created from Python prompt with:
-- from eecologysmsreciever.models import dump_ddl
-- print dump_ddl()

CREATE SCHEMA sms;

CREATE TABLE sms.raw_messages (
	message_id UUID NOT NULL,
	sender VARCHAR,
	body VARCHAR,
	sent_to VARCHAR,
	device_id VARCHAR,
	sent_timestamp TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (message_id)
);

CREATE TABLE sms.messages (
	message_id UUID NOT NULL,
	device_info_serial INTEGER,
	date_time TIMESTAMP WITH TIME ZONE,
	battery_voltage FLOAT(3),
	memory_usage FLOAT(1),
	debug_info VARCHAR,
	PRIMARY KEY (message_id),
	FOREIGN KEY(message_id) REFERENCES sms.raw_messages (message_id)
);

CREATE TABLE sms.positions (
	message_id UUID NOT NULL,
	date_time TIMESTAMP WITH TIME ZONE NOT NULL,
	lon FLOAT,
	lat FLOAT,
	PRIMARY KEY (message_id, date_time),
	FOREIGN KEY(message_id) REFERENCES sms.messages (message_id)
);
