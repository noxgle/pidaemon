#!/bin/bash
# 
# Script start in project folder.

cp pidaemon.service /etc/systemd/system/
systemctl start pidaemon
systemctl enable pidaemon


cp api_pidaemon.nginx /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/api_pidaemon.nginx /etc/nginx/sites-enabled/
cp api_pidaemon.service /etc/systemd/system/
systemctl restart nginx
systemctl start api_pidaemon
systemctl enable api_pidaemon

systemctl status pidaemon
systemctl status api_pidaemon