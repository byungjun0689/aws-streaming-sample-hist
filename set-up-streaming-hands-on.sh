#!/bin/bash -

OS_NAME=$(cat /etc/os-release | awk -F "=" '$1 == "NAME" { print $2 }')
if [[ z"${OS_NAME}" == z"\"Amazon Linux AMI\"" ]];
then
  sudo yum -y update
  sudo yum -y install python39
  sudo yum -y install python3-pip

  sudo pip-3.9 install -U boto3
  sudo pip-3.9 install csvkit
  sudo pip-3.9 install mimesis==4.1.3
  sudo pip3 install pandas
elif [[ z"${OS_NAME}" == z"\"Amazon Linux\"" ]];
then
  sudo yum -y update
  sudo yum -y install python3
  sudo yum -y install python3-pip

  sudo pip3 install -U boto3
  sudo pip3 install csvkit
  sudo pip3 install mimesis==4.1.3
  sudo pip3 install pandas
elif [[ z"${OS_NAME}" == z"\"Ubuntu\"" ]];
then
  sudo apt-get -y update
  sudo apt-get -y install python3.9
  sudo apt-get -y install python3-pip

  sudo pip3 install -U boto3
  sudo pip3 install csvkit
  sudo pip3 install mimesis==4.1.3
  sudo pip3 install pandas
else
  echo "[Unknown OS] You should install python3.6+, pip3+ for yourself!"
  exit 0
fi