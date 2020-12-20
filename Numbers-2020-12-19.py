#Docdb 20515
import os,sys,string,time,commentjson
from csv import reader
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

import numpy as np

mycolors = {"ProtoDUNE":"blue","FD":"red","ND":"grey","Analysis":"orange","Total":"black"}
mydashes = {"ProtoDUNE":"solid","FD":"solid","ND":"solid","Analysis":"dashed","Total":"solid"}

def cumulate(a,lifetime=100):
  if lifetime < 1:
    return a*lifetime
  b = np.zeros(len(a))
  for i in range(0,len(a)):
    begin = max(0,i-lifetime+1)
    #print ("begin",begin,lifetime)
    for j in range(begin,i+1):
      b[i] += a[j]
  return b
  
def dump(n,k,a):
  s = ""
  s  += "%5s, %10s (%s)"%(n,k,Units[k])
  for j in range(0,len(a)):
    s += ", "
    s += "%8.1f"%a[j]
  s += "\n"
  return s
  
# for detector values
def DrawDet(Value,Years,Data,Types,Units,detcolors,detlines):
  
  fig=plt.figure()
  ax = fig.add_axes([0.2,0.2,0.7,0.7])
  ax.set_xlim(2018,2030)
  ax.spines['bottom'].set_position('zero')
  toplot = Data[Value]
  for type in Types:
    ax.plot(Years,toplot[type],color=detcolors[type],linestyle=detlines[type],label=type)
  ax.legend(frameon=False)
  ax.set_title(Value)
  ax.set_xlabel("Year")
  ax.set_ylabel(Value + ", " + Units[Value])
  plt.savefig(Value+".png",transparent=True)
  plt.show()
  
def DrawType(Value,Years,Data,Types,Units,typecolors,typelines):
  fig=plt.figure()
  ax = fig.add_axes([0.2,0.2,0.7,0.7])
  ax.set_xlim(2018,2030)
  ax.spines['bottom'].set_position('zero')
  for type in Types:
    print ("plot",type,Value)
    ax.plot(Years,Data[type][Value],color=typecolors[type],linestyle=typelines[type],label=type)
  ax.legend(frameon=False)

#ax.plot(Years,toplot["Total"],color='black')
  ax.set_xlabel("Year")
  ax.set_ylabel(Value + ", " + Units[Value])
  ax.set_title(Value)
  plt.savefig(Value+".png",transparent=True)
  plt.show()
  
#-------------------------------- main --------------------------------------
  
configfile = "Parameters.json"
if os.path.exists(configfile):
  with open(configfile,'r') as f:
    config = commentjson.load(f)
else:
  print ("no config file",configfile)
  sys.exit(0)
print (config)

# set up shortcuts for parameters

Years = np.array(config["Years"])
size = len(Years)

Units = config["Units"]

Detectors = config["Detectors"]

CombinedDetectors = config["CombinedDetectors"]

DetectorParameters = list(config["SP"].keys())

TapeLifetimes = config["TapeLifetimes"]

DiskLifetimes = config["DiskLifetimes"]

TapeCopies = config["TapeCopies"]

DiskCopies = config["DiskCopies"]

PerYear = config["PerYear"]

StorageTypes = list(TapeCopies.keys())

DetColors=config["DetColors"]
DetLines = config["DetLines"]
TypeColors=config["TypeColors"]
TypeLines = config["TypeLines"]

# build the inputs array

Inputs = {}

# read in the input values (Events and amount of commissioning in TB)
 
for det in ["SP","DP","ND","FD"]:
  Inputs[det]={}
  for type in ["Events","Test","Sim Events"]:
    Inputs[det][type] = np.array(config[det][type])
    
# use those to calculate CPU and space needs
    
for det in Detectors:
  print (Inputs[det])
  for key in DetectorParameters:
    if key in ["Events","Test","Sim Events"]:
      continue
    if not "Sim" in key:
      print
      Inputs[det][key]=Inputs[det]["Events"]*config[det][key]
    else:
      Inputs[det][key]=Inputs[det]["Sim Events"]*config[det][key]
      
# write some of this out

o = open("out.csv",'w')
o.write(dump("Year","Years",Years))

# use inputs to calculate per year sizes and store in transposed map Data

