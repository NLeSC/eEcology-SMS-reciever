eEcology-SMS-reciever
=====================

Store recieved SMS messages into a database table.

Accepts SMS messages from SMSSync Android app see https://play.google.com/store/apps/details?id=org.addhen.smssync, http://smssync.ushahidi.com/ and https://github.com/ushahidi/SMSSync .

Getting Started
---------------

    cd <directory containing this file>
    virtualenv env
    . env/bin/activate
    python setup.py develop
    cp development.ini-dist development.ini

Edit development.ini to configure db connection, etc.

    initialize_eEcology-SMS-reciever_db development.ini
    pserve development.ini

SMSSync configuration
---------------------

Configure Sync URL with:

* Secret key = Same as value of 'secret_key' key in *ini file.
* Keyword = '^ID', all tracker messages start with 'ID'
* URL = Depends on where you run this server and if it is reversed proxied.
* HTTP Method = POST
* Data Format = JSON
