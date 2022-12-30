# Flight-Tracker

This project processed ADS-B signals from aircraft collected by an SDR (Software-Defined-Radio) then pushes the information to a database for later analysis.

Here's the [antenna](https://store.adsbexchange.com/collections/frontpage/products/adsbexchange-com-r820t2-rtl2832u-0-5-ppm-tcxo-ads-b-sdr-w-amp-and-1090-mhz-filter-software-on-industrial-microsd) that I used. 

The main parameters that processed are aircraft callsign, altitude, serial number, location coordinates, speed, and heading. 

In the repository, the file pushToDB.py processes that data and stores it in a MariaDB database. It also analyzes the number of local and passing flights around the area of detection, and the busiest hours. Then the analysis results are stored.

## How it works

After plugging the SDR into my Raspberry Pi, I installed a decoder called [dump1090](https://github.com/MalcolmRobb/dump1090) by MalcolmRobb, which processes signals and turns them into readable data. 

In order to collect this data, I used the networking feature of dump1090, in which I could send data to a TCP port. The data contains timestamped lines, with each line being a decoded message from an aircraft in the vicinity containing location, altitude, heading, speed, etc.

To automate the collection process, I wrote two shell scripts that are scheduled by a crontab to start and stop and certain times every day.

- The first script runs dump1090 and sends data to the port. Its structure was inspired from [this](https://www.satsignal.eu/raspberry-pi/dump1090.html) website.
- The second script will intially clear all the space in a text file that stores data. Then, it uses the [netcat](https://www.geeksforgeeks.org/introduction-to-netcat/) network utility to read the port and send all its data to a text file. 

As soon as the scripts stop running for the day, the program pushToDB.py is run. It will:
1. Read the text file, remove unecessary information, and store it in a temporary flight data table in a MariaDB database. 
2. Scan through the table once to collect the number of flights each hour, the overall information about each flight, and the total number of local adn passing flights that day.
3. Sorts the array with the number of flights each hour to rank them, and then stores the other analysis results from the sorting and step #2 in separate databases for different types of data.
4. Deletes the temporary table when step #3 is done.

Hundreds of thousands of messages could be processed over the course of 1 day, so running pushToDB.py can take about 10 minutes.

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
Note: be sure to also edit "PROG_FILE" in ncToFile.sh to the same file chosen in the data_file from .env

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

- A web app to see the past flights on a map or to livestream data.
- Hosting the web server on my Raspberry Pi to open the website from anywhere
- A more advanced SDR receiver setup where parts can be manually chosen to be added or not, like the bias tee, amplifier, type of antenna, etc.
