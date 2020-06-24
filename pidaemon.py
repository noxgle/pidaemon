#!/usr/bin/env python3
# https://www.loggly.com/blog/new-style-daemons-python/
import logging
import sys
import time
import os
import sqlite3
import threading
import schedule
import uuid
import json
import socket
from collections import deque
import subprocess
from datetime import datetime
# from flask import jsonify, request
from app import app

DB_NAME = app.config['DB_SQL']


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        logging.error(f"create_connection: {e}")
    return conn


def gpio_output_to_api(gpio):
    gpio_output = gpio['GPIO'][1]
    for pin in gpio_output:
        val = gpio_output[pin]
    return {'pin': pin, 'val': val}


def gpio_output_from_api(module_name, module_parms, pin, pin_val):
    return {module_name: [module_parms, {pin: pin_val}]}


def get_id_device():
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT value FROM system_info WHERE module_name="general" and name="id_device"')
    rows = cur.fetchall()
    if len(rows) == 1:
        id_device = rows[0][0]
    else:
        id_device = 0
    conn.close()
    return id_device


def get_system_info_id_list():
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM system_info')
    rows = cur.fetchall()
    pin_list = []
    for r in rows:
        pin_list.append(r[0])
    conn.close()
    return pin_list


def get_system_info_id(id):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT * FROM system_info WHERE id=?', (id,))
    rows = cur.fetchall()
    conn.close()
    return rows[0]


def get_system_info(module_name, name):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT value FROM system_info WHERE module_name=? and name=?', (module_name, name))
    rows = cur.fetchall()
    val = rows[0][0]
    conn.close()
    return val


def set_system_info(module_name, name, val):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE system_info SET value = ? WHERE module_name=? and name=?', (val, module_name, name))
    conn.commit()
    conn.close()


def get_pin_info(pin, key):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT * FROM gpio_pin WHERE pin_number=?', (pin,))
    rows = cur.fetchall()
    status = {'id': rows[0][0], 'name': rows[0][1], 'pin_number': rows[0][2], 'pin_conf': rows[0][3],
              'pin_status': rows[0][4], 'enabled': rows[0][5]}
    conn.close()
    if key is False:
        return status
    else:
        try:
            return status[key]
        except Exception as e:
            logging.error(f"get_pin_info: bad key, exception:  {e}")


def get_pin_list():
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT pin_number FROM gpio_pin')
    rows = cur.fetchall()
    pin_list = []
    for r in rows:
        pin_list.append(r[0])
    conn.close()
    return pin_list


def set_pin_status(pin, pin_status):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE gpio_pin SET pin_status = ? WHERE pin_number=?', (pin_status, pin))
    conn.commit()
    conn.close()


def set_pin_enabled(pin, enabled):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE gpio_pin SET enabled = ? WHERE pin_number=?', (enabled, pin))
    conn.commit()
    conn.close()


def set_pin_conf(pin, pin_conf):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE gpio_pin SET pin_conf = ? WHERE pin_number=?', (pin_conf, pin))
    conn.commit()
    conn.close()


def get_gpio_setwarnings():
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT value FROM system_info WHERE module_name="raspberrypi" and name="gpio_setwarnings"')
    rows = cur.fetchall()
    gpio_setwarnings = rows[0][0]
    conn.close()
    return string_to_boolen(gpio_setwarnings)


def get_gpio_setmode():
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT value FROM system_info WHERE module_name="raspberrypi" and name="gpio_setmode"')
    rows = cur.fetchall()
    gpio_setmode = rows[0][0]
    conn.close()
    return gpio_setmode


def get_scheduler_id_list():
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM picron')
    rows = cur.fetchall()
    id_list = []
    for r in rows:
        id_list.append(r[0])
    conn.close()
    return id_list


