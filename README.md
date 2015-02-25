eEcology-SMS-reciever
=====================

[![Build Status](https://travis-ci.org/NLeSC/eEcology-SMS-reciever.svg?branch=master)](https://travis-ci.org/NLeSC/eEcology-SMS-reciever)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/NLeSC/eEcology-SMS-reciever/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/NLeSC/eEcology-SMS-reciever/?branch=master)
[![Code Coverage](https://scrutinizer-ci.com/g/NLeSC/eEcology-SMS-reciever/badges/coverage.png?b=master)](https://scrutinizer-ci.com/g/NLeSC/eEcology-SMS-reciever/?branch=master)

Webservice to store SMS messages into a database table.

Accepts SMS messages from SMSSync Android app see https://play.google.com/store/apps/details?id=org.addhen.smssync, http://smssync.ushahidi.com/ and https://github.com/ushahidi/SMSSync .

Getting Started
---------------

    cd <directory containing this file>
    virtualenv env
    . env/bin/activate
    python setup.py develop
    cp development.ini-dist development.ini

Edit development.ini to configure db connection, etc.

Create sms database schema:

    psql -h db.e-ecology.sara.nl eecology < sms.sql

Grant `<someone>` user rights to perform inserts on table.

    GRANT USAGE ON SCHEMA sms TO <someone>;
    GRANT INSERT ON sms.messages TO <someone>;

Start service:

    pserve development.ini

Service running at http://localhost:6566/sms/

SMSSync configuration
---------------------

Configure Sync URL with:

* Secret key = Same as value of 'secret_key' key in *ini file.
* Keyword = '^ID', all tracker messages start with 'ID'
* URL = Depends on where you run this server and if it is reversed proxied.
* HTTP Method = POST
* Data Format = URLEncoded

Docker build
------------

### Construct image

1. `sudo docker build -t sverhoeven/smsreciever:1.0.0 .`
2. Export or push to registry

### Run container

1. Import or pull from registry
2. `sudo docker run -p 6566:6566 --env DB_URL="postgresql://*******:********@db.e-ecology.sara.nl/eecology?sslmode=require" --env SECRET_KEY=supersecretkey -d --name smsreciever sverhoeven/smsreciever:1.0.0`

Error log is available with `sudo docker logs smsreciever`.

Web application will run on http://localhost:6566/sms/
