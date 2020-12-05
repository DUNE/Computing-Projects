#Docdb 20515
import os,sys,string,time
from csv import reader

import numpy as np

def cummulate(a,lifetime=100):
  if lifetime < 1:
    return a*lifetime
  b = np.zeros(len(a))
  for i in range(0,len(a)):
    begin = max(0,i-lifetime+1)
    print ("begin",begin,lifetime)
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
  

Years = np.array([2018,2019,2020,2021,2022,2023,2024,2025,2026,2027,2028,2029,2030])
size = len(Years)
Units = {"Events":"M", "Raw":"TB", "Test":"TB","Reco":"TB","CPU":"MHr","Sim Events":"M","Sim":"TB","Sim-CPU":"MHr","All":"TB"}
TapeLifetimes = {"Raw":100,"Test":.5,"Reco":15,"Sim":15}
DiskLifetimes = {"Raw":1,"Test":.5,"Reco":2,"Sim":2}
TapeCopies = {"Raw":2,"Test":.5,"Reco":1,"Sim":1}
DiskCopies = {"Raw":1,"Test":.5,"Reco":2,"Sim":2}
PerYear = {"Raw":1,"Test":1,"Reco":2,"Sim":1,"Events":1,"Sim Events":1,"CPU":2,"Sim-CPU":1}

StorageTypes = ["Raw","Test","Reco","Sim"]
Inputs = {}
 

data = []
file = open("Numbers-2020-11-28.csv",'r')
for line in reader(file):
  if line[1] == "Year":
    continue
  print (line)
  if line[0] == "":
    continue
  data = []
  if (line[0] not in Inputs):
    Inputs[line[0]] = {}
  for i in range(2,15):
    if line[i] == '':
      break
    data.append(float(line[i]))
    
  print (data)
  Inputs[line[0]][line[1]] = np.array(data)
  print (line[0], line[1], Inputs[line[0]][line[1]])

o = open("out.csv",'w')
Totals = {}
for k in Inputs["ND"].keys():
  Totals[k] = np.zeros(size)



for i in Inputs.keys():
  for k in Inputs[i].keys():
   # print ("%d%di,k, len(Inputs[i][k]))
    Totals[k] = Totals[k] + Inputs[i][k]*PerYear[k]
    o.write(dump(i,k,Inputs[i][k]))
#  for j in Inputs[i]:
##    print  (i, j, len(Inputs[i][j]), Inputs[i][j])
#    o.write ("%4s, %10s (%3s)"%(i,j,Units[j]))
#
#    for k in range(0,size):
#      o.write(", ")
#      o.write ("%8.1f"%Inputs[i][j][k])
#    o.write("\n")
    


for k in Totals:
  print ("total:",k,Units[k], Totals[k])
  o.write(dump("Total",k,Totals[k]))
#  o.write ("Total %10s (%3s)"%(k,Units[k]))
#  for j in range(0,size):
#    o.write(", ")
#    o.write ("%8.1f"%Totals[k][j])
#  o.write("\n")
  
Tape = {}
CummulativeTape = {}
Disk = {}
CummulativeDisk = {}
#Tape["Raw"] = Totals["Raw"]*2
#CummulativeTape["Raw"] = cummulate(Tape["Raw"],100)
#o.write(dump("Tape","Raw",CummulativeTape["Raw"]))
#Tape["Reco"] = Totals["Reco"]
#CummulativeTape["Reco"] = cummulate(Tape["Reco"],2)
TotalTape = np.zeros(size)
TotalDisk = np.zeros(size)

for k in StorageTypes:
  Tape[k] = Totals[k]*TapeCopies[k]
  o.write(dump("Tape Copies",k,Tape[k]))
  Disk[k] = Totals[k]*DiskCopies[k]
  o.write(dump("Disk Copies",k,Disk[k]))
  CummulativeTape[k] = cummulate(Tape[k],TapeLifetimes[k])
  o.write(dump("Cummulative Tape Copies",k,CummulativeTape[k]))
  CummulativeDisk[k] = cummulate(Disk[k],DiskLifetimes[k])
  o.write(dump("Cummulative Disk Copies",k,CummulativeDisk[k]))
  TotalTape += CummulativeTape[k]
  TotalDisk += CummulativeDisk[k]
o.write(dump("Cummulative Tape","All",TotalTape))
o.write(dump("Cummulative Disk","All",TotalDisk))
  