def get_picron_info(id, key):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT * FROM picron WHERE id=?', (id,))
    rows = cur.fetchall()
    status = {'id': rows[0][0], 'name': rows[0][1], 'schedule_name': rows[0][2], 'schedule_parm': rows[0][3],
              'module_name': rows[0][4], 'module_parm': rows[0][5], 'python_module': rows[0][6], 'enabled': rows[0][7]}
    conn.close()
    if key is False:
        return status
    else:
        try:
            return status[key]
        except Exception as e:
            logging.error(f"get_scheduler_info: bad key, exception:  {e}")


def add_picron_job(name, schedule_name, schedule_parm, module_name, module_parms, python_module, enabled, pin, pin_val):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    if python_module == 1:
        if module_name == 'GPIO':
            # {'GPIO': ['GPIO.output', {pin: output}]}
            # module = {module_name: [module_parms, {pin: pin_val}]}
            module = gpio_output_from_api(module_name, module_parms, pin, pin_val)
            cur.execute('INSERT INTO picron VALUES (null, ?, ?, ?, ?, ?, ?, ?)',
                        (name, schedule_name, schedule_parm, module_name, json.dumps(module), python_module, enabled))
    elif python_module == 0:
        cur.execute('INSERT INTO picron VALUES (null, ?, ?, ?, ?, ?, ?, ?)',
                    (name, schedule_name, schedule_parm, module_name, module_parms, python_module, enabled))

    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_picron_job(id, module_name, val):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    if module_name == 'name':
        cur.execute('UPDATE picron SET name = ? WHERE id=?', (val, id))
    elif module_name == 'schedule_name':
        cur.execute('UPDATE picron SET schedule_name = ? WHERE id=?', (val, id))
    elif module_name == 'schedule_parm':
        cur.execute('UPDATE picron SET schedule_parm = ? WHERE id=?', (val, id))
    elif module_name == 'module_name':
        cur.execute('UPDATE picron SET module_name = ? WHERE id=?', (val, id))
    elif module_name == 'module_parms':
        cur.execute('UPDATE picron SET module_parms = ? WHERE id=?', (val, id))
    elif module_name == 'python_module':
        cur.execute('UPDATE picron SET python_module = ? WHERE id=?', (val, id))
    elif module_name == 'enabled':
        cur.execute('UPDATE picron SET enabled = ? WHERE id=?', (val, id))
    conn.commit()
    conn.close()


def del_picron_job(id):
    conn = create_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute('DELETE FROM picron WHERE id=?', (id,))
    conn.commit()
    conn.close()


def string_to_boolen(string):
    if string == 'Fasle':
        return False
    elif string == 'True':
        return True


def return_time_status():
    # timedatectl show --property=NTPSynchronized --value
    status = subprocess.getoutput('/usr/bin/timedatectl show --property=NTPSynchronized --value')
    if status == 'yes':
        logging.info(f"return_time_status: System time is synchronized")
        return True
    else:
        logging.warning(f"return_time_status: System time is not synchronized")
        return False


def pideamon_talk(cmd):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(app.config['PI_TALK_SOCKETFILE'])
        s.settimeout(1)
        # data=json.dumps([id, 'PIDEAMON', {'GPIO':['GPIO.setup',{'24':'GPIO.OUT'}]}])
        data = json.dumps(cmd)
        bytes_data = data.encode()
        s.send(bytes_data)
        try:
            msg = json.loads(s.recv(1024))
            if msg[0] == 'OK':
                return True
            else:
                return False
        except ValueError as e:
            logging.warning(f"pideamon_talk: received data is not json, {e}")
    except IOError as e:
        print(f'Cant connect {e}')
    finally:
        s.close()


