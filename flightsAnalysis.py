import os
import MySQLdb
from dotenv import load_dotenv
from datetime import date

load_dotenv()

mysql_username = os.getenv('mysql_username')
mysql_password = os.getenv('mysql_password')

def connect_to_db(host_name, username, pw, db):
    try:
        connection = MySQLdb.connect(
            host = host_name,
            user = username,
            password = pw,
            database = db
        )
    except Error as err:
        print("Error: {err}")
    return connection

conn = MySQLdb.connect('localhost', mysql_username, mysql_password, 'FlightData')

cursor = conn.cursor()

def processMonth(monthNumber):
    if monthNumber=="01":
        return "January"
    elif monthNumber=="02":
        return "February"
    elif monthNumber=="03":
        return "March"
    elif monthNumber=="04":
        return "April"
    elif monthNumber=="05":
        return "May"
    elif monthNumber=="06":
        return "June"
    elif monthNumber=="07":
        return "July"
    elif monthNumber=="08":
        return "August"
    elif monthNumber=="09":
        return "September"
    elif monthNumber=="10":
        return "October"
    elif monthNumber=="11":
        return "November"
    elif monthNumber=="12":
        return "December"
    else:
        return "January"

# example input: 2019/09/16
dateRequest = input("Enter date request in yyyy/mm/dd format: ")
idxMonth = dateRequest.find("/")
monthRaw = dateRequest[idxMonth+1:(idxMonth+3)]
monthProcessed = processMonth(monthRaw)
month_yr = monthProcessed + "_" + dateRequest[:idxMonth]

class aircraft:
    global keyAlt
    keyAlt= 5000 # determines if passing or local
    def __init__(self, row):
        self.time = row[1] # last time detected
        self.planeid = row[2] # hex serial number
        self.status = "passing"
        self.callsign = row[3]
        if row[4] != "null":
            self.init_alt = int(row[4])
            self.curr_alt = self.init_alt
            if self.curr_alt <= keyAlt:
                self.status = "local  "
        else:
            self.init_alt = 0
            self.curr_alt = 0
        self.curr_spd = row[5]
        self.trk = row[6]
        self.lat = row[7]
        self.lon = row[8]
    def update_attrs(self, row):
        self.time = row[1]
        if row[3] != "null":
            self.callsign = row[3]
        if row[4] != "null":
            if self.init_alt == 0:
                self.init_alt = int(row[4])
            self.curr_alt = int(row[4])
            if self.curr_alt <= keyAlt:
                self.status = "local  "
        if row[5] != "null":
            self.curr_spd = row[5]
        self.trk = row[6]
        self.lat = row[7]
        self.lon = row[8]

def outOfRange(currTime, lastDetect):
    if int(currTime[0:2])-int(lastDetect[0:2])>=1:
        # different hours
        curr_min = int(currTime[3:5]) + int(lastDetect[3:5])
        last_min = int(lastDetect[3:5])
        if(curr_min-last_min>=5):
            return True
        return False
    elif int(currTime[3:5])-int(lastDetect[3:5])>=5:
        return True # more than 5 minutes apart
    return False

cursor.execute("SELECT * FROM {} WHERE Date='{}'".format(month_yr, dateRequest))
conn.commit()
res = cursor.fetchall()

currFlights = [] # array of aircraft objects

# Analyzing: num of local/passing
num_local = 0 # departing or arriving from area of detection
num_passing = 0
num_departing = 0 # departing the area of detection
num_arriving = 0

print("The aircraft detected are:")

for row in res:
    # Method for any analysis: maintaining aircraft objects (def above).
    # every row stores: Date, time, hex, callsign, altitude, speed, track, latitude, longitude
    # every row of currFlights will be the same, but also with initial and final altitude
    currTime = row[1]
    entered = False
    toRemove = []
    for set in currFlights:
        if row[2] == set.planeid and entered==False:
            # update the variables in the set
            entered = True
            set.update_attrs(row)
        elif outOfRange(currTime, set.time)==True:
            # Update analysis variables
            if set.status == "local  ":
                num_local += 1
            else:
                num_passing += 1
            atcSign = "none    "
            if set.callsign != "null":
                atcSign = set.callsign
            print("- Hex:", set.planeid, " Callsign:", atcSign, "Status:", set.status, " Altitude:", set.init_alt, "-", set.curr_alt)
            toRemove.append(set) # remove all out of range at the end
    if entered == False:
        # if the planeid was not found in current flights, it is new
        newPlane = aircraft(row)
        currFlights.append(newPlane)
    for left in toRemove:
        currFlights.remove(left)

for set in currFlights:
    if set.status == "local  ":
        num_local += 1
    else:
        num_passing += 1
    atcSign = "none    "
    if set.callsign != "null":
        atcSign = set.callsign
    print("- Hex:", set.planeid, " Callsign:", atcSign, "Status:", set.status, " Altitude:", set.init_alt, "-", set.curr_alt)

conn.close()
# print out analysis variables
print("On {}:".format(dateRequest))
print("- {} planes were passing".format(num_passing))
print("- {} planes were local".format(num_local))
