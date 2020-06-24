from pidaemon import *
from flask import jsonify, request


# API
# https://restfulapi.net/http-methods/
# ['ab248654-c56c-4af6-a825-e8be026ef549', 'PIDEAMON', {'GPIO': ['GPIO.setup', {'24': 'GPIO.OUT'}]}]
# /api/ab248654-c56c-4af6-a825-e8be026ef549/pideamon/gpio/setup/24/out
# /api/apikey/thread/module/seting1/pin/seting2
# http://127.0.0.1:5000/api/78be65df-a7a1-4aef-8691-70cf749efc85/gpio/GPIO.setup/24/GPIO.OUT

def return_api(data, status):
    resp = jsonify(data)
    resp.status_code = status
    return resp

@app.route('/api/<id_device>/system/piinfo', methods=['GET'])
def get_raspberrypi_info(id_device):
    if get_id_device() == id_device:
        cpuinfo = subprocess.getoutput('/bin/cat /proc/cpuinfo')
        return return_api({'cpuinfo': cpuinfo}, 200)
    logging.warning(f"Api: get_raspberrypi_info: bad id_device {id_device}")
    return return_api('Bad id device', 404)

@app.route('/api/<id_device>/system/time', methods=['GET'])
def api_system_info_time(id_device):
    if get_id_device() == id_device:
        time_sync = return_time_status()
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        return return_api({'time_sync': time_sync, 'time': dt_string}, 200)
    else:
        logging.warning(f"Api: api_system_info_time: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/system/info', methods=['GET'])
def api_system_info_id_list(id_device):
    if get_id_device() == id_device:
        return return_api(get_system_info_id_list(), 200)
    else:
        logging.warning(f"Api: api_system_info_id_list: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/system/info/<int:id>', methods=['GET'])
def api_system_info_id(id_device, id):
    if get_id_device() == id_device:
        return return_api(get_system_info_id(id), 200)
    else:
        logging.warning(f"Api: api_system_info_id: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio', methods=['GET'])
def api_gpio_pin_list(id_device):
    if get_id_device() == id_device:
        return return_api(get_pin_list(), 200)
    else:
        logging.warning(f"Api: api_gpio_pin_number: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/<int:pin>', methods=['GET'])
def api_gpio_pin_info(id_device, pin):
    if get_id_device() == id_device:
        pin_info = get_pin_info(pin, False)
        logging.info(f"Api: api_gpio: pin_info: {pin}")
        return return_api(pin_info, 200)
    else:
        logging.warning(f"Api: api_gpio_input: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/setup', methods=['PUT'])
def api_gpio_setup(id_device):
    if get_id_device() == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                pin = data['pin']
                pin_set = data['setup']
            except Exception as e:
                return return_api('Bad name pin or', 404)
            else:
                if get_pin_info(pin, 'enabled') == 1:
                    # ([id, 'PIDEAMON', {'GPIO':['GPIO.setup',{'24':'GPIO.OUT'}]}])
                    cmd = [id_device, 'PIDEAMON', {'GPIO': ['GPIO.setup', {pin: pin_set}]}]
                    msg = pideamon_talk(cmd)
                    if msg:
                        return return_api('OK', 200)
                    else:
                        return return_api(f'Incorrect commands', 404)
                else:
                    return return_api(f'Pin {pin} is disabled, enable first', 404)
    else:
        logging.warning(f"Api: api_gpio_setup: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/output', methods=['PUT'])
def api_gpio_output(id_device):
    if get_id_device() == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                pin = data['pin']
                output = data['output']
            except Exception as e:
                return return_api('Bad name pin or', 404)
            else:
                if get_pin_info(pin, 'enabled') == 1:
                    cmd = [id_device, 'PIDEAMON', {'GPIO': ['GPIO.output', {pin: output}]}]
                    msg = pideamon_talk(cmd)
                    if msg:
                        return return_api('OK', 200)
                    else:
                        return return_api(f'Incorrect commands', 404)
                else:
                    return return_api(f'Pin {pin} is disabled, enable first', 404)
    else:
        logging.warning(f"Api: api_gpio_output: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/input/<int:pin>', methods=['GET'])
def api_gpio_input(id_device, pin):
    if get_id_device() == id_device:
        pin_status = get_pin_info(pin, 'pin_status')
        logging.info(f"Api: api_gpio_input: pin_status {pin_status}")
        return return_api(pin_status, 200)
    else:
        logging.warning(f"Api: api_gpio_input: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/enable/<int:pin>', methods=['PUT'])
def api_gpio_enable(id_device, pin):
    if get_id_device() == id_device:
        set_pin_enabled(pin, 1)
        return return_api('OK', 200)
    else:
        logging.warning(f"Api: api_gpio_enable: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/disable/<int:pin>', methods=['PUT'])
def api_gpio_disable(id_device, pin):
    if get_id_device() == id_device:
        set_pin_enabled(pin, 0)
        return return_api('OK', 200)
    else:
        logging.warning(f"Api: api_gpio_enable: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler', methods=['GET'])
def api_scheduler_list(id_device):
    if get_id_device() == id_device:
        return return_api(get_scheduler_id_list(), 200)
    else:
        logging.warning(f"Api: api_scheduler_list: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/<int:id>', methods=['GET'])
def api_scheduler_id(id_device, id):
    if get_id_device() == id_device:
        job_info = get_picron_info(id, False)
        module_parm=job_info['module_parm']
        gpio_output=gpio_output_to_api(module_parm)
        job_info['pin']=gpio_output['pin']
        job_info['val'] = gpio_output['val']
        del job_info['module_parm']
        logging.info(f"Api: api_scheduler_id: {job_info}")
        return return_api(job_info, 200)
    else:
        logging.warning(f"Api: api_scheduler_id: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/gpio/add', methods=['POST'])
def api_scheduler_gpio_add(id_device):
    if get_id_device() == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                name = data['name']
                schedule_name = data['schedule_name']
                schedule_parm = data['schedule_parm']
                module_name = data['module_name']
                module_parms = data['module_parms']
                python_module = 1
                enabled = data['enabled']
                pin = data['pin']
                pin_val = data['pin_val']
            except Exception as e:
                return return_api('Bad json data', 404)
            else:
                new_id = add_picron_job(name, schedule_name, schedule_parm, module_name, module_parms, python_module,
                                        enabled, pin, pin_val)

                cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
                msg = pideamon_talk(cmd)
                if msg:
                    return return_api('OK', 200)
                else:
                    return return_api(f'Incorrect commands', 404)
    else:
        logging.warning(f"Api: api_scheduler_gpio_add: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/script/add', methods=['POST'])
def api_scheduler_script_add(id_device):
    if get_id_device() == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                name = data['name']
                schedule_name = data['schedule_name']
                schedule_parm = data['schedule_parm']
                module_name = data['module_name']
                module_parms = data['module_parms']
                python_module = data['python_module']
                enabled = data['enabled']
            except Exception as e:
                return return_api('Bad json data', 404)
            else:
                new_id = add_picron_job(name, schedule_name, schedule_parm, module_name, module_parms, python_module,
                                        enabled)

                cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
                msg = pideamon_talk(cmd)
                if msg:
                    return return_api('OK', 200)
                else:
                    return return_api(f'Incorrect commands', 404)
    else:
        logging.warning(f"Api: api_gpio_output: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/update/<int:id>', methods=['PUT'])
def api_scheduler_update(id_device, id):
    if get_id_device() == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            for key in list(data):
                if key == 'name':
                    update_picron_job(id, key, data[key])
                elif key == 'schedule_name':
                    update_picron_job(id, key, data[key])
                elif key == 'schedule_parm':
                    update_picron_job(id, key, data[key])
                elif key == 'enabled':
                    update_picron_job(id, key, data[key])
            cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
            msg = pideamon_talk(cmd)
            if msg:
                return return_api('OK', 200)
            else:
                return return_api(f'Incorrect commands', 404)
    else:
        logging.warning(f"Api: api_scheduler_update: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/delete/<int:id>', methods=['DELETE'])
def api_scheduler_delete(id_device, id):
    if get_id_device() == id_device:
        del_picron_job(id)
        logging.info(f"Api: api_scheduler_delete: {id}")
        cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
        msg = pideamon_talk(cmd)
        if msg:
            return return_api('OK', 200)
        else:
            return return_api(f'Incorrect commands', 404)
    else:
        logging.warning(f"Api: api_scheduler_delete: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/<daemon>', methods=['PUT'])
def api_deamon(id_device, daemon):
    if get_id_device() == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            daemon=daemon.upper()
            if daemon in data:
                if daemon == 'PICRON':
                    if data[daemon] == 'RESTART':
                        cmd = [id_device, 'PICRON', {'PICRON': ['RESTART']}]
                        msg = pideamon_talk(cmd)
                        if msg:
                            return return_api('OK', 200)
                        else:
                            return return_api(f'Incorrect commands', 404)

                    elif data[daemon] == 'LOCAL_SYNC':
                        cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
                        msg = pideamon_talk(cmd)
                        if msg:
                            return return_api('OK', 200)
                        else:
                            return return_api(f'Incorrect commands', 404)
                elif daemon == 'PIDEAMON':
                    if data[daemon] == 'RESTART':
                        cmd = [id_device, 'PIDEAMON', {'PIDEAMON': ['RESTART']}]
                        msg = pideamon_talk(cmd)
                        if msg:
                            return return_api('OK', 200)
                        else:
                            return return_api(f'Incorrect commands', 404)

                    elif data[daemon] == 'PIREBOOT':
                        cmd = [id_device, 'PIDEAMON', {'PIDEAMON': ['PIREBOOT']}]
                        msg = pideamon_talk(cmd)
                        if msg:
                            return return_api('OK', 200)
                        else:
                            return return_api(f'Incorrect commands', 404)
                else:
                    return return_api(f'Incorrect daemon, {daemon}', 404)
            else:
                return return_api(f'Key {daemon} not found in data', 404)
    else:
        logging.warning(f"Api: api_deamon: bad id_device {id_device}")
        return return_api('Bad id device', 404)

    return return_api('Bad command', 404)


#if __name__ == '__main__':
#    app.run(debug=False, host='0.0.0.0')
