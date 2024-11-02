#!/bin/bash
# Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
# More information and complete source: https://github.com/ludgerh/cam-ai
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

validate() {
    grep -F -q -x "$1" <<EOF
raspi_4_12
raspi-5-12
debian_12
EOF
}

if validate $1; then
  rm -rf backup
  read -p "Press enter to continue"
  mv cam-ai backup
  read -p "Press enter to continue"
  git clone https://github.com/ludgerh/cam-ai
  read -p "Press enter to continue"
  mv backup/camai/passwords.py cam-ai/camai/
  mv backup/plugins/ cam-ai/plugins
  mv backup/data/ cam-ai/data
  mv backup/accounts/templates/django_registration/privacy.html cam-ai/accounts/templates/django_registration/
  mv backup/accounts/templates/django_registration/terms.html cam-ai/accounts/templates/django_registration/
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
  echo "OSTYPE in raspi_4_12, raspi-5-12, debian_12"  
fi  
