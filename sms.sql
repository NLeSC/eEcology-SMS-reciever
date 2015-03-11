-- Created from Python prompt with:
-- from eecologysmsreciever.models import dump_ddl
-- print dump_ddl()

CREATE SCHEMA sms;

CREATE TABLE sms.raw_message (
	id SERIAL NOT NULL,
	message_id UUID,
	sent_from VARCHAR,
	body VARCHAR,
	sent_to VARCHAR,
	gateway_id VARCHAR,
	sent_timestamp TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	UNIQUE (message_id)
);


CREATE TABLE sms.message (
	id INTEGER NOT NULL,
	device_info_serial INTEGER,
	date_time TIMESTAMP WITH TIME ZONE,
	battery_voltage FLOAT(3),
	memory_usage FLOAT(1),
	debug_info VARCHAR,
	PRIMARY KEY (id),
	FOREIGN KEY(id) REFERENCES sms.raw_message (id)
);


CREATE TABLE sms.position (
	id INTEGER NOT NULL,
	device_info_serial INTEGER,
	date_time TIMESTAMP WITH TIME ZONE NOT NULL,
	lon FLOAT,
	lat FLOAT,
	location geometry(POINT,4326),
	PRIMARY KEY (id, date_time),
	UNIQUE (device_info_serial, date_time),
	FOREIGN KEY(id) REFERENCES sms.message (id)
);

CREATE INDEX "idx_position_location" ON "sms"."position" USING GIST (location);

-- create user to insert sms messages
--
-- CREATE USER smswriter WITH LOGIN PASSWORD '<please change me>';
-- GRANT USAGE ON SCHEMA sms TO smswriter;
-- GRANT INSERT ON sms.raw_message TO smswriter;
-- GRANT SELECT (id) ON sms.raw_message TO smswriter;
-- GRANT INSERT ON sms.message TO smswriter;
-- GRANT INSERT ON sms.position TO smswriter;
-- GRANT USAGE on SEQUENCE sms.raw_message_id_seq TO smswriter;
