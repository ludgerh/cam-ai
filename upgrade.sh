#!/bin/bash
validate() {
    grep -F -q -x "$1" <<EOF
raspi11
debian10
debian12
EOF
}

if validate $1; then
  rm -rf backup
  mv cam-ai backup
  git clone https://github.com/ludgerh/cam-ai
  cp backup/camai/passwords.py cam-ai/camai/
  mv backup/env cam-ai/env
  mv backup/data cam-ai/data
  cd cam-ai
  source env/bin/activate
  pip install --upgrade pip
  cp requirements.$1 requirements.txt
  pip install -r requirements.txt
  python manage.py migrate
  cp upgrade.sh ..
  chmod u+x ../upgrade.sh
  cd ..
  echo Upgrade is done
else
  echo "Usage: upgrade [OSTYPE]"
  echo "OSTYPE in raspi11, debian10, debian12"  
fi  