# class
class MDeamon():

    def __init__(self):

        self.size_deamon_queue = app.config['SIZE_DEAMON_QUEUE']
        self.socketfile = app.config['PI_TALK_SOCKETFILE']
        self.connectionTimeout = app.config['PI_TALK_CONNECTION_TIMEOUT']

        self.dbname = app.config['DB_SQL']

        if not os.path.exists(self.dbname):
            FirstRun(DB_NAME)

        self.id_device = get_id_device()

        self.PCQ = PiCronQueue(self.size_deamon_queue)
        self.PDQ = PiDeamonQueue(self.size_deamon_queue)

    def start(self):
        while True:
            try:
                if PD.is_alive() is False:
                    PD = PiDeamon(self.PCQ, self.PDQ, self.dbname)
                    PD.start()
            except Exception as e:
                PD = PiDeamon(self.PCQ, self.PDQ, self.dbname)
                PD.start()
            time.sleep(1)
            try:
                if PC.is_alive() is False:
                    PC = PiCron(self.PCQ, self.PDQ, self.dbname)
                    PC.start()
            except Exception as e:
                PC = PiCron(self.PCQ, self.PDQ, self.dbname)
                PC.start()
            time.sleep(1)
            try:
                if PT.is_alive() is False:
                    PT = PiTalk(self.PCQ, self.PDQ, self.socketfile, self.connectionTimeout, self.id_device)
                    PT.start()
            except Exception as e:
                PT = PiTalk(self.PCQ, self.PDQ, self.socketfile, self.connectionTimeout, self.id_device)
                PT.start()

            time.sleep(10)


class FirstRun:
    def __init__(self, dbname):
        logging.info(f"FirstRun: initiate {dbname}")
        conn = create_connection(dbname)
        self.c = conn.cursor()
        self.create_db()
        self.save_first_run()
        conn.commit()
        conn.close()

    def create_db(self):
        self.c.execute(
            '''CREATE TABLE system_info (id integer primary key AUTOINCREMENT, module_name text, name text, value text)''')
        self.c.execute(
            '''CREATE TABLE picron (id integer primary key AUTOINCREMENT, name text, schedule_name text, schedule_parm text, module_name text, module_parms text, python_module integer, enabled integer)''')
        self.c.execute(
            '''CREATE TABLE gpio_pin (id integer primary key AUTOINCREMENT, name text, pin_number integer, pin_conf text, pin_status text, enabled integer)''')

    def save_first_run(self):
        si = {'first_run_time': time.time(), 'id': uuid.uuid4()}
        with open('id.txt', 'w') as file:  # Use file to refer to the file object
            file.write(f'{si["id"]}')
        logging.info(f"FirstRun: first run piDeamon: {si['first_run_time']}")
        logging.info(f"FirstRun: id device: {si['id']}")
        self.c.execute(f"INSERT INTO system_info VALUES (null, 'general', 'first_run', '{si['first_run_time']}')")
        self.c.execute(f"INSERT INTO system_info VALUES (null, 'general', 'id_device', '{si['id']}')")
        self.c.execute(f"INSERT INTO system_info VALUES (null, 'system', 'wait_for_ntp_sync', 'True')")
        self.c.execute(f"INSERT INTO system_info VALUES (null, 'raspberrypi', 'is_configured', 'True')")
        self.c.execute(f"INSERT INTO system_info VALUES (null, 'raspberrypi', 'gpio_setwarnings', 'True')")
        self.c.execute(f"INSERT INTO system_info VALUES (null, 'raspberrypi', 'gpio_setmode', 'board')")

        gpio_number_on_board = int(app.config['GPIO_NUMBER_ON_BOARD'])
        for i in range(1, (gpio_number_on_board + 1)):
            self.c.execute("INSERT INTO gpio_pin VALUES (null, 'Example name', ?, '', '',0)", (i,))


