# BlackholeBandicoot

Testing web server that accepts any request and at a minimum logs the request
to stdout. To be used by developers or testers, not a production web/app server.

To get started run the following command and then make
requests to http://127.0.0.1:4000/.
```
# Plain app server that will return 200 and {"ok": 1}
docker run -p 4000:4000 closeio/blackholebandicoot

# Return 400 error for every request
docker run -p 4000:4000 -e ERROR_RATE=100 closeio/blackholebandicoot

# Pause 2 seconds for 50% of the requests
docker run -p 4000:4000 -e PAUSE_TIME=2 -e PAUSE_RATE=50 closeio/blackholebandicoot

# Save every request to sqlite3 database
docker run -p 4000:4000 -e SAMPLE_RATE=100 --name blackhole closeio/blackholebandicoot
# Run a test request and output data in requests table
curl -v http://127.0.0.1:4000/testit
docker exec blackhole find db -name '*.db' -exec sqlite3 {} 'select * from requests;' \;
/testit?|127.0.0.1:4000||[["Host", "127.0.0.1:4000"], ["User-Agent", "curl/7.54.0"], ["Accept", "*/*"]]
```


## Configuration options
The following settings can be adjusted via environment variables or a
`config.yml` file (see `config.sample.yml`). The settings in the `config.yml`
file will be checked every 5 seconds so that you can modify the behavior of
running processes without restarting them.


* PAUSE_RATE: Percentage of requests that should pause `PAUSE_TIME` seconds
* PAUSE_TIME: Decimal seconds that will be slept
* SAMPLE_RATE: Percentage of requests that should be written to sqlite3 database
* ERROR_RATE: Percentage of requests that should return 400 reponses instead of 200
* max_old (config file only): Number of rotated sqlite3 database files that should be kept


## Sqlite3 db
Look in the `db` directory for the database files. Run `select * from requests;` to see request data.