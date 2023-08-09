#!/bin/bash -
sudo yum -y update
sudo yum -y install python3
sudo yum -y install python3-pip

sudo pip3 install -U boto3
sudo pip3 install csvkit
sudo pip3 install mimesis==4.1.3
sudo pip3 install pandas