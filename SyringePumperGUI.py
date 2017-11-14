from SyringePumper import SyringePump
from Tkinter import *
import time
import threading

root = Tk()
root.title("AutoPump")
_width = 850
_height = 500
root.minsize(_width, _height)
crossArea = 707
stepsPerRev = 200
ratePerMin = 40000
totalValves = 2
valves = []
mu = u"\u03BC"
stopPressed = False
executeThread = threading.Thread()
def setParamsCallBack():
    paramWin = Toplevel()
    paramWin.title("Parameters")
    paramWin.resizable(0,0)
    params = Frame(paramWin)
    params.pack()
    L1 = Label(params, text="Syringe Cross Section Area")
    L1.grid(row=0, column=0)
    E1 = Entry(params, bd=5)
    E1.grid(row=0, column=1)
    E1.insert(0, str(crossArea))
    L4 = Label(params, text="Number of Valves")
    L4.grid(row=1, column=0)
    E2 = Entry(params, bd=5)
    E2.insert(0, str(totalValves))
    E2.grid(row=1, column=1)
    L5 = Label(params, text="Initial Valve")
    L5.grid(row=2, column=0)
    E3 = Entry(params, bd=5)
    E3.insert(0, "1")
    E3.grid(row=2, column=1)
    L2 = Label(params, text="Steps Per Revolution")
    L2.grid(row=3, column=0)
    var1 = StringVar()
    var1.set("200")
    spr = Spinbox(params, from_=48, to=200, wrap=True, textvariable=var1)
    spr.grid(row=3, column=1)
    L3 = Label(params, text="Default Microliters Per Minute")
    L3.grid(row=4, column=0)
    var2 = StringVar() 
    var2.set("40000")
    rpm = Spinbox(params, from_=60, to=100000, wrap=True, textvariable=var2)
    rpm.grid(row=4, column=1)
    options = Frame(paramWin, height=80)
    options.pack()
    submit = Button(options, text="Submit", command=lambda: submitParamsCallBack(paramWin, float(E1.get()), float(E3.get()), float(spr.get()), float(rpm.get()), float(E2.get())))
    submit.pack(expand=True)

    
def submitCommand1CallBack(micLit, dir, micLitPerMin, pos, sec, min, hour):
    output = ""
    if(dir == 1):
        output+="Infuse "
    else:
        output+="Extract "
    output+=str(micLit) + " " + mu + "L at " + str(micLitPerMin) + " " + mu + "L/min"
    if(sec!=0 or min!=0 or hour!=0):
        output+=" after "
        if(sec!=0):
            output+=str(sec) + " seconds "
        if(min!=0):
            output+=str(min) + " minutes "
        if(hour!=0):
            output+=str(hour) + " hours"
    if(pos == 0):
        qList.insert(END, output)
    else:
        qList.insert(0, output)
    rateEntry.delete(0, END)
    rateEntry.insert(0, ratePerMin)
    execute.config(state=NORMAL, relief=RAISED)
    clear.config(state=NORMAL, relief=RAISED)
    sp.addTaskMotor1(micLit, dir, micLitPerMin, pos, sec, min, hour)
    
def submitCommand2CallBack(valve, pos, sec, min, hour, reset):
    output = ""
    r = False
    if(reset==1):
        r = True
        output+="Reset Syringe Position"
    else:
        output+="Move to valve " + str(valve)
    if(sec!=0 or min!=0 or hour!=0):
        output+=" after "
        if(sec!=0):
            output+=str(sec) + " seconds "
        if(min!=0):
            output+=str(min) + " minutes "
        if(hour!=0):
            output+=str(hour) + " hours"
    if(pos == 0):
        qList2.insert(END, output)
    else:
        qList2.insert(0, output)
    execute.config(state=NORMAL, relief=RAISED)
    clear.config(state=NORMAL, relief=RAISED)
    sp.addTaskMotor2(valve, pos, sec, min, hour, r)
  
def submitParamsCallBack(paramWin, area, initVal, spr, rpm, valv):
    paramWin.destroy()
    valveParams = Toplevel()
    valveParams.title("Valve Locations")
    vp = Frame(valveParams)
    vp.pack()
    entryList = []
    totalValves = max(valv, 0)
    for i in range(totalValves):
        label = Label(vp,text="Valve " + str(i+1) + " Location (" + mu + "L)")
        label.grid(row=i, column=0)
        value = StringVar()
        loc = Entry(vp, bd=5, textvariable=value)
        loc.grid(row=i, column=1)
        entryList.append(value)
    subFrame = Frame(valveParams, height=80)
    subFrame.pack()
    submit = Button(subFrame, text="Submit", command=lambda: submitValvesCallback(valveParams, entryList))
    submit.pack(expand=True)
    crossArea = area
    if(spr > 200):
        stepsPerRev = 200
    elif(spr < 35):
        stepsPerRev = 35
    else:
        stepsPerRev = spr
    if(rpm < 60):
        ratePerMin = 60
    else:
        ratePerMin = rpm
    rateEntry.delete(0, END)
    rateEntry.insert(0, ratePerMin)
    aVar.set("Cross Section Area: " + str(crossArea) + " mm^2")
    sprVar.set("Steps Per Revolution: " + str(stepsPerRev))
    rpmVar.set("Default Microliters Per Minute: " + str(ratePerMin))
    valvVar.set("Number of Valves: " + str(totalValves))
    aDisp.config(textvariable=aVar)
    sprDisp.config(textvariable=sprVar)
    rpmDisp.config(textvariable=rpmVar)
    valvDisp.config(textvariable=valvVar)
    sp.setParams(spr, rpm)
    sp.setInitialValve(initVal)
    sp.setConversMotor1(area)
    sp.setConversMotor2(area)

def submitValvesCallback(valveWin, entryList):
    valveWin.destroy()
    for entry in entryList:
        valves.append(int(entry.get()))
    sp.setValveNums(totalValves, valves)
    
def createTimeFrame(frame):
    timeFrame = Frame(frame, width=_width/2)
    timeFrame.pack()
    dLabel = Label(timeFrame, text="Delay:")
    dLabel.grid(row=1, column=0)
    sLabel = Label(timeFrame, text="Seconds")
    sLabel.grid(row=1, column=1, padx=1)
    sEntry = Entry(timeFrame, bd=5, width=5)
    sEntry.insert(0, 0)
    sEntry.grid(row=1, column=2, padx=1)
    miLabel = Label(timeFrame, text="Minutes", pady=5)
    miLabel.grid(row=1, column=3, padx=1)
    miEntry = Entry(timeFrame, bd=5, width=5)
    miEntry.insert(0, 0)
    miEntry.grid(row=1, column=4, padx=1)
    hLabel = Label(timeFrame, text="Hours", pady=5)
    hLabel.grid(row=1, column=5, padx=1)
    hEntry = Entry(timeFrame, bd=5, width=5)
    hEntry.insert(0, 0)
    hEntry.grid(row=1, column=6, padx=1)
    return [sEntry, miEntry, hEntry]

def resetChecked():
    if(resetVar.get() == 1):
        valveVal.set("0")
        valve.config(state=DISABLED)
    else:
        valveVal.set("1")
        valve.config(state=NORMAL)
    
def displayCommand(motorNum):
    if(motorNum == 1):
        sm = sp._syringeMotor1
    event = sm._commandEvent1
    if(motorNum == 2):
        sm = sp._syringeMotor2
        event = sm._commandEvent2
    while(len(sm._taskQueue)!= 0):
        event.wait()
        if(sm.commandIndex != 0):
            prevComm = qList.get(sm.commandIndex-1).split("   ")[0]
            qList.delete(sm.commandIndex-1)
            qList.insert(sm.commandIndex-1, prevComm)
            qList.itemconfig(sm.commandIndex-1, bg="#ffffff")
        comm = qList.get(sm.commandIndex)
        qList.delete(sm.commandIndex)
        qList.insert(sm.commandIndex, comm + "    " + sm.commandStatus)
        qList.itemconfig(sm.commandIndex, bg="#66ff66")
        event.clear()
    lastComm = qList.get(sm.commandIndex).split("   ")[0]
    qList.delete(sm.commandIndex)
    qList.insert(sm.commandIndex, lastComm)
    qList.itemconfig(sm.commandIndex, bg="#ffffff")

def execute():
    stop.config(state=NORMAL, relief=RAISED)
    sp.execute()
    thread = threading.Thread(target=displayCommand, args=(1,))
    thread.start()
     
def stopFun(frame):
    sp.stop()
    cont.pack(expand=True, side=RIGHT)    

def contin(frame):
    frame.destroy()
    stopFrame = Frame(exFrame, bg="#00ff00")
    stopFrame.pack(expand=True)
    stop = Button(stopFrame, text="STOP", relief=SUNKEN, width=10, height=1, bd=4, state=DISABLED, command=lambda: stopFun(stopFrame))
    stop.pack()
    clear.pack(side=BOTTOM)
    stop.config(state=NORMAL, relief=RAISED)
    sp.execute()
    thread = threading.Thread(target=displayCommand, args=(1,))
    thread.start()

def clear():
    len1 = qList.size()
    len2 = qList2.size()
    qList.delete(0, END)
    qList2.delete(0, END)
    for i in range(0, len1-1):
        if(len(sp._syringeMotor1._taskQueue) != 0):
            sp.deleteTaskMotor1(i)
    for i in range(0, len2-1):
        if(len(sp._syringeMotor2._taskQueue) != 0):
            sp.deleteTaskMotor2(i)
    execute.config(state=DISABLED, relief=SUNKEN)
    clear.config(state=DISABLED, relief=SUNKEN)
    
#start paramFrame
paramFrame = Frame(root, height=_height/6)
paramFrame.pack(fill=X)
setParams = Button(paramFrame, text="Set Parameters", width=15, command = setParamsCallBack)
setParams.pack(side=LEFT, fill=Y)
aVar = StringVar()
aVar.set("Cross Section Area: " + str(crossArea) + " mm^2")
aDisp = Message(paramFrame, textvariable=aVar, justify=CENTER, bd=6, width=110)
aDisp.pack(side=LEFT, expand=True)
sprVar = StringVar()
sprVar.set("Steps Per Revolution: " + str(stepsPerRev))
sprDisp = Message(paramFrame, textvariable=sprVar, justify=CENTER, bd=6, width=130)
sprDisp.pack(side=LEFT, expand=True)
rpmVar = StringVar()
rpmVar.set("Default Microliters Per Minute: " + str(ratePerMin))
rpmDisp = Message(paramFrame, textvariable=rpmVar, justify=CENTER, bd=6, width=170)
rpmDisp.pack(side=LEFT, expand=True)
valvVar = StringVar()
valvVar.set("Number of Valves: " + str(totalValves))
valvDisp = Message(paramFrame, textvariable=valvVar, justify=CENTER, bd=6, width=100)
valvDisp.pack(side=LEFT, expand=True)
#end paramFrame

#start controlFrame
controlFrame = Frame(root, bg="#00ffff", bd=5, height=_height/2)
controlFrame.pack(fill=X)
#start syringe1Frame
syringe1Frame = Frame(controlFrame, bg="#00ff00", bd=5, width=_width/2, height=_height/2)
syringe1Frame.pack(side=LEFT)
#syringe1Frame.place(relx=.25-(25/_width))
s1Var =StringVar(value="Syringe 1")
s1Title = Message(syringe1Frame, textvariable=s1Var, justify=CENTER, width=100, relief=GROOVE, bd=5)
s1Title.pack()
commandParams = Frame(syringe1Frame, width=_width/2, bd=5)
commandParams.pack()
mLabel = Label(commandParams, text="Microliters")
mLabel.grid(row=0, column=0)
mEntry = Entry(commandParams, bd=5, width=7)
mEntry.grid(row=0, column=1)
mEntry.insert(0, 0)
placeVar = IntVar()
nextOpt = Radiobutton(commandParams, text="Add as Next", variable=placeVar, value=0)
nextOpt.grid(row=0, column=2)
nextOpt.select()
firstOpt = Radiobutton(commandParams, text="Add as First", variable=placeVar, value=1)
firstOpt.grid(row=0, column=3)
rateFrame = Frame(syringe1Frame, width=_width/2)
rateFrame.pack()
rateLabel = Label(rateFrame, text="Microliters Per Minute")
rateLabel.grid(column=0)
rateEntry = Entry(rateFrame, bd=5, width=4)
rateEntry.grid(row=0, column=1)
rateEntry.insert(0, ratePerMin)
dirVar = IntVar()
forwardOpt = Radiobutton(rateFrame, text="Infuse", variable=dirVar, value=1)
forwardOpt.grid(row=0, column=2)
forwardOpt.select()
backwardOpt = Radiobutton(rateFrame, text="Extract From Source", variable=dirVar, value=0)
backwardOpt.grid(row=0, column=3)
time = createTimeFrame(syringe1Frame)
addCommand1 = Button(syringe1Frame, text="Add Command", bd=3, command=lambda: submitCommand1CallBack(
    mEntry.get(), dirVar.get(), int(rateEntry.get()), placeVar.get(), int(time[0].get()), int(time[1].get()), int(time[2].get()))) #moved to next line for visibility
