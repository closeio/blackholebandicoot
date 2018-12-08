"""BlackholeBandicoot."""

import json
import os
import random
import sqlite3
import threading
import time
import uuid

import envparse

import yaml

from flask import Flask, Response, request

DB_POOL_SIZE = 5
MAX_OLD_DBS = 2
MAX_DB_SIZE = 10000000  # Bytes
CONFIG_REFRESH_TIME = 5  # Seconds

app = Flask(__name__)
env = envparse.Env()

class DB(object):
    def __init__(self, base, num):
        self.name = 'db/{}-{}.db'.format(base, num)
        self.db = None

    def create_db(self):
        if not self.db:
            self.db = sqlite3.connect(self.name)
            self.db.execute('create table requests (host text, path text, payload text, headers text)')

    def too_big(self):
        c = self.db.cursor()
        c.execute('SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();')
        size = int(c.fetchone()[0])
        if size > MAX_DB_SIZE:
            print ('Reached max size, closing db {} ({})'.format(self.name, size))
            self.db.close()
            return True

    def insert_request(self, r):
        data = r.get_data(cache=False, as_text=True)
        headers = json.dumps([(k, v) for k, v in r.headers])
        sql = 'insert into requests (host, path, payload, headers) values (?, ?, ?, ?)'
        self.db.execute(sql, (r.full_path, r.host, data, headers))
        self.db.commit()


class DBPool(object):
    def __init__(self, size=5, max_old=None):
        self.base_name = str(uuid.uuid4())
        self.counter = 1
        self.size = size
        self.free_db = []
        self.old = []
        self.max_old = max_old
        self.lock = threading.Lock()
        for i in range(0, size):
            self.free_db.append(DB(self.base_name, self.counter))
            self.counter += 1

    def get_db(self):
        """Checkout db connection from pool."""

        self.lock.acquire()
        try:
            while True:
                if self.free_db:
                    db = self.free_db.pop()
                    db.create_db()
                    return db
                print ('Waiting for db')
                time.sleep(.02)
        finally:
            self.lock.release()

    def release_db(self, db):
        """
        Release connection back into pool.

        Checks size of DB and rotates to a new connection if over max size.
        Deletes old data files if max old files is set.
        """

        self.lock.acquire()
        try:
            if db.too_big():
                self.free_db.append(DB(self.base_name, self.counter))
                self.counter += 1
                if self.max_old:
                    self.old.insert(0, db.name)
                    if len(self.old) >= self.max_old:
                        old = self.old.pop()
                        try:
                            os.remove(old)
                        except Exception:
                            pass
            else:
                self.free_db.append(db)
        finally:
            self.lock.release()


db_pool = DBPool(DB_POOL_SIZE, MAX_OLD_DBS)
last_config = 0
pause_time = env('PAUSE_TIME', cast=float, default=0)
pause_rate = env('PAUSE_RATE', cast=int, default=0)

sample_rate = env('SAMPLE_RATE', cast=int, default=0)

error_rate = env('ERROR_RATE', cast=int, default=0)

def print_config():
    print ('Pause time:{} Random pause:{} Sample rate:{}'.format(
        pause_time, pause_rate, sample_rate
        ))


def load_config():
    """Dynamically reads config settings from disk file."""

    global error_rate, local_config, last_config, pause_time, pause_rate, sample_rate

    if not os.path.isfile('config.yml') or time.time() - last_config < CONFIG_REFRESH_TIME:
        return

    last_config = time.time()
    try:
        with open('config.yml') as f:
            config = yaml.load(f)
            config = config['config']
            db_pool.max_old = config['max_old']
            pause_time = float(config['pause'])
            sample_rate = int(config['sample_rate'])
            pause_rate = int(config['pause_rate'])
            error_rate = int(config['error_rate'])
            print_config()
    except Exception as e:
        print ('Error loading config', e)


def should_i(rate):
    return (rate != 0 and
           (rate == 100 or random.randint(1, 100) <= rate))

print_config()


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    """Process all requests."""

    load_config()
    db = None
    try:
        if should_i(sample_rate):
            db = db_pool.get_db()
            db.insert_request(request)
        if should_i(pause_rate):
            time.sleep(pause_time)
        if should_i(error_rate):
            return_code = 400
        else:
            return_code = 200

    except Exception:
        raise
    finally:
        if db:
            db_pool.release_db(db)
    return Response('{"ok": 1}', mimetype='application/json', status=return_code)
