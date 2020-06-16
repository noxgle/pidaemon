import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'IuEZvlXZBf1pNCo9folW'
    SIZE_DEAMON_QUEUE = 100
    DB_SQL = 'db.sql'
    PI_TALK_SOCKETFILE='pidaemon.sock'
    PI_TALK_CONNECTION_TIMEOUT = 5
    GPIO_NUMBER_ON_BOARD = 50

    DEV= False
