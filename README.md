# Flight-Tracker

This project processes aircraft ADS-B signals collected by an SDR (Software-Defined-Radio), analyzes the data, and stores processed data and analysis results in a database.

Here is the [antenna](https://store.adsbexchange.com/collections/frontpage/products/adsbexchange-com-r820t2-rtl2832u-0-5-ppm-tcxo-ads-b-sdr-w-amp-and-1090-mhz-filter-software-on-industrial-microsd) that I used. 

The main parameters that are processed are aircraft callsign, altitude, serial number, location coordinates, speed, and heading. 

The file `pushToDB.py` processes that data and stores it in a MariaDB database. It also analyzes the number of local and passing flights around the area of detection, and the busiest hours. Then, the analysis results are stored.

## How it works

### Reading the data

After plugging the SDR into my Raspberry Pi, I installed a decoder called [dump1090](https://github.com/MalcolmRobb/dump1090) by MalcolmRobb, which processes signals and turns them into readable data. 

In order to collect this data, I used the networking feature of dump1090, in which I could send data to a TCP port. The data contains timestamped lines, with each line being a decoded message from an aircraft in the vicinity containing location, altitude, heading, speed, etc. Normally one could see live data frames in the terminal by simply calling `dump1090 --interactive`. However, it is impossible to transfer the decoded data frames to a text file directly, so one has to stream it to a TCP port, then read the port and transfer it somewhere. 

To automate the collection process, I wrote two shell scripts that are scheduled by a crontab to start and stop and certain times every day, and will run continuously until stopped.

- The first script, `dump1090.sh`, runs dump1090 and sends data to the port. Its structure was inspired by [this](https://www.satsignal.eu/raspberry-pi/dump1090.html) website. 
- The second script, `ncToFile.sh`, will initially clear all the space in a text file that stores data. Then, it uses the [netcat](https://www.geeksforgeeks.org/introduction-to-netcat/) network utility tool to read the port and send all its data to a text file. 

### Storing & Analyzing Data

As soon as the scripts stop running for the day, the program `pushToDB.py` should be run. It will:
1. Read the text file, remove unnecessary information, and store frames in a temporary flight data table in a MariaDB database. 
2. Scan through the table once to collect many data points. This includes the number of flights each hour, the overall information about each flight (flight number, starting/ending altitudes, locations, speeds, etc.), and the total number of local and passing flights that day.
3. Delete the table storing raw data. This was done to avoid data overflow in the database. 
4. Sort the array with the number of flights each hour to rank them, and then store the other analysis results from the sorting and step #2 in separate databases for different types of data. Please see below for more information. 

The four **databases being used** are:

- The `FlightData` database contains a table that stores raw aircraft frames that are the output of the dump1090 decoder. Each data frame is a transmission from a single aircraft at a certain point in time. The file `pushToDB.py` will simply use it for easier traversal of data. This means that there will be two entire traversals of data, which is very inefficient and requires further work.
- The `FlightStats` database contains information about individual planes. Rather than store all the frames and risk damaging the computer, I decided to simply store each flight's callsign, the start and end detection times, speeds, locations, and altitudes. This would help me determine if this flight was local (i.e. departing or arriving) or simply passing at a high altitude.
- The `FlightsPerHour` database stores information about each hour tracked. The points for each hour include the date, the hour, the number of flights, and the hour's ranking during the entire day. For example, if the most flights were tracked from 14:00 to 15:00, then it will have a ranking of 1, obtained by a basic bubble sorting algorithm (needs improvement).
- The `DataSummary` database is like the title implies: a summary of the data collected on a certain date. Each call of the program `pushToDB.py` will only add a single data point to this database table. Each point contains the total number of flights tracked, and the number of passing, departing, and arriving flights.

Thousands of flight data points could be processed over the course of 1 day, so running pushToDB.py can take about 10 minutes as it will linearly search the entire database twice.

Next, by running the file `db_analysis.py`, the user can request a valid date range (like 2022/07/07 - 2022/09/09, for example), and the program will output a data summary from those dates. For example, it will output the top 10 busiest days (if possible), the busiest hours of the day on average, and the average number of passing or local flights. Furthermore, a list of the 10 most commonly occurring callsigns will be outputted. 

**Notes for improvement:** for now, most of the functions in `db_analysis.py` were migrated to `pushToDB.py` after the change from storing all frames to select data points was made, so `db_analysis.py` is now **redundant** and has yet to be updated. In addition, the file `pushToDB.py` is noticeably too long (300+ lines of code) and must be shortened with **modularization**. Further attempts to make the code more concise should also allow the database connections to persist between modules. 

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
Note: be sure to also edit the "PROG_FILE" variable in ncToFile.sh to the same file chosen in the data_file from .env

5) Finally schedule the automatic collection of data in the cronjob based on the example below. 

    To find which shell interpreter is used on your computer, run `which sh` on your terminal, then paste the _resulting_ _output_ into the parts of crontab currently filled in as 'bash_shebang'.
   
    The process needs to be reloaded/restarted at a set time interval to avoid data overflow in file.
    
    Be sure to run dump1090 at least a minute before running netcat, as some data needs to come in for processing or else netcat will just cut out. 
```
    SHELL=bash_shebang
    PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

    min hr * * * sudo bash_shebang /full_directory/Flight-Tracker/dump1090.sh start
    min hr * * * sudo bash_shebang /full_directory/Flight-Tracker/ncToFile.sh start
    min hr * * * sudo bash_shebang /full_directory/Flight-Tracker/ncToFile.sh reload
```

## Future Updates

- A web app to see past flights on a map or to live stream data.
- Hosting the web server on my Raspberry Pi to open the website from anywhere
- A more advanced SDR receiver setup where parts can be manually chosen to be added or not, like the bias tee, amplifier, type of antenna, etc.
