#!/bin/bash
validate() {
    grep -F -q -x "$1" <<EOF
raspi11
raspi12
debian10
debian12
debian
EOF
}

if validate $1; then
  rm -rf backup
  mv cam-ai backup
  git clone https://github.com/ludgerh/cam-ai
  cp backup/camai/passwords.py cam-ai/camai/
  mv backup/data cam-ai/data
  cd cam-ai
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
  pip install --upgrade pip
  cp requirements.$1 requirements.txt
  pip install -r requirements.txt
  python manage.py migrate
  cp upgrade-conda.sh ..
  chmod u+x ../upgrade-conda.sh
  cd ..
  echo "Upgrade is done"
else
  echo "Usage: upgrade-conda.sh [OSTYPE]"
  echo "OSTYPE in raspi11, raspi12, debian10, debian12"  
fi  
