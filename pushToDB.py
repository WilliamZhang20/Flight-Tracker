import os
import MySQLdb
from dotenv import load_dotenv
from datetime import date

load_dotenv()

mysql_username = os.getenv('mysql_username')
mysql_password = os.getenv('mysql_password')
data_file = os.getenv('data_file')

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

conn = connect_to_db('localhost', mysql_username, mysql_password, 'FlightData')
conn2 = MySQLdb.connect('localhost', mysql_username, mysql_password, 'FlightStats')
conn3 = MySQLdb.connect('localhost', mysql_username, mysql_password, 'FlightsPerHour')
conn4 = MySQLdb.connect('localhost', mysql_username, mysql_password, 'DataSummary')

cursor = conn.cursor()
cursor2 = conn2.cursor()
cursor3 = conn3.cursor()
cursor4 = conn4.cursor()

def checkIfHasWords(str): # If at least 1 character is a letter, it is accepted
    for i in str:
        if i.isalpha():
            return True
    return False

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

def processData(line):
    x = line.split(",") # split into list based on commas (see sample line in README)
    if x[14] == '' and x[10]=='' and x[11] == '' and x[12] == '':
        return [' '] # has no usable data (no alt, spd, hdg, etc), therefore is blank
    del x[8:10] # delete date duplicate
    del x[0:4] # delete unecessary data in front
    del x[1]
    del x[9:15] # delete unecessary data at back
    x.insert(2, x.pop(0))
    return x

table_name = "Temp_Data_Table"

def enterData(list):
    if list == [' ']:
        return
    for i in range(len(list)):
        if list[i] == '':
            list[i] = 'null' # replace blanks with nulls to fill space
    insertOper = "INSERT INTO {}(Date, Time, SerialNum, Callsign, Altitude, Speed, Track, Latitude, Longitude) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);".format(table_name)
    data = (list[0], list[1], list[2], list[3], list[4], list[5], list[6], list[7], list[8])
    cursor.execute(insertOper, data) # when entering data, put MySQL and data separately, like this
    conn.commit()

class aircraft:
    global keyAlt
    keyAlt= 5000 # determines if passing or local
    def __init__(self, row):
        self.date = row[0]
        self.init_time = row[1]
        self.time = row[1] # last time detected
        self.planeid = row[2] # hex serial number
        self.status = "passing"
        self.callsign = row[3]
        if row[4] != "null" and row[4] != "0": # record altitude change
            self.init_alt = int(row[4])
            self.curr_alt = self.init_alt
            if self.curr_alt <= keyAlt:
                self.status = "local  "
        else:
            self.init_alt = 0
            self.curr_alt = 0
        if row[5] != "null": # record speed change
            self.init_spd = row[5]
            self.curr_spd = self.init_spd
        else:
            self.init_spd = "0"
            self.curr_spd = "0"
        if row[6] != "null": # record track/heading change
            self.init_trk = row[6]
            self.curr_trk = self.init_trk
        else:
            self.init_trk = "0"
            self.curr_trk = "0"
        if row[7] != "null": # lat change
            self.init_lat = row[7]
            self.curr_lat = self.init_lat
        else:
            self.init_lat = "0"
            self.curr_lat = "0"
        if row[8] != "null": # lon change
            self.init_lon = row[8]
            self.curr_lon = self.init_lon
        else:
            self.init_lon = "0"
            self.curr_lon = "0"

    def update_attrs(self, row):
        self.time = row[1]
        if row[3] != "null":
            self.callsign = row[3]
        if row[4] != "null" and row[4] != "0":
            if self.init_alt == 0:
                self.init_alt = int(row[4])
            self.curr_alt = int(row[4])
            if self.curr_alt <= keyAlt:
                self.status = "local  "
        if row[5] != "null":
            self.curr_spd = row[5]
        if row[6] != "null":
            self.curr_trk = row[6]
        if row[7] != "null":
            self.curr_lat = row[7]
        if row[8] != "null":
            self.curr_lon = row[8]

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

file = open(data_file, 'r')
lines = file.readlines()
# Table names should have lowercase words separated by underscores
cursor.execute("CREATE TABLE IF NOT EXISTS {} (Date VARCHAR(255), Time VARCHAR(255), SerialNum VARCHAR(255), Callsign VARCHAR(255), Altitude VARCHAR(255), Speed VARCHAR(255), Track VARCHAR(255), Latitude VARCHAR(255), Longitude VARCHAR(255));".format(table_name))
conn.commit()

Date = ""
# scanning
setDate = False
for line in lines:
    if checkIfHasWords(line)==False:
        break
    dataList = processData(line)
    if dataList != [' ']:
        Date = dataList[0]
    enterData(dataList)
    if setDate==False:
        Date = dataList[0]
        setDate = True
print("Pushed to temporary data table... now to other tables")

idxMonth = Date.find("/")
monthRaw = Date[idxMonth+1:(idxMonth+3)]
monthProcessed = processMonth(monthRaw)
month_yr = monthProcessed + "_" + Date[:idxMonth]

print(month_yr)

