#!/bin/bash
cp upgrade.sh ..
chmod u+x ../upgrade.sh
sudo apt update
sudo apt -y upgrade
sudo apt -y install python3-dev
sudo apt -y install python3-venv
sudo apt -y install default-libmysqlclient-dev
sudo apt -y install build-essential
sudo apt -y install ffmpeg
sudo apt -y install libgeos-dev
sudo apt -y install redis
echo "#***** CAM-AI setting" | sudo tee -a /etc/dhcp/dhclient.conf
echo "timeout 180;" | sudo tee -a /etc/dhcp/dhclient.conf
echo "#***** CAM-AI setting" | sudo tee -a /etc/sysctl.conf
echo "vm.overcommit_memory = 1" | sudo tee -a /etc/sysctl.conf
echo "net.core.somaxconn=1024" | sudo tee -a /etc/sysctl.conf
sudo sed -i '/^save/d' /etc/redis/redis.conf
echo "#***** CAM-AI disabled saving" | sudo tee -a /etc/redis/redis.conf
echo "#save 900 1" | sudo tee -a /etc/redis/redis.conf
echo "#save 300 10" | sudo tee -a /etc/redis/redis.conf
echo "#save 60 10000" | sudo tee -a /etc/redis/redis.conf
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp ~/cam-ai/camai/passwords.py.example ~/cam-ai/camai/passwords.py
python setup.py
python manage.py migrate

