#!/bin/bash
validate() {
    grep -F -q -x "$1" <<EOF
raspi11
debian10
debian12
EOF
}

if validate $1; then
  echo "valid"
else
  echo "Usage: upgrade [OSTYPE]"
  echo "OSTYPE in raspi11, debian10, debian12"  
fi  

