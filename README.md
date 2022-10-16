# Flight-Tracker

This project takes ADS-B signals from aircraft collected by an SDR (Software-Defined-Radio) then pushes the information to a database. The data can then be used in countless ways.
The main parameters that processed in this repository are the aircraft callsign, latitude, longitude, speed, and heading. 
Originally inspired by [FlightRadar24](https://www.flightradar24.com/).
Since I am a beginner at this, I used a very simple SDR with many useful features inside. It is identical to the one on **[this](https://store.adsbexchange.com/collections/frontpage/products/adsbexchange-com-r820t2-rtl2832u-0-5-ppm-tcxo-ads-b-sdr-w-amp-and-1090-mhz-filter-software-on-industrial-microsd)** website.

## How it works

Currently, the project analyzes the flights that are passing the area of detection or have departed or arrived from that area. 
The data collected by the SDR is run through [Malcolm Robb's dump1090](https://github.com/MalcolmRobb/dump1090) decoder, and then sent to a TCP server port. Then, by using netcat, the data sent through the TCP port is written to a text file. Each line is a Mode S message sent by an aircraft. The program pushToDB.py reads the file and inputs it into a MySQL database with only the necessary information only. Then, the flightsAnalysis.py program can perform the analysis after reading the database.
The process of running the decoder and writing to a text file was automated with a bash script.
The bash scripts in this repository were drawn from **[this](https://www.satsignal.eu/raspberry-pi/dump1090.html)** website. They can be used to automatically run in a cronjob. 

## Getting started

As of the latest commit, an SDR is required to run the programs.
The steps below are:
1) First, clone the project:

```
    git clone https://github.com/WilliamZhang20/Flight-Tracker.git
    cd Flight-Tracker
```
2) Then, install MariaDB and the python-dotenv package:

```
    sudo pip3 install python-dotenv
    sudo apt-get update
    sudo apt-get upgrade
    sudo reboot
    sudo apt install mariadb-server
    sudo python3 -m pip install mysqlclient
    sudo mysql_secure_installation
```
3) Next, answer 'no' to all installation prompts, set your password, and then enter the server to create the FlightData database:

```
    sudo mysql -u root -p
    CREATE DATABASE FlightData;
```
4) After that, create a file called `.env` to define environment variables `mysql_username`, `mysql_password`, and `data_file`. The python programs will need to know which text file the flight data has been written to. 
    For example:
```
    mysql_username=your_username
    mysql_password=your_password
    data_file=directory_from_ncShellFile
```
5) Finally schedule the automatic collection of data in the cronjob based on the example below. 

For example, with generic names: (The 'shebang' is the Unix shebang, like /bin/sh for example)
Furthermore, the process needs to be reloaded to avoid data overflow in file.
```
    min hr * * * shebang sudo ./directory/Flight-Tracker/dump1090.sh start
    min hr * * * shebang sudo ./directory/Flight-Tracker/ncToFile.sh start
    min hr * * * shebang sudo ./directory/Flight-Tracker/ncToFile.sh reload
```

## Future Updates

- Automatically push to database when task is reloaded
- A web app to see the past flights on a map
- Back-end features to open the website from anywhere
- A more advanced SDR receiver setup where parts can be manually chosen to be added or not, like the bias tee, amplifier, type of antenna, etc.
