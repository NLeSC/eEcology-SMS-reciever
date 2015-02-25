-- How to create this file see http://docs.sqlalchemy.org/en/rel_0_9/faq/metadata_schema.html#how-can-i-get-the-create-table-drop-table-output-as-a-string
CREATE SCHEMA sms;

CREATE TABLE sms.raw_messages (
    id TEXT NOT NULL,
    sender TEXT,
    message TEXT,
    sent_to TEXT,
    device_id TEXT,
    sent_timestamp TEXT,
    PRIMARY KEY (id)
);