class PiTalk(threading.Thread):

    def __init__(self, PCQ, PDQ, socketfile, connectionTimeout, id_device):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.socketfile = socketfile
        self.connectionTimeout = connectionTimeout
        self.id_device = id_device
        self.PCQ = PCQ
        self.PDQ = PDQ
        if os.path.exists(self.socketfile):
            os.remove(self.socketfile)

    def run(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(self.socketfile)
        s.listen(5)

        logging.info(f'PiTalk: server socket is ready and waiting for connections..')
        while True:
            client, ipPort = s.accept()
            client.settimeout(int(self.connectionTimeout))
            try:
                data = json.loads(client.recv(1024).decode())
                logging.info(f'PiTalk: received data: {data}')
                if data[0] == self.id_device:
                    try:
                        if data[1] == 'PICRON':
                            order = data[2]
                            self.PCQ.add(order)
                        elif data[1] == 'PIDEAMON':
                            order = data[2]
                            self.PDQ.add(order)
                    except Exception as e:
                        logging.warning(f'PiTalk: bad data, exception: {e}')
                    try:
                        client.send(json.dumps(['OK']).encode())
                    except Exception as e:
                        logging.warning(f'PiTalk: connection end without bye, exception: {e}')
                else:
                    logging.warning(f'PiTalk: bad id_device')
                    try:
                        client.send(json.dumps(['BADCOMMAND']).encode())
                    except Exception as e:
                        logging.warning(f'PiTalk: connection end without bye, exception: {e}')
            except ValueError as e:
                logging.warning(f'PiTalk: received data is not json, exception: {e}')
            except socket.timeout as e:
                logging.warning(f'PiTalk: connection timeout, exception: {e}')
            finally:
                client.close()


class PiCronQueue:

    def __init__(self, size):
        self.cmd_queue = deque([])
        self.lock = threading.Lock()
        self.size = size

    def get(self):
        if len(self.cmd_queue) > 0:
            self.lock.acquire()
            try:
                order = self.cmd_queue.popleft()
            finally:
                self.lock.release()
            return order
        else:
            return None

    def add(self, order):
        if len(self.cmd_queue) < self.size:
            self.lock.acquire()
            try:
                self.cmd_queue.append(order)
            finally:
                self.lock.release()


class PiCron(threading.Thread):
    def __init__(self, PCQ, PDQ, dbname):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.PCQ = PCQ
        self.PDQ = PDQ
        self.dbname = dbname

    def setJobs(self):
        logging.info("PiCron: create new cron list")
        schedule.clear()
        conn = create_connection(self.dbname)
        cur = conn.cursor()
        cur.execute("SELECT * FROM picron WHERE enabled=1")

        rows = cur.fetchall()

        for row in rows:
            id = row[0]
            name = row[1]
            schedule_name = row[2]
            schedule_parm = row[3]
            module_name = row[4]
            module_parm = row[5]
            python_module = row[6]

            if schedule_name == 'seconds':
                schedule.every(int(schedule_parm)).seconds.do(self.job, module_name, module_parm, python_module)
            elif schedule_name == 'second.at':
                schedule.every().second.at(schedule_parm).do(self.job, module_name, module_parm, python_module)

            elif schedule_name == 'minutes':
                schedule.every(int(schedule_parm)).minutes.do(self.job, module_name, module_parm, python_module)
            elif schedule_name == 'minute.at':
                schedule.every().minute.at(schedule_parm).do(self.job, module_name, module_parm, python_module)

            elif schedule_name == 'hours':
                schedule.every(int(schedule_parm)).hours.do(self.job, module_name, module_parm, python_module)
            elif schedule_name == 'hour.at':
                schedule.every().hour.at(schedule_parm).do(self.job, module_name, module_parm, python_module)

            elif schedule_name == 'days':
                schedule.every(int(schedule_parm)).days.do(self.job, module_name, module_parm, python_module)
            elif schedule_name == 'day.at':
                schedule.every().day.at(schedule_parm).do(self.job, module_name, module_parm, python_module)

        conn.close()

    def job(self, module_name, module_parm, python_module):
        if python_module == 1:
            if module_name == 'GPIO':
                self.PDQ.add(json.loads(module_parm))
        elif python_module == 0:
            if os.path.exists(module_name):
                if module_parm == '':
                    try:
                        status = subprocess.call(module_name, shell=True)
                        logging.info(f'PiCron: script: {module_name}, module parm: {module_parm}, status: {status}')
                    except Exception as e:
                        logging.warning(f'PiCron: script: {module_name}, module parm: {module_parm}, exception: {e}')
                else:
                    try:
                        status = subprocess.call(f'{module_name} {module_parm}', shell=True)
                        logging.info(f'PiCron: script: {module_name}, module parm: {module_parm}, status: {status}')
                    except Exception as e:
                        logging.warning(f'PiCron: script: {module_name}, module parm: {module_parm}, exception: {e}')
            else:
                logging.warning(f"PiCron: script: {module_name} don't exist")

    def run(self):
        if app.config['DEV'] is False:
            if string_to_boolen(get_system_info('system', 'wait_for_ntp_sync')) is True:
                logging.info("PiCron: server is waiting for time synchronization ..")
                while True:
                    if return_time_status():
                        break
                    time.sleep(60)
        logging.info("PiCron: server is ready and running..")
        self.setJobs()
        while True:
            schedule.run_pending()
            cmd = self.PCQ.get()
            if cmd is not None:
                logging.info(f"PiCron: commands: {cmd}")
                for key in list(cmd):
                    if key == 'PICRON':
                        if cmd[key][0] == 'RESTART':
                            logging.info("PiCron: restart")
                            sys.exit()
                        elif cmd[key][0] == 'LOCAL_SYNC':
                            self.setJobs()
            else:
                time.sleep(1)


class PiDeamonQueue(PiCronQueue):
    def __init__(self, size):
        self.cmd_queue = deque([])
        self.lock = threading.Lock()
        self.size = size


class PiDeamon(threading.Thread):
    def __init__(self, PCQ, PGD, dbname):
        threading.Thread.__init__(self)
        self.dbname = dbname
        self.PG = PiGpio(self.dbname)
        self.PGD = PGD
        self.PCQ = PCQ

        self.setDaemon(True)

    def run(self):
        logging.info("PiDeamon: server is ready and running..")
        while True:
            commands = self.PGD.get()
            if commands is not None:
                logging.info(f"PiDeamon: commands: {commands}")
                for key in list(commands):
                    if key == 'PIDEAMON':
                        if commands['PIDEAMON'][0] == 'RESTART':
                            logging.info("PiDeamon: restart")
                            sys.exit()
                        elif commands['PIDEAMON'][0] == 'PIREBOOT':
                            logging.info("PiDeamon: rebooting PI")
                            subprocess.call('/sbin/reboot', shell=True)
                    elif key == 'GPIO':
                        self.PG.gpio_job(commands['GPIO'])
            else:
                time.sleep(0.1)


class PiGpio:
    def __init__(self, dbname):
        self.dbname = dbname
        if app.config['DEV'] is False:
            if string_to_boolen(get_system_info('raspberrypi', 'is_configured')) is True:
                self.reset()
                self.set_conf()
                self.load_pin_conf_from_db()
                self.load_pin_status_from_db()

    def set_conf(self):
        if get_gpio_setwarnings():
            GPIO.setwarnings(True)
        else:
            GPIO.setwarnings(False)
        setmode = get_gpio_setmode()
        logging.info(f"PiGpio: setting setmode: {setmode}")
        if setmode == 'board':
            try:
                GPIO.setmode(GPIO.BOARD)
            except Exception as e:
                logging.info(f"PiGpio: {e}")
        elif setmode == 'bcm':
            try:
                GPIO.setmode(GPIO.BCM)
            except Exception as e:
                logging.info(f"PiGpio: {e}")

    def reset(self):
        GPIO.cleanup()

    def load_pin_status_from_db(self):
        conn = create_connection(self.dbname)
        cur = conn.cursor()
        cur.execute('SELECT pin_number, pin_status FROM gpio_pin WHERE enabled=1 and pin_conf="GPIO.OUT"')
        rows = cur.fetchall()
        for r in rows:
            pin_number = r[0]
            pin_status = r[1]
            if pin_status == '1' or pin_status == '0':
                cmd = ['GPIO.output', {pin_number: int(pin_status)}]
                self.gpio_job(cmd, sync_db=False)
        conn.close()

    def load_pin_conf_from_db(self):
        conn = create_connection(self.dbname)
        cur = conn.cursor()
        cur.execute('SELECT pin_number, pin_conf FROM gpio_pin WHERE enabled=1')
        rows = cur.fetchall()
        for r in rows:
            pin_number = r[0]
            pin_conf = r[1]
            cmd = ['GPIO.setup', {pin_number: pin_conf}]
            self.gpio_job(cmd, sync_db=False)
        conn.close()

    def gpio_job(self, job, sync_db=True):
        logging.info(f"PiGpio: setting gpio: {job}")
        if app.config['DEV'] is False:
            if string_to_boolen(get_system_info('raspberrypi', 'is_configured')) is True:
                command = job[0]
                command_val = job[1]
                for pin in list(command_val.keys()):
                    pin_val = command_val[pin]
                    pin_int = int(pin)
                    enabled = get_pin_info(pin_int, 'enabled')
                    if enabled == 1:
                        if command == 'GPIO.setup':
                            if pin_val == 'GPIO.OUT':
                                try:
                                    GPIO.setup(pin_int, GPIO.OUT, initial=GPIO.HIGH)
                                    GPIO.setup(pin_int, GPIO.OUT)
                                except Exception as e:
                                    logging.error(f"PiGpio: setup exception: {e}")
                                    return False
                                else:
                                    if sync_db:
                                        set_pin_conf(pin_int, 'GPIO.OUT')
                            elif pin_val == 'GPIO.IN':
                                try:
                                    GPIO.setup(pin_int, GPIO.IN)
                                except Exception as e:
                                    logging.error(f"PiGpio: setup exception: {e}")
                                    return False
                                else:
                                    if sync_db:
                                        set_pin_conf(pin_int, 'GPIO.IN')
                        elif command == 'GPIO.output':
                            try:
                                GPIO.output(pin_int, pin_val)
                            except Exception as e:
                                logging.error(f"PiGpio: output exception: {e}")
                                return False
                            else:
                                if sync_db:
                                    set_pin_status(pin_int, pin_val)
                        elif command == 'GPIO.input':
                            try:
                                input_status = GPIO.input(pin_int)
                            except Exception as e:
                                logging.error(f"PiGpio: input exception: {e}")
                                return False
                            else:
                                if sync_db:
                                    set_pin_status(pin_int, input_status)
                    else:
                        logging.warning(f"PiGpio: pin {pin} is disabled")


class SystemdHandler(logging.Handler):
    # https://www.loggly.com/blog/new-style-daemons-python/
    PREFIX = {
        # EMERG <0>
        # ALERT <1>
        logging.CRITICAL: "<2>",
        logging.ERROR: "<3>",
        logging.WARNING: "<4>",
        # NOTICE <5>
        logging.INFO: "<6>",
        logging.DEBUG: "<7>",
        logging.NOTSET: "<7>"
    }

    def __init__(self, stream=sys.stdout):
        self.stream = stream
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            msg = self.PREFIX[record.levelno] + self.format(record)
            msg = msg.replace("\n", "\\n")
            self.stream.write(msg + "\n")
            self.stream.flush()
        except Exception:
            self.handleError(record)


if __name__ == '__main__':
    if app.config['DEV'] is False:
        import RPi.GPIO as GPIO

    root_logger = logging.getLogger()
    root_logger.setLevel("INFO")
    root_logger.addHandler(SystemdHandler())

    MD = MDeamon()
    MD.start()
