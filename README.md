# Flight-Tracker

This project takes ADS-B signals from aircraft collected by an SDR (Software-Defined-Radio) then pushes the information to a database. The data is then analyzed by a separate program.
The main parameters that processed in this repository are the aircraft callsign, altitude, mode S code, latitude, longitude, speed, and heading. <br/>
I was originally inspired by [FlightRadar24](https://www.flightradar24.com/) and the way it and other websites crowdsource data.</br>
When I obtained my SDR, I initially used the adsbexchange.com feed client to feed my data to their website just like FlightRadar24 does it for theirs. 
I then decided to process and analyze the data myself. However, the dump1090 signal decoder which was most flexible, could not operate at the same time as the readsb signal decoder required for the feed client. As a result, I had to uninstall the feed client and the readsb signal decoder.
Since I am a beginner at working with SDRs, I used a very simple SDR with many useful features inside. It is identical to the one on **[this](https://store.adsbexchange.com/collections/frontpage/products/adsbexchange-com-r820t2-rtl2832u-0-5-ppm-tcxo-ads-b-sdr-w-amp-and-1090-mhz-filter-software-on-industrial-microsd)** website. To run the programs, I plugged the SDR to the USB port on my Raspberry Pi 3 Model B+ on which I wrote and ran this repo's code.

## How it works

Currently, the project analyzes the number of flights that are passing or arre local to the area of detection and the busiest hours of detection. 
The data collected by the SDR is run through [Malcolm Robb's dump1090](https://github.com/MalcolmRobb/dump1090) decoder, and then sent to a TCP server port. Then, by using netcat, the data sent through the TCP port is written to a text file. 
The process of running the decoder and writing to a text file was automated with the two bash scripts.
The bash scripts in this repository were inspired from [this](https://www.satsignal.eu/raspberry-pi/dump1090.html) website. A cronjob can be used to automate the excecution of these scripts.  
</br>
Each line sent to the text file is a Mode S message sent by an aircraft. The file pushToDB.py will process the lines, and then push a filtered version of each line into a temporary table of a MySQL database called FlightData. That same program will analyze the data in the lines and break it down into three categories: the overall paramters of each flight that was tracked, the busiest hours tracked, and a basic summary of the status of flights. Each category's information for the day will be pushed into its own database, with 1 table per month. Note that number of flights is not necessarily number of planes, as an arriving and departing aircraft will mean 1 arriving flight and 1 departing flight.</br>
The database called FlightStats records 1 flight per line, and each line will contain the flight's date, flight parameters, and the range of time that it was detected. The database FlightsPerHour has a list of each hour tracked by the receiver. Every day, a list of hours, ordered from the busiest hours first to the least busiest last, will be added. The database called DataSummary will have 1 line per day, and each line will detail the number of departing, arriving, local, passing, and total flights. </br>
Hundreds of thousands of messages could be processed over the course of 1 day, so running pushToDB.py can take about 5 minutes. In addition, the temporary data table containing all the lines is dropped after the simplified portions have been pushed to their respective databases.
Next, in the file db_analysis.py, the user can request a valid date range (like 2022/07/07 - 2022/09/09, for example), and the program will output a data summary from those dates. For example, it will output the top 10 busiest days (if possible), the busiest hours of the day on average, and the average number of passing or local flights. Furthermore, a list of the 10 most commonly occuring flight numbers will be outputted. 

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
    CREATE DATABASE FlightStats;
    CREATE DATABASE FlightsPerHour;
    CREATE DATABASE DataSummary;
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

    For example, with generic names: (run 'which sh' on your terminal, then paste the resulting otuput into the parts of crontab filled in as 'bash_shebang') </br>
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

- A web app to see the past flights on a map
- Hosting the web server on my Raspberry Pi to open the website from anywhere
- A more advanced SDR receiver setup where parts can be manually chosen to be added or not, like the bias tee, amplifier, type of antenna, etc.
