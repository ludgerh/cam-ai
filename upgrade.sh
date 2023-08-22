#!/bin/bash
mv cam-ai backup
git clone https://github.com/ludgerh/cam-ai
cp backup/camai/passwords.py cam-ai/camai/
mv backup/env cam-ai/env
mv backup/data cam-ai/data
rm -rf backup
if [ $1 = "copy" ]; then
  cp cam-ai/upgrade.sh ./
  echo Copy is done
else
  cd cam-ai
  source env/bin/activate
  pip install --upgrade pip
  cp requirements.$1 requirements.txt
  pip install -r requirements.txt
  python manage.py migrate
  cd ..
  echo Upgrade is done
fi  
