import time
from class_NanoPZ import NanoPZ

port = 'COM3'
ctrl_no = 1
mypiezo = NanoPZ(port, ctrl_no)

print("ErrorCode "+mypiezo.getErrorCode())
print("HardwareID "+mypiezo.getHardwareID())
print("HardwareStatus "+mypiezo.getHardwareStatus())
print("ControllerStatus "+mypiezo.getControllerStatus())
print("MotorOn "+mypiezo.setMotorON())
print()
#print("Current Position "+mypiezo.getCurrentPosition())
#print("Position relative "+mypiezo.setPositionRelative(10))
#print("Current position "+mypiezo.getCurrentPosition())
#print("Position relative "+mypiezo.setPositionRelative(-10))
#print("Current Position "+mypiezo.getCurrentPosition())
print("Current Position "+mypiezo.getCurrentPosition())
#print("abspos: "+mypiezo.setAbsolutePosition(-550000))
#print("Current Position "+mypiezo.getCurrentPosition())

print(float(mypiezo.getCurrentPosition()[5:])*0.01)
print("Current Position "+mypiezo.setAbsolutePosition(5000/0.01))
print(float(mypiezo.getCurrentPosition()[5:])*0.01)
#print(mypiezo.setMotorOFF())
#print(mypiezo.getErrorCode())


