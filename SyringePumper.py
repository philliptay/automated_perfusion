from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_StepperMotor

import time
import atexit
import threading
from collections import deque
from math import exp

#Define class for SyringePump object: handling two syringe motors
class SyringePump(object):
    def __init__(self, stepperId1=1, stepperId2=2, stepsPerRev=200, rpm=40000, addr=0x60, stopAtExit=True):
        #Initialize syringe motors and threads
        self._syringeMotor1 = SyringeMotor(stepperId1, False, stepsPerRev, rpm, addr, stopAtExit)
        self._syringeMotor2 = SyringeMotor(stepperId2, True, stepsPerRev, rpm, addr, stopAtExit)
        self._motor1Thread = threading.Thread()
        self._motor2Thread = threading.Thread()
        #Configure to stop at program exit (Extra insurance)
        if stopAtExit:
            atexit.register(self.stop)

    #set parameters after initialization
    def setParams(self, spr, rpm):
        self._syringeMotor1.setParams(spr, rpm)
        self._syringeMotor2.setParams(spr, rpm)        

    #execute tasks for both motors in one thread
    def execute(self, sec1=0, min1=0, hour1=0, sec2=0, min2=0, hour2=0):
      if(not self._motor2Thread.isAlive() and len(self._syringeMotor2._taskQueue) != 0):
          self._motor2Thread = threading.Thread(target=self._syringeMotor2.executeTasks, args=(sec2, min2, hour2))
          self._motor2Thread.start()
      if(not self._motor1Thread.isAlive() and len(self._syringeMotor1._taskQueue) != 0):
          self._motor1Thread = threading.Thread(target=self._syringeMotor1.executeTasks, args=(sec1, min1, hour1))
          self._motor1Thread.start()

    #set conversion from microliters to microsteps for motor 1
    def setConversMotor1(self, crossSecArea):
        self._syringeMotor1.setConvers(crossSecArea)

    #set conversion from microliters to microsteps for motor 2
    def setConversMotor2(self, crossSecArea):
        self._syringeMotor2.setConvers(crossSecArea)

    #set initial valve
    def setInitialValve(self, valveNum):
        self._syringeMotor2.setInitialValve(valveNum)
    
    #set parameters for valves
    def setValveNums(self, total, dist):
        self._syringeMotor2.setValveNums(total, dist)

    #add task to motor one, either to the top or bottom
    def addTaskMotor1(self, microLiters, direct, micLitPerMin=0, pos=0, sec=0, min=0, hour=0):
        if(pos == 1):
            self._syringeMotor1.addTaskToTop(microLiters, direct, micLitPerMin, sec, min, hour)
        elif(pos == 0):
            self._syringeMotor1.addTaskToBottom(microLiters, direct, micLitPerMin, sec, min, hour)

    #add task to motor two, either to the top or bottom
    def addTaskMotor2(self, valveNum, pos=0, sec=0, min=0, hour=0, r=False):
        if(pos == 1):
            self._syringeMotor2.addTaskToTop(valveNum=valveNum, sec=sec, min=min, hour=hour, reset=r)
        elif(pos == 0):
            self._syringeMotor2.addTaskToBottom(valveNum=valveNum, sec=sec, min=min, hour=hour, reset=r)

    #delete task from motor 1
    def deleteTaskMotor1(self, pos):
        self._syringeMotor1.deleteTask(pos)

    #delete task from motor 2
    def deleteTaskMotor2(self, pos):
        self._syringeMotor2.deleteTask(pos)
            
    #stop the syringe pump (called upon exit)
    def stop(self):
        self._syringeMotor1.kill()
        self._syringeMotor2.kill()

#Define class for a SyringeMotor object: syringe pumping capabilities implemented for a stepper motor
class SyringeMotor(object):
    motorMoving = threading.Condition()
    availableMove = True
    #Constant intrinsic to syringe motor: number of microsteps required to move a linear distance of 1 mm
    MICROSTEPS_PER_MM = 317.95
    #Constructor for SyringeMotor object
    def __init__(self, stepperId, isValveSyringe, stepsPerRev=200, mi_rpm=40000, addr=0x60, stopAtExit=True):
        #Initialize motor HAT and stepper motor with frequency and speed
        self._mh = Adafruit_MotorHAT(addr)
        self._stepper = self._mh.getStepper(stepsPerRev, stepperId)
        self._spr = stepsPerRev
        self._mi_rpm = mi_rpm
        self._stepperId = stepperId
        self._taskQueue = deque([])
        self._execThread = threading.Thread()
        self._commandEvent1 = threading.Event()
        self._commandEvent2 = threading.Event()
        self._isValveSyringe = isValveSyringe
        self.MICROSTEP_PER_MICROLITER = 0.45
        self.SINGLE_STEP_LIMIT = 64
        self.INTERLEAVE_STEP_LIMIT = 32
        self.VALVE_TOT = 6
        self.valvePositions = []
        self.currentValveNum = 0
        self.executing = False
        self.commandIndex = 0
        self.timeToDie = False
        self.commandStatus = "(currently executing)"
        #Start with motor off, and configure motor to stop at program exit
        self._mh.getMotor(stepperId).run(Adafruit_MotorHAT.RELEASE)
        if stopAtExit:
            atexit.register(self.stop)

    #set parameters after initialization
    def setParams(self, spr, rpm):
        self._stepper = self._mh.getStepper(spr, self._stepperId)
        self._mi_rpm = rpm

    #set the conversion from microliters to microsteps, given a cross section area of syringe
    def setConvers(self, crossSecArea):
        self.MICROSTEP_PER_MICROLITER = SyringeMotor.MICROSTEPS_PER_MM/crossSecArea
        self._stepper.setSpeed(self._mi_rpm*self.MICROSTEP_PER_MICROLITER/self._spr)

    #set the number of valves on syringe
    def setValveNums(self, total, dists):
        self.VALVE_TOT = total
        self.valvePositions = dists

    #set the initial valve position
    def setInitialValve(self, valveNum):
        self.currentValveNum = valveNum

    #move to a specific valve
    def moveToValve(self, valveNum=0, s=0, m=0, h=0, reset=False):
        if(reset==True):
            self.move(1.5*self.valvePositions[self.VALVE_TOT-1], 0, sec=s, min=m, hour=h)
            self.currentValveNum = 0
        else:
            distToMove = 0
            if(self.currentValveNum==0):
                distToMove = self.valvePositions[valveNum-1]
            else:
                distToMove = self.valvePositions[valveNum-1] - self.valvePositions[self.currentValveNum-1]
            if(distToMove > 0):
                self.move(distToMove, 1, sec=s, min=m, hour=h)
            else:
                self.move(abs(distToMove), 0, sec=s, min=m, hour=h)
            self.currentValveNum = valveNum

    #move a quantity of microliters
    def move(self, microLiters, direct, micLitPerMin=40000, sec=0, min=0, hour=0):
        if(sec != 0 or min != 0 or hour !=0):
            time.sleep(sec + min*60 + hour*3600)
        SyringeMotor.availableMove = False
        SyringeMotor.motorMoving.acquire()
        if(direct == 0):
            dir = Adafruit_MotorHAT.FORWARD
        elif(direct == 1):
            dir = Adafruit_MotorHAT.BACKWARD
        microStepsLeft =  float(microLiters)*self.MICROSTEP_PER_MICROLITER
        #RPM of stepper motor if syringe apparatus had no friction
        theoreticalRPM = int(micLitPerMin*self.MICROSTEP_PER_MICROLITER/self._spr)
        #Equation for converting the theoretical RPM parameter to the real RPM, due to friction of the apparatus
        realRPM = int(24*(1-exp(-.0185*theoreticalRPM)))
        self._stepper.setSpeed(theoreticalRPM*theoreticalRPM/realRPM)
        halfStep = False
        if(abs(microStepsLeft - int(microStepsLeft)) > .25 and abs(microStepsLeft - int(microStepsLeft)) < 1):
            halfStep = True
        microStepsLeft = int(microStepsLeft)
        if(self.timeToDie):
            return
        self._stepper.step(microStepsLeft, dir, Adafruit_MotorHAT.SINGLE)
        microStepsLeft = 0
        if(halfStep):
            self._stepper.oneStep(dir, Adafruit_MotorHAT.INTERLEAVE)
        if(microStepsLeft == 0):
            self.stop()
        SyringeMotor.motorMoving.notify()
        SyringeMotor.motorMoving.release()
        SyringeMotor.availableMove = True

    def isMoveAvailable(self):
        if SyringeMotor.availableMove:
            return True
        else:
            return False
         
    #add a task to be executed first
    def addTaskToTop(self, microLiters=0, direct=1, micLitPerMin=0, sec=0, min=0, hour=0, valveNum=0, reset=False):
        if(micLitPerMin==0):
            micLitPerMin = self._mi_rpm
        if(self._isValveSyringe):
            args = [valveNum, sec, min, hour, reset]
        else:
            args = [microLiters, direct, micLitPerMin, sec, min, hour]
        self._taskQueue.appendleft(args)

    #add a task to be executed last
    def addTaskToBottom(self, microLiters=0, direct=1, micLitPerMin=0, sec=0, min=0, hour=0, valveNum=0, reset=False):
        if(micLitPerMin==0):
            micLitPerMin = self._mi_rpm
        if(self._isValveSyringe):
            args = [valveNum, sec, min, hour, reset]
        else:
            args = [microLiters, direct, micLitPerMin, sec, min, hour]
        self._taskQueue.append(args)

    #delete a task at specified position in queue
    def deleteTask(self, position):
        self._taskQueue.rotate(-position)
        self._taskQueue.popleft()
        self._taskQueue.rotate(position)

    #execute the tasks by iterating through queue, optional delay time
    def executeTasks(self, sec=0, min=0, hour=0):
        if(sec != 0 or min != 0 or hour !=0):
            time.sleep(sec + min*60 + hour*3600)
        if not self.executing:
            self.executing = True
            while(len(self._taskQueue) != 0):
                if(self.timeToDie):
                    return
                args = self._taskQueue.popleft()
                SyringeMotor.motorMoving.acquire()
                while not self.isMoveAvailable():
                    self.commandStatus = "(awaiting executing)"
                    SyringeMotor.motorMoving.wait()
                self.commandStatus = "(currently executing)"
                if(self._isValveSyringe):
                    self._commandEvent2.set()
                    self.moveToValve(args[0], args[1], args[2], args[3], args[4])
                    self._commandEvent2.clear()
                else:
                    self._commandEvent1.set()
                    self.move(args[0], args[1], args[2], args[3], args[4], args[5])
                    self._commandEvent1.clear()
                SyringeMotor.motorMoving.release()
                self.commandIndex+=1  
        else:
            print("Queue is already executing.")
        self.executing = False

    def kill(self):
        if(self.executing):
            self.timeToDie=True
        self.stop()


    #stop the motor (atexit.register requires a function parameter)
    def stop(self):
        self._mh.getMotor(self._stepperId).run(Adafruit_MotorHAT.RELEASE)
