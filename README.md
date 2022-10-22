# Flight-Tracker

This project takes ADS-B signals from aircraft collected by an SDR (Software-Defined-Radio) then pushes the information to a database. The data can then be used in countless ways.
The main parameters that processed in this repository are the aircraft callsign, latitude, longitude, speed, and heading. <br/>
I was originally inspired by [FlightRadar24](https://www.flightradar24.com/) and thhe way it and other websites crowdsource data.</br>
When I obtained my SDR, I initially used the adsbexchange.com feed client to feed my data to their website just like FlightRadar24 does it for theirs. 
But then I uninstalled the feed client to process and analyze the data from my SDR.
Since I am a beginner at this, I used a very simple SDR with many useful features inside. It is identical to the one on **[this](https://store.adsbexchange.com/collections/frontpage/products/adsbexchange-com-r820t2-rtl2832u-0-5-ppm-tcxo-ads-b-sdr-w-amp-and-1090-mhz-filter-software-on-industrial-microsd)** website. To run the programs, I attached the SDR to the USB port on my Raspberry Pi 3 Model B+.

## How it works

Currently, the project analyzes the number of flights that are passing the area of detection or have departed or arrived from that area. 
The data collected by the SDR is run through [Malcolm Robb's dump1090](https://github.com/MalcolmRobb/dump1090) decoder, and then sent to a TCP server port. Then, by using netcat, the data sent through the TCP port is written to a text file. Each line is a Mode S message sent by an aircraft. The program pushToDB.py reads the file and inputs it into a MySQL database with only the necessary information. Then, the flightsAnalysis.py program can perform the analysis after reading the database.
The process of running the decoder and writing to a text file was automated with a bash script.
The bash scripts in this repository were inspired from [this](https://www.satsignal.eu/raspberry-pi/dump1090.html) website. They can be used to automatically run in a cronjob. 

## Getting started

As of the latest commit, an SDR is required to be plugged in to run the programs.
The steps below are:
1) First, clone the project:

```
    git clone https://github.com/WilliamZhang20/Flight-Tracker.git
    cd Flight-Tracker
```
2) Then, install MariaDB  and the python-dotenv package:

```
    sudo pip3 install python-dotenv
    sudo apt-get update
    sudo apt-get upgrade
    sudo reboot
    sudo apt install mariadb-server
    sudo python3 -m pip install mysqlclient
    sudo mysql_secure_installation
    sudo mysql -u root -p
    CREATE DATABASE FlightData;
```
3) Next, set up dump1090, netcat, and the bash scripts, and use UFW (uncomplicated firewall) to enable the network ports:

```
    cd ~
    git clone https://github.com/MalcolmRobb/dump1090.git
    make
    sudo apt-get install netcat
    cd Flight-Tracker
    chmod +x dump1090.sh
    chmod +x ncToFile.sh
    sudo apt-get install ufw
    sudo ufw enable
    sudo ufw allow 30003
``` 

4) After that, create a file called `.env` to define environment variables `mysql_username`, `mysql_password`, and `data_file`. The python programs will need to know which text file the flight data has been written to. 
    For example:
```
    mysql_username=your_username
    mysql_password=your_password
    data_file=directory_from_ncShellFile
```
5) Finally schedule the automatic collection of data in the cronjob based on the example below. 

    For example, with generic names: (run 'which sh' on your terminal, then type that into the bash_shebang of crontab **and** the header of each shell script) </br>
    The process needs to be reloaded/restarted at a set time interval to avoid data overflow in file. </br>
    Be sure to run dump1090 at least a minute before running netcat, as some data needs to come in for processing or else netcat will just cut out. 
```
    SHELL=bash_shebang
    PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

    min hr * * * sudo bash_shebang /full_directory/Flight-Tracker/dump1090.sh start
    min hr * * * sudo bash_shebang /full_directory/Flight-Tracker/ncToFile.sh start
    min hr * * * sudo bash_shebang /full_directory/Flight-Tracker/ncToFile.sh reload
```

## Future Updates

- Automatically push to database when task is reloaded
- A web app to see the past flights on a map
- Hosting the web server on my Raspberry Pi to open the website from anywhere
- A more advanced SDR receiver setup where parts can be manually chosen to be added or not, like the bias tee, amplifier, type of antenna, etc.
