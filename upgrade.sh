#!/bin/bash
rm -rf backup
mv cam-ai backup
git clone https://github.com/ludgerh/cam-ai
cp ~/backup/camai/passwords.py ~/cam-ai/camai/
mv ~/backup/env ~/cam-ai/env
mv ~/backup/data ~/cam-ai/data
cd ~/cam-ai
source env/bin/activate
python manage.py migrate
echo done
