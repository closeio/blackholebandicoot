# BlackholeBandicoot

Flask app that accepts any request and at a minimum logs the request
to stdout.

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
