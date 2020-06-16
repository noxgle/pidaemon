#!/bin/bash
# 
# Script start in project folder.

systemctl stop pidaemon
systemctl disable pidaemon
rm /etc/systemd/system/pidaemon.service
rm /etc/systemd/system/pidaemon.service
rm /usr/lib/systemd/system/pidaemon.service
rm /usr/lib/systemd/system/pidaemon.service
systemctl daemon-reload
systemctl reset-failed

systemctl stop api_pidaemon
systemctl disable api_pidaemon
rm /etc/systemd/system/api_pidaemon.service
rm /etc/systemd/system/api_pidaemon.service
rm /usr/lib/systemd/system/api_pidaemon.service
rm /usr/lib/systemd/system/api_pidaemon.service
systemctl daemon-reload
systemctl reset-failed
