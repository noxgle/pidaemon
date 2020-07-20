import requests

URL = 'http://127.0.0.1:5080'

with open("id.txt", encoding='utf-8') as f:
    ID = f.read()

req = requests.get(url=f'{URL}/api/{ID}/system/info')
id_system = req.json()
print('Table system_info:')
for i in id_system:
    req = requests.get(url=f'{URL}/api/{ID}/system/info/{i}')
    print(req.json())

req = requests.get(url=f'{URL}/api/{ID}/gpio')
gpio = req.json()
print('Table gpio_pin:')
for g in gpio:
    req = requests.get(url=f'{URL}/api/{ID}/gpio/{g}')
    print(req.json())

req = requests.get(url=f'{URL}/api/{ID}/scheduler')
scheduler = req.json()
print('Table picron:')
for s in scheduler:
    req = requests.get(url=f'{URL}/api/{ID}/scheduler/{s}')
    print(req.json())