cursor.execute("SELECT * FROM {}".format(table_name))
conn.commit()
res = cursor.fetchall()
cursor2.execute("CREATE TABLE IF NOT EXISTS {} (Date VARCHAR(255), ModeS_Code VARCHAR(255), Callsign VARCHAR(255), Status VARCHAR(255), Times VARCHAR(255), Altitudes VARCHAR(255), Speeds VARCHAR(255), Headings VARCHAR(255), Latitudes VARCHAR(255), Longtitudes VARCHAR(255));".format(month_yr))
conn2.commit()
cursor3.execute("CREATE TABLE IF NOT EXISTS {} (Date VARCHAR(255), HourOfDay INT, Ranking INT, NumOfFlights INT);".format(month_yr))
conn3.commit()
cursor4.execute("CREATE TABLE IF NOT EXISTS {} (Date VARCHAR(255), Num_Flights INT, Num_Passing INT, Num_Local INT, Num_Departing INT, Num_Arriving INT);".format(month_yr))
conn4.commit()

currFlights = [] # array of aircraft objects
hourTracker = [] # to rank busiest hours

num_local = 0 # departing or arriving from area of detection
num_passing = 0
num_departing = 0 # departing the area of detection
num_arriving = 0

print("The aircraft detected are:")

setHour = False
countPrev = 0 # count out of range flights that flew during the hour

for row in res:
    # Method for any analysis: maintaining aircraft objects (def above).
    # every row stores: Date, time, hex, callsign, altitude, speed, track, latitude, longitude
    # every row of currFlights will be the same, but also with initial and final altitude
    currTime = row[1]
    entered = False
    toRemove = []
    if setHour == False: # to count num. of flights per hour
        currHour = int(currTime[0:(currTime.find(":"))])
        setHour = True
    else:
        currTimeHr = int(currTime[0:currTime.find(":")])
        if currTimeHr - currHour >= 1 or currTimeHr < currHour:
            temp = [currHour, len(currFlights) + countPrev]
            hourTracker.append(temp)
            currHour = currTimeHr
            countPrev = 0
    for set in currFlights:
        if row[2] == set.planeid and entered==False:
            # update the variables in the set
            entered = True
            set.update_attrs(row)
        elif outOfRange(currTime, set.time)==True:
            # Update analysis variables
            if set.status == "local  ":
                if set.curr_alt > set.init_alt:
                    num_departing += 1
                elif set.curr_alt < set.init_alt:
                    num_arriving += 1
                else:
                    num_local -= 1
                    num_passing += 1
                num_local += 1
            else:
                num_passing += 1
            atcSign = "none    "
            if set.callsign != "null":
                atcSign = set.callsign
            print("- Hex:", set.planeid, " Callsign:", atcSign, "Status:", set.status, " Altitude:", set.init_alt, "-", set.curr_alt)
            oper = "INSERT INTO {} (Date, ModeS_Code, Callsign, Status, Times, Altitudes, Speeds, Headings, Latitudes, Longtitudes) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);".format(month_yr)
            data = (set.date, set.planeid, set.callsign, set.status, (set.init_time + "-" + set.time), (str(set.init_alt) + "-" + str(set.curr_alt)), (set.init_spd + "-" + set.curr_spd), (set.init_trk + "-" + set.curr_trk), (set.init_lat + "-" + set.curr_lat), (set.init_lon + "-" + set.curr_lon))
            cursor2.execute(oper, data)
            conn2.commit()
            countPrev += 1
            toRemove.append(set) # remove all out of range at the end
    if entered == False:
        # if the planeid was not found in current flights, it is new
        newPlane = aircraft(row)
        currFlights.append(newPlane)
    for left in toRemove: # removing here
        currFlights.remove(left)
temp = [currHour, len(currFlights)]
hourTracker.append(temp)

for set in currFlights:
    if set.status == "local  ":
        num_local += 1
    else:
        num_passing += 1
    atcSign = "none    "
    if set.callsign != "null":
        atcSign = set.callsign
    print("- Hex:", set.planeid, " Callsign:", atcSign, "Status:", set.status, " Altitude:", set.init_alt, "-", set.curr_alt)

cursor.execute("DROP TABLE {}".format(table_name))
conn.commit()

# print out analysis variables
print("On {}:".format(Date))
print("- {} planes were passing".format(num_passing))
print("- {} planes were local".format(num_local))

def bubbleSort(arr): # used easiest sorting algo
    sz = len(arr)
    for i in range(sz):
        for j in range(0, sz-i-1):
            if arr[j][1] > arr[j+1][1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]

# printing out busiest hours tracked
bubbleSort(hourTracker)
hourTracker.reverse()
print("Busiest hours tracked, from busiest to least busy:")
for i in range(len(hourTracker)):
    print("{}. {}:00 - {}:00, {} flights".format(i+1, hourTracker[i][0], hourTracker[i][0] + 1, hourTracker[i][1]))
    hourDB_oper = "INSERT INTO {} (Date, HourOfDay, Ranking, NumOfFlights) VALUES (%s, %s, %s, %s);".format(month_yr)
    hourDB_data = (Date, hourTracker[i][0], i+1, hourTracker[i][1])
    cursor3.execute(hourDB_oper, hourDB_data)
    conn3.commit()

totalFlights = num_local + num_passing
summaryDB_oper = "INSERT INTO {} (Date, Num_Flights, Num_Passing, Num_Local, Num_Departing, Num_Arriving) VALUES (%s, %s, %s, %s, %s, %s);".format(month_yr)
summaryDB_data = (Date, totalFlights, num_passing, num_local, num_departing, num_arriving)
cursor4.execute(summaryDB_oper, summaryDB_data)
conn4.commit()
print("Successfully finished for {}".format(Date))
conn.close()
conn2.close()
conn3.close()
conn4.close()