addCommand1.pack()
queueFrame = Frame(syringe1Frame, bd=5, width=_width/2)
queueFrame.pack()
qScroll = Scrollbar(queueFrame)
qScroll.pack(side=RIGHT, fill=Y)
qList = Listbox(queueFrame, width=65, yscrollcommand=qScroll.set)
qList.pack(side=LEFT, fill=BOTH)
qScroll.config(command=qList.yview)
#end syringe1Frame
#start syringe2Frame
syringe2Frame = Frame(controlFrame, bg="#00ff00", bd=5, width=_width/2, height=_height/2)
syringe2Frame.pack(side=RIGHT)
s2Var =StringVar(value="Syringe 2")
s2Title = Message(syringe2Frame, textvariable=s2Var, justify=CENTER, width=100, relief=GROOVE, bd=5)
s2Title.pack()
resetVar = IntVar()
resetCheck = Checkbutton(syringe2Frame, text="Reset Syringe", variable=resetVar, onvalue=1, offvalue=0, command=resetChecked)
resetCheck.pack()
valveParams = Frame(syringe2Frame, width=_width/2, bd=7)
valveParams.pack()
vLabel = Label(valveParams, text="Select Valve", padx=5)
vLabel.grid(row=0, column=0)
valveVal = StringVar()
valveVal.set("0")
valve = Spinbox(valveParams, from_=1, to=totalValves, wrap=True, bd=5, width=6, textvariable=valveVal)
valve.grid(row=0, column=1)
placeVar2 = IntVar()
nextOpt2 = Radiobutton(valveParams, text="Add as Next", variable=placeVar2, value=0)
nextOpt2.grid(row=0, column=2)
nextOpt2.select()
firstOpt2 = Radiobutton(valveParams, text="Add as First", variable=placeVar2, value=1)
firstOpt2.grid(row=0, column=3)
time2 = createTimeFrame(syringe2Frame)
addCommand2 = Button(syringe2Frame, text="Add Command", bd=3, command=lambda: submitCommand2CallBack(
    int(valve.get()), placeVar2.get(), int(time2[0].get()), int(time2[1].get()), int(time2[2].get()), resetVar.get()))
addCommand2.pack()
queueFrame2 = Frame(syringe2Frame, bd=5, width=_width/2)
queueFrame2.pack()
qScroll2 = Scrollbar(queueFrame2)
qScroll2.pack(side=RIGHT, fill=Y)
qList2 = Listbox(queueFrame2, width=65, yscrollcommand=qScroll2.set)
qList2.pack(side=LEFT, fill=BOTH)
qScroll2.config(command=qList2.yview)
#end syringe2Frame
#end controlFrame
#start exFrame
exFrame = Frame(root, bg="#12abff", bd=5)
exFrame.pack(fill=BOTH, expand=True)
execute = Button(exFrame, text="EXECUTE", relief=SUNKEN, width=10, height=1, bd=4, state=DISABLED, command=execute)
execute.pack(expand=True)
stopFrame = Frame(exFrame, bg="#00ff00")
stopFrame.pack(expand=True)
stop = Button(stopFrame, text="STOP", relief=SUNKEN, width=10, height=1, bd=4, state=DISABLED, command=lambda: stopFun(stopFrame)) #moved to next line for visibility
stop.pack(side=LEFT)
cont = Button(stopFrame, text="CONTINUE", width=10, height=1, bd=4, relief=RAISED, command=lambda: contin(stopFrame))
clear = Button(exFrame, text="CLEAR", relief=SUNKEN, width=10, height=1, bd=4, state=DISABLED, command=clear)
clear.pack(expand=True)
#end exFrame

sp = SyringePump(stepsPerRev=stepsPerRev, rpm=ratePerMin)

root.mainloop()
