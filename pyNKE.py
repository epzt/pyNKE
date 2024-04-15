import pysftp
import os
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from stat import ST_CTIME

#######################################################################################
# Global variable to change according your settings
CURRENT_DIR = os.getcwd()
LOCAL_DATA_DIR = os.path.join(CURRENT_DIR, "data")
LOCAL_GPX_DIR = os.path.join(CURRENT_DIR, "gpx")
LOCAL_ALARM_DIR = os.path.join(CURRENT_DIR, "alarm")
OUTPUT_FILE_NAME = os.path.join(CURRENT_DIR, "Total_Measurements.txt")

########################################################################################
# DO NOT CHANGE AFTER THIS
########################################################################################
# Constant declarations
SENSORNAME = ["Pressure",
              "Temperature",
              "Chlorophyll_a",
              "pH",
              "Turbidity",
              "Oxygen_Concentration",
              "Oxygen_Saturation",
              "Oxygen_Temperature",
              "Conductivity",
              "Temperature",
              "Practical_Salinity"]

years = mdates.YearLocator()   # every year
months = mdates.MonthLocator()  # every month
days = mdates.DayLocator(bymonthday=range(1,32), interval=1)  # every day
hours = mdates.HourLocator(interval=6)
hoursFmt = mdates.DateFormatter('%H:%M')
daysFmt = mdates.DateFormatter('%d-%m-%y')

class Sftp:
    def __init__(self):
        """Constructor Method"""
        # Set connection object to None (initial value)
        self.connection = None
        self.hostname = "ftp.nke-i.com"
        self.username = "wimo-5a47"
        self.password = "!27TE?2H$6"
        self.port = 22

    def connect(self):
        """Connects to the sftp server and returns the sftp connection object"""
        try:
            # Get the sftp connection object
            self.connection = pysftp.Connection(
                host=self.hostname,
                username=self.username,
                password=self.password,
                port=self.port,
            )
        except Exception as err:
            raise Exception(err)
        finally:
            print(f"Connected to {self.hostname} as {self.username}.")

    def disconnect(self):
        """Closes the sftp connection"""
        self.connection.close()
        print(f"Disconnected from host {self.hostname}")

    def listdir(self, remote_path):
        """lists all the files and directories in the specified path and returns them"""
        for obj in self.connection.listdir(remote_path):
            yield obj

    def listdir_attr(self, remote_path):
        """lists all the files and directories (with their attributes) in the specified path and returns them"""
        for attr in self.connection.listdir_attr(remote_path):
            yield attr

    def download(self, remote_file, target_local_path):
        try:
            print(
                f"downloading from {self.hostname} as {self.username} [(remote path : {remote_file});(local path: {target_local_path})]"
            )

            # Create the target directory if it does not exist
            if not os.path.isdir(target_local_path):
                try:
                    os.makedirs(target_local_path)
                except Exception as err:
                    raise Exception(err)

            # Download from remote sftp server to local
            self.connection.get(remote_file, os.path.join(target_local_path,remote_file))
            print("download completed")

        except Exception as err:
            raise Exception(err)


########################################################################################
#
########################################################################################
class Measure():
    def __init__(self, parent=None):
        # Variables
        self._ldata = []
        self._datetime = ""

    def SetDateTime(self, strstr):
        if len(strstr) >= 12:
            self._datetime = dt.datetime(int(strstr[0:4]), int(strstr[5:7]), int(strstr[8:10]), int(strstr[11:13]),
                                         int(strstr[14:16]), int(strstr[17:19]))
            return True
        return False

    def GetDateTime(self):
        return self._datetime

    def GetDate(self):
        return self._datetime.date()

    def GetTime(self):
        return self._datetime.time()

    def SetDataList(self, strstr):
        if len(strstr) > 0:
            self._ldata = strstr.split(",")[1:]
            return True
        return False

    def GetDataList(self):
        return self._ldata

def get_files_by_date(directory):
    os.chdir(directory)
    files = [(os.stat(fname)[ST_CTIME], fname) for fname in os.listdir(directory) if os.path.isfile(fname)]
    files.sort()
    return [f for s,f in files]

def str2datetime(a):
  a = dt.datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
  return(a)

def GetFiles():
    # Create SFTP object
    sftp = Sftp()
    # Connect to SFTP
    sftp.connect()
    # Lists files with attributes of SFTP
    remote_path = "./"
    list_of_remote_files = [f for f in sftp.listdir(remote_path)]
    downloaded_data_files = 0
    present_data_files = 0
    # Download files from SFTP
    for f in list_of_remote_files:
        if "5a47_data" in os.path.basename(f):
            if not os.path.isfile(os.path.join(LOCAL_DATA_DIR,f)):
                sftp.download(f, LOCAL_DATA_DIR)
                downloaded_data_files += 1
            else:
                present_data_files += 1
        elif "5a47_gps" in os.path.basename(f):
            if not os.path.isfile(os.path.join(LOCAL_GPX_DIR,f)):
                sftp.download(f, LOCAL_GPX_DIR)
                downloaded_data_files += 1
            else:
                present_data_files += 1
        elif "5a47_alarm" in os.path.basename(f):
            if not os.path.isfile(os.path.join(LOCAL_ALARM_DIR,f)):
                sftp.download(f, LOCAL_ALARM_DIR)
                downloaded_data_files += 1
            else:
                present_data_files += 1
        else:
            printf(f"File {f} is not managed")
    # Disconnect from SFTP
    sftp.disconnect()
    return downloaded_data_files, present_data_files

