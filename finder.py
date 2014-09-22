#!/usr/bin/env python

"""
twitter-finder is a bot that searches twitter for a set of search terms and then
publishes metrics based on when those terms are found.

Please see the README at https://github.com/chooper/twitter-finder/ for more info
"""

# imports
import os, time, json
from sys import exit
import urlparse
from contextlib import contextmanager
import psycopg2
import tweepy

# import exceptions
from urllib2 import HTTPError

def log(**kwargs):
    print ' '.join( "{0}={1}".format(k,v) for k,v in sorted(kwargs.items()) )


@contextmanager
def measure(**kwargs):
    start = time.time()
    status = {'status': 'starting'}
    log(**dict(kwargs.items() + status.items()))
    try:
        yield
    except Exception, e:
        status = {'status': 'err', 'exception': "'{0}'".format(e)}
        log(**dict(kwargs.items() + status.items()))
        raise
    else:
        status = {'status': 'ok', 'duration': time.time() - start}
        log(**dict(kwargs.items() + status.items()))


def count(prefix, key, value, **kwargs):
    key = "count#{0}.{1}".format(prefix, key)
    count = {key: value}
    log(**dict(kwargs.items() + count.items()))


def debug_print(text):
    """Print text if debugging mode is on"""
    if os.environ.get('DEBUG'):
        print text


def validate_env():
    keys = [
        'SEARCH_TERM',
        'METRIC_PREFIX',
        'TW_USERNAME',
        'TW_CONSUMER_KEY',
        'TW_CONSUMER_SECRET',
        'TW_ACCESS_TOKEN',
        'TW_ACCESS_TOKEN_SECRET',
        'DATABASE_URL',
        ]

    # Check for missing env vars
    for key in keys:
        v = os.environ.get(key)
        if not v:
            log(at='validate_env', status='missing', var=key)
            raise ValueError("Missing ENV var: {0}".format(key))

    # Log success
    log(at='validate_env', status='ok')


def main():
    log(at='main')
    main_start = time.time()

    validate_env()

    search_term      = os.environ.get('SEARCH_TERM')
    metric_prefix     = os.environ.get('METRIC_PREFIX')
    #owner_username    = os.environ.get('TW_OWNER_USERNAME')
    username          = os.environ.get('TW_USERNAME')
    consumer_key      = os.environ.get('TW_CONSUMER_KEY')
    consumer_secret   = os.environ.get('TW_CONSUMER_SECRET')
    access_key        = os.environ.get('TW_ACCESS_TOKEN')
    access_secret     = os.environ.get('TW_ACCESS_TOKEN_SECRET')
    database_url      = os.environ.get('DATABASE_URL')

    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["DATABASE_URL"])

    with measure(at='db-connect'):
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port)

    with measure(at='db-init'):
        cursor = conn.cursor()
        try:
          cursor.execute('''
              CREATE TABLE tweets (
                  id bigint CONSTRAINT firstkey PRIMARY KEY,
                  created_at timestamp,
                  text char(180), /* sometimes i find tweets slightly larger than 140chars */
                  author_id bigint,
                  author_screenname char(40)
              );
          ''')
        except psycopg2.ProgrammingError:
            # already exists
            pass
        finally:
            cursor.close()
            conn.commit()

    while True:
        auth = tweepy.OAuthHandler(consumer_key=consumer_key,
            consumer_secret=consumer_secret)
        auth.set_access_token(access_key, access_secret)

        api = tweepy.API(auth_handler=auth, secure=True, retry_count=3)

        with measure(at='search', term=search_term):
            results = api.search(search_term, lang='en')

        for status in results:
            with measure(at='process_status', status_id=status.id):
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO tweets (id, created_at, text, author_id, author_screenname)
                        VALUES (%s, %s, %s, %s, %s)''',
                        (
                            status.id,
                            status.created_at,
                            status.text,
                            status.author.id,
                            status.author.screen_name,
                        )
                    )
                except psycopg2.IntegrityError:
                    # we already saw this tweet
                    pass
                else:
                    count(metric_prefix, 'tweets', 1, status=status.id, author=status.author.id)
                finally:
                    cursor.close()
                    conn.commit()

        log(at='finish', status='ok', duration=time.time() - main_start)
        time.sleep(60)

if __name__ == '__main__':
    # set up rollbar
    rollbar_configured = False
    rollbar_access_key = os.environ.get('ROLLBAR_ACCESS_KEY')
    if rollbar_access_key:
        import rollbar
        rollbar.init(rollbar_access_key, 'production')
        rollbar_configured = True

    while True:
        try:
            main()
        except KeyboardInterrupt:
            log(at='keyboard_interrupt')
            quit()
        except:
            if rollbar_configured:
                rollbar.report_exc_info()
            raise
        time.sleep(10)

