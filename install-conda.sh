#!/bin/bash
validate() {
    grep -F -q -x "$1" <<EOF
raspi11
raspi12
debian10
debian12
EOF
}

if validate $1; then
  cp upgrade-conda.sh ..
  chmod u+x ../upgrade-conda.sh
  sudo apt update
  sudo apt -y upgrade
  sudo apt -y install python3-dev
  sudo apt -y install default-libmysqlclient-dev
  sudo apt -y install build-essential
  sudo apt -y install ffmpeg
  sudo apt -y install libgeos-dev
  sudo apt -y install redis
  sudo apt -y install pkg-config
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
  source ~/miniconda3/etc/profile.d/conda.sh
  conda create --name tf python=3.10
  conda activate tf
  pip install --upgrade pip
  cp requirements.$1 requirements.txt
  pip install -r requirements.txt
  cp ~/cam-ai/camai/passwords.py.example ~/cam-ai/camai/passwords.py
  python setup.py
  python manage.py migrate
else
  echo "Usage: install [OSTYPE]"
  echo "OSTYPE in raspi11, raspi12, debian10, debian12"  
fi  