# Create and fill the result file
def ConcatData():
    try:
        resDataFile = open(OUTPUT_FILE_NAME,'w')  # Default file name (see at the top)
    except:
        return False
    sepChar = '\t'
    strHeader = "Date"+sepChar+"Heure"+sepChar
    for i in range(len(SENSORNAME)-1):
        strHeader += SENSORNAME[i] + sepChar
    strHeader += SENSORNAME[len(SENSORNAME)-1] + '\n'
    resDataFile.write(strHeader)  # Write field names

    M = Measure()
    # Loop over the data files located in the data folder
    for lfile in get_files_by_date(LOCAL_DATA_DIR):
        fname = lfile.split(".")[0]
        startdatetime = "{}-{}-{}".format(2000+int(fname.split("_")[2][0:2]),
                                                    fname.split("_")[2][2:4],
                                                    fname.split("_")[2][4:6])
        with open(lfile,'r', errors='ignore') as f:
            lcontent = f.readlines()  # Open the file and read it

        for lline in lcontent:   # Loop over lines
            lline.rstrip('\n')
            if len(lline) <= 2:  # Do nothing if line too short
                continue
            if not lline.startswith(startdatetime): # Skip header lines
                continue
            if M.SetDateTime(lline.split(",")[0]):  # extraction of the date
                resDataFile.write(str(M.GetDate())+sepChar+str(M.GetTime())+sepChar)  # Write data and time

            if M.SetDataList(lline):  # extraction of values from the line
                ldata = len(M.GetDataList())
                for i in range(ldata-1):  # Lopp over values
                  resDataFile.write(str(M.GetDataList()[i]) + sepChar)  # write n-1 values
                resDataFile.write(str(M.GetDataList()[ldata-1]))  # Write the last value
    # Close file
    resDataFile.close()
    return True


#####################################################################################
# Class de gestion d'affichage des graphes SAMBAT
#####################################################################################
class PlotNKE():
    def __init__(self, _dFileName, _dSepChar, parent=None):
        self.initDate = 0
        self.lastDate = 0
        self.xdata = []
        self.dFileName = _dFileName
        self.dSepChar = _dSepChar
        self.nGraphs = 10  # Nombre de graphics
        self.tideChbg = None
        return

    def plotGraphics(self):
        # Load the data set
        self.getData()
        fig, axes = plt.subplots(nrows=self.nGraphs,ncols=1,sharex=True)
        colors = ["black","red", "green","brown","blue","yellow","black","red","green","brown","blue"]

        fig.subplots_adjust(hspace=0.9,top=0.95,bottom=0.1,left=0.1,right=0.95,wspace=0.1)
        for i in range(self.nGraphs):
           axes[i].plot_date(self.xdata, self.ydata[:,i],ls='solid',marker="None",fmt=colors[i],xdate=True)
           axes[i].set_title(SENSORNAME[i])
           # format the ticks
           axes[i].xaxis.set_major_locator(months)
           axes[i].xaxis.set_major_formatter(daysFmt)
           axes[i].format_xdata = daysFmt
           axes[i].xaxis.set_minor_locator(hours)
           axes[i].xaxis.set_minor_formatter(hoursFmt)
           axes[i].set_xlim(min(self.xdata), max(self.xdata))
           axes[i].grid(True)
           axes[i].xaxis_date()

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        fig.autofmt_xdate()
        plt.show()

    def getData(self):
        try:
          with open(self.dFileName): pass
        except IOError:
          print(f"File {self.dFileName} cannot be read")
          return

        with open(self.dFileName,'r', errors='ignore') as dataFile:
            lcontent = dataFile.readlines()  # Open and read the entire file

        # It is considering the first line containts names of variables and the number of fields
        # of this line correspond to the number of graphs to draw
        self.nGraphs = len(lcontent[0].rstrip('\n').split(self.dSepChar))-2

        firstpass = True
        for lline in lcontent[1:]:   # Loop over data lines
          lineData = lline.rstrip('\n').split(self.dSepChar)
          theData = [float(i) for i in lineData[2:]]
          currentDateTime = np.datetime64(lineData[0]+'T'+lineData[1]+'.00Z')
          if firstpass:
              self.xdata = currentDateTime
              self.initDate = self.xdata
              self.ydata = np.array(np.asarray(theData)) # fill the array
              firstpass=False
          else:
              self.xdata = np.append(self.xdata, currentDateTime)
              self.ydata = np.append(self.ydata,np.asarray(theData)) # fill the array array

        self.lastDate = self.xdata[len(self.xdata)-1]

        self.xdata = pd.to_datetime(self.xdata)
        self.ydata.resize(len(self.xdata), self.nGraphs)
        return

if __name__ == "__main__":
    downloaded, present = GetFiles()
    print(f"{downloaded} new data files downloaded")
    print(f"{present} files ignored (still present)")
    ConcatData()
    pltNKE = PlotNKE(OUTPUT_FILE_NAME, '\t')
    pltNKE.plotGraphics()
