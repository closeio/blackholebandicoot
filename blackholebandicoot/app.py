"""BlackholeBandicoot."""

import os
import random
import sqlite3
import time
import uuid

import yaml

from flask import Flask, Response, request

DB_POOL_SIZE = 5
MAX_OLD_DBS = 2
MAX_DB_SIZE = 10000000  # Bytes
CONFIG_REFRESH_TIME = 5  # Seconds

app = Flask(__name__)


class DB(object):
    def __init__(self, base, num):
        self.name = 'db/{}-{}.db'.format(base, num)
        self.db = None

    def create_db(self):
        if not self.db:
            self.db = sqlite3.connect(self.name)
            self.db.execute('create table requests (host text, path text, payload text)')

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

        sql = "insert into requests (host, path, payload) values ('{}', '{}', '{}')".format(
                        r.full_path, r.host, data)
        self.db.execute(sql)
        self.db.commit()


class DBPool(object):
    def __init__(self, size=5, max_old=None):
        self.base_name = str(uuid.uuid4())
        self.counter = 1
        self.size = size
        self.free_db = []
        self.old = []
        self.max_old = max_old
        for i in range(0, size):
            self.free_db.append(DB(self.base_name, self.counter))
            self.counter += 1


    def get_db(self):
        """Checkout db connection from pool."""

        while True:
            if self.free_db:
                db = self.free_db.pop()
                db.create_db()
                return db
            print ('Waiting for db')
            time.sleep(.02)

    def release_db(self, db):
        """
        Release connection back into pool.

        Checks size of DB and rotates to a new connection if over max size.
        Deletes old data files if max old files is set.
        """

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


db_pool = DBPool(DB_POOL_SIZE, MAX_OLD_DBS)
last_config = 0
pause_time = 0
random_pause = 0


def load_config():
    """Dynamically reads config settings from disk file."""

    global local_config, last_config, pause_time, random_pause
    if time.time() - last_config < CONFIG_REFRESH_TIME:
        return
    print ('Loading config')
    last_config = time.time()
    with open('config.yml') as f:
        config = yaml.load(f)
        config = config['config']
        db_pool.max_old = config['max_old']
        pause_time = config['pause']
        random_pause = config['random_pause']


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    """Process all requests."""

    load_config()
    db = db_pool.get_db()

    try:
        db.insert_request(request)
        if ((random_pause and random.randint(0, random_pause - 1) == 1) or
                not random_pause):
            time.sleep(pause_time)

    except Exception:
        raise
    finally:
        db_pool.release_db(db)
    return Response('{ok: 1}', mimetype='application/json')
