1.0.6
-----

- When raw message already exists return OK, instead of error

1.0.5
-----

- Inserts raw message before parsing message, instead of parsing message and then inserting raw message and parsed message.

1.0.4
-----

- Use timestamp without time zone, as it is used in other eEcology tables.

1.0.3
-----

- Debug string changed, detect it by number of columns
- Treat each insert as a seperate transaction. Position duplicates are skipped, but new message is stored.

1.055
-----

- Date time has changed in firmware 1.055 to

    * date = 2 digits year (base 2000) + 3 digits day of year
    * time = seconds of day

1.0.0
-----

-  Initial version