Data = {}
for i in Inputs["ND"].keys():
  Data[i] = {}
  for k in Inputs.keys():
    print (i,k,Inputs[k][i])
    Data[i][k] = Inputs[k][i] * float(PerYear[i])
    if Units[i] == "PB":
      Data[i][k] *= 0.001
    o.write(dump(k,i,Data[i][k]))

# look at the # of events

DrawDet("Events",Years,Data,Inputs.keys(),Units,DetColors,DetLines)

# combine ProtoDUNEs into one

for k in Data.keys():
  i = "ProtoDUNE"
  Data[k][i] = Data[k]["SP"] + Data[k]["DP"]
  Data[k].pop("SP")
  Data[k].pop("DP")
  o.write(dump(i,k,Data[k][i]))
  
# make a total CPU category
Data["Total-CPU"]={}

for k in CombinedDetectors:
  Data["Total-CPU"][k] =  Data["CPU"][k] + Data["Sim-CPU"][k]
  
# sum up data across detectors.

DataTypes = list(Data.keys())
for i in DataTypes:
  Data[i]["Total"] = np.zeros(size)
  for k in Data[i].keys():
    if k == "Total":
      continue
    Data[i]["Total"] += Data[i][k]
  
# assume analysis CPU = some multiplier of total sim + reco

Data["Total-CPU"]["Analysis"]= np.zeros(size)
for det in config["Analysis"]["Add"]:
  Data["Total-CPU"]["Analysis"]+= Data["Total-CPU"][det]
  
o.write(dump("Analysis","Total-CPU",Data["Total-CPU"]["Analysis"]))
  
# and put it in the total

Data["Total-CPU"]["Total"] += Data["Total-CPU"]["Analysis"]

# and make a special data type for cores

Data["Cores"] = {}
MHrsPerYear = 1000000./365/24
for k in Data["Total-CPU"].keys():
  efficiency = config["Cores"]["Efficiency"]
  scaleTo2020 = config["Cores"]["2020Units"]
  Data["Cores"][k] = Data["Total-CPU"][k]*MHrsPerYear/efficiency/scaleTo2020

# write out the totals

for k in Data.keys():
  print ("total:",k,Units[k], Data[k]["Total"])
  o.write(dump("Total",k,Data[k]["Total"]))


# now do some cumulative work.  Stuff stays on tape/disk for different amounts of time and we have multiple copies

Data["Total"] = {}
Data["Total"]["Cumulative Tape"] = 0
Data["Total"]["Cumulative Disk"] = 0
for k in StorageTypes:
  print ("storage",k)
  
  Data[k]["Tape"] = Data[k]["Total"]*TapeCopies[k]
  o.write(dump("Tape Copies",k,Data[k]["Tape"]))
  Data[k]["Disk"] = Data[k]["Total"]*DiskCopies[k]
  o.write(dump("Disk Copies",k,Data[k]["Disk"]))
  Data[k]["Cumulative Tape"] = cumulate(Data[k]["Tape"],TapeLifetimes[k])
  o.write(dump("Cumulative Tape",k,Data[k]["Cumulative Tape"]))
  Data[k]["Cumulative Disk"] = cumulate(Data[k]["Disk"],DiskLifetimes[k])
  o.write(dump("Cumulative Disk",k,Data[k]["Cumulative Disk"] ))
  Data["Total"]["Cumulative Tape"] += Data[k]["Cumulative Tape"]
  Data["Total"]["Cumulative Disk"] += Data[k]["Cumulative Disk"]
o.write(dump("Cumulative Tape","All",Data["Total"]["Cumulative Tape"] ))
o.write(dump("Cumulative Disk","All",Data["Total"]["Cumulative Disk"] ))

Types = ["ProtoDUNE","FD","ND","Analysis","Total"]
DrawDet("Total-CPU",Years,Data,Types,Units,DetColors,DetLines)
DrawDet("Cores",Years,Data,Types,Units,DetColors,DetLines)
DrawType("Cumulative Tape",Years,Data,StorageTypes+["Total"],Units,TypeColors,TypeLines)
DrawType("Cumulative Disk",Years,Data,StorageTypes+["Total"],Units,TypeColors,TypeLines)

