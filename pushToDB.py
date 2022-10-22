import os
import MySQLdb
from dotenv import load_dotenv
from datetime import date

load_dotenv()

mysql_username = os.getenv('mysql_username')
mysql_password = os.getenv('mysql_password')
data_file = os.getenv('data_file')

conn = MySQLdb.connect(
    host = 'localhost',
    user = mysql_username,
    password = mysql_password,
    database = 'FlightData'
)

cursor = conn.cursor()

def checkIfHasWords(str): # If at least 1 character is a letter, it is accepted
    for i in str:
        if i.isalpha():
            return True
    return False

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

today = date.today()
Date = today.strftime("%b_%d_%Y") # eg. Sep_16_2019. (source: https://www.programiz.com/python-programming/datetime/current-datetime)
month = today.strftime("%B_%Y")

def enterData(list):
    if list == [' ']:
        return
    for i in range(len(list)):
        if list[i] == '':
            list[i] = 'null' # replace blanks with nulls to fill space
    insertOper = "INSERT INTO {}(Date, Time, SerialNum, Callsign, Altitude, Speed, Track, Latitude, Longitude) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);".format(month)
    data = (list[0], list[1], list[2], list[3], list[4], list[5], list[6], list[7], list[8])
    cursor.execute(insertOper, data) # when entering data, put MySQL and data separately, like this

file = open(data_file, 'r')
lines = file.readlines()
# Table names should have lowercase words separated by underscores
cursor.execute("CREATE TABLE IF NOT EXISTS {} (Date VARCHAR(255), Time VARCHAR(255), SerialNum VARCHAR(255), Callsign VARCHAR(255), Altitude VARCHAR(255), Speed VARCHAR(255), Track VARCHAR(255), Latitude VARCHAR(255), Longitude VARCHAR(255));".format(month))

# scanning
for line in lines:
    if checkIfHasWords(line)==False:
        break
    dataList = processData(line)
    enterData(dataList)
print("Successfully finished for {}".format(Date))
conn.commit()
conn.close()
