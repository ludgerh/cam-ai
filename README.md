# CAM-AI Server

#### CAM-AI reads security cameras and adds artificial intelligence: No more false alarms!

This is an installation tutorial for a development system of the CAM-AI Server on a Raspberry Pi 4 and Debian 11 (bullseye) 64bit (get it at https://raspi.debian.net/tested-images/ , and install it on your Raspberry Pi). Other configurations are probably possible, but might need some testing and modifications. Raspberry Pi OS does not work. Raspi 3 does not work. Here we go:

1. ####  Initial customizing of Raspi

   On a fresh installation you first need to a root password, initially thats empty. You log in as root and continue like this:

   `passwd root`

   Then you might want to set the Raspi to the korrekt keyboard layout:

   `apt update`

   `apt upgrade`

   `apt install keyboard-configuration`

   `apt install console-setup`

   `apt install locales`

   `dpkg-reconfigure tzdata`

   `apt install systemd-cron`

   It is recommended to create a special user for operating the camera server. In our example this users name will be cam_ai :

   **If the sudo-utility is not yet installed** on your target system, you can install it by doing:

   `apt install sudo`

   Then you continue:

   `adduser cam_ai`

   You will be asked for all kind of information for the new user. The only thing you need to provide is a valid password (2 times), you can skip the rest by hitting return a couple of times. 

   `usermod -aG sudo cam_ai`

   `exit`

   **Then you login on a new console with the new users credential, either local or remote.**

   There is one setting in the DHCP-configuration that causes proplems. We need to fix that:

   `sudo nano /etc/dhcp/dhclient.conf`

   Next you find the line 
   `#timeout 60;`

   and replace it with

   `timeout 180;`

   Following the rcommendations of the Redis logfile I did some more finetuning:

   `sudo nano /etc/sysctl.conf`

   Add at the bottom of this file:

   `vm.overcommit_memory = 1`

   `net.core.somaxconn=1024`

   Save and leave Nano. Create the file

   `sudo nano /etc/systemd/system/disable-transparent-huge-pages.service`

   and put this in:

   `[Unit]`
   `Description=Disable Transparent Huge Pages`

   `[Service]`
   `Type=oneshot`
   `ExecStart=/bin/sh -c "/usr/bin/echo "never" | tee /sys/kernel/mm/transparent_hugepage/enabled"`
   `ExecStart=/bin/sh -c "/usr/bin/echo "never" | tee /sys/kernel/mm/transparent_hugepage/defrag"`

   `[Install]`
   `WantedBy=multi-user.target`

   Then enable the service:

   `sudo systemctl enable disable-transparent-huge-pages`
   `sudo systemctl start disable-transparent-huge-pages`

   

2. #### Installing a database server

   Because most of the non-volatile information and configuration is stored in a SQL-database, you need to install a database server. **If you already have installed a recent version of MariaDB** on your target system, you can skip this section.

   Here are the steps to install the server:

   `sudo apt install mariadb-server`

   `sudo mysql_secure_installation` 

   The Secure-Installation-Tool will ask you for the root password. Do that and accept the default for all the other questions.

   

3. #### Creating an db user

   We need a special CAM-AI-User for the database:

   `sudo mysql`

   `grant all on *.* to 'CAM-AI'@'localhost' identified by '[enter your password here]' with grant option;`

   `flush privileges;`

   `exit`

   

4. #### Cloning this repository from Github 

   If needed, install GIT:

   `sudo apt install git`

   Then do the cloning:

   `git clone https://github.com/ludgerh/cam-ai`

   

5. #### Create the database in the local server

   Log in as the new user. You will need the password you defined in Section 3:

   `mysql -u CAM-AI -p`

   Then create the database:

   ``create database `CAM-AI`;``

   `exit`

   Import the initial data:

   `mysql -u CAM-AI -p "CAM-AI" < ~/cam-ai/sql/new.sql` !!!!

   

6. #### Create your private password file

   `cp ~/cam-ai/camai/passwords.py.example ~/cam-ai/camai/passwords.py`

   `nano ~/cam-ai/camai/passwords.py`

   Modify the two variables db_password and security_key. The easiest way to get a valid Django Security Key is usinfg the generator on https://djecrety.ir/ .

   Save and close Nano.

   

7. #### Create an Python environment

   On Raspi-Debian you have to install Python first:

   `sudo apt install python3`

   `sudo apt install python3-dev`

   Change to the project folder:

   `cd ~/cam-ai`

   Install the virtual environment tool, create an environment and update PIP:

   `sudo apt install python3-venv`

   `python3 -m venv env`

   `source env/bin/activate`

   `pip install --upgrade pip`

   

8. #### **Install the needed software components**

   `sudo apt install default-libmysqlclient-dev`

   `sudo apt install build-essential`

   `sudo apt install ffmpeg` 

   `sudo apt-get install libgeos-dev`

   `sudo apt install redis`

   In default Redis saves all database contents to disk. We do not want this. So we switch it off:

   `sudo nano /etc/redis/redis.conf`

   Find the lines

   `save 900 1`

   `save 300 10`

   `save 60 10000`

    and change them to 

   `#save 900 1`

   `#save 300 10`

   `#save 60 10000`

   

8. #### Fill the environment with all needed libraries

   `pip install django`

   `pip install channels==3.0.5`

   `pip install mysqlclient` 

   `pip install pillow`

   `pip install opencv-contrib-python`

   `pip install requests`

   `pip install multitimer`

   `pip install shapely`

   `pip install django_tables2`

   `pip install setproctitle`

   `pip install websocket-client`

   `pip install redis`

   `pip install psutil`

   

10. #### Start the server

   `nano ~/cam-ai/camai/settings.py`

   Find the variable ALLOWED_HOSTS and add your hosts domain or IP address to the bracket.

   Find the line

   `STATICFILES_DIRS = [str(BASE_DIR)+'/camai/static', ]`

   and replace it with

   `#STATICFILES_DIRS = [str(BASE_DIR)+'/camai/static', ]`

   Save and close Nano.

   After that you should be able to start the server. Replace the IP (plus brackets(!)) with the actual address of your server host.

   `python manage.py runserver [ip]:8000 --noreload`

10. #### Log in

    From another PC in the same network you can now log in by giving your browser:
    `https://[ip]:8000/`
    The initial login information is user=admin password=cam-ai-123

    
