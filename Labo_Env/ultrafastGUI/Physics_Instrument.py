"Python Pipython wrapper for the GUI interface"
from tkinter import messagebox
from multiprocessing import Process
import time
import numpy as np
import serial
from math import floor


class LinearStage:
    """
    This class is used to wrap the pipython package from Physick Instrument to
    utilize their function and adapt it to a GUI interface. It allows a
    uniformatization of the different pipython devices. In a close futur
    this class will need subclasses that are specific to a given stage. With
    there own calibration and initialisation.

    Attributes:
        mainf : This is a tkinter object that represent the MainFrame if
        it exist when sent it is used to update the experiment window when
        used within the MainFrame.
        device : This is the pipython GCSDevice object that represent the
        Physick Intrument device.
        axes : This is the axis number that you can move you device with.
        It need an update to allow many axis stages that would allow dual
        axis mouvement.
        dev_name : This is a string representing the Device.

    """
    def __init__(self, mainf=None):
        """
        Constructor for the LinearStage class.

        Parameters:
            mainf : MainFrame object to be only passed if you have the
            Mainwindow and you want to update the experiment window.
        """
        self.mainf = mainf
        self.device = None
        self.axes = None
        self.dev_name = None

    def connect_identification(self, dev_name=None, dev_ip=None, exp_dependencie=False):
        """
        This function utilize the pipython package to connect the stage by
        scanning the available device plugged by usb or IP. If the usb mask
        exist among your devices it will connect it.

        Parameters :
            dev_name/dev_ip : This is a mask that will be used to disinguish
            your device from others connected to your computer. It is either
            your device name or the IP that it is linked to.
            exp_dependencie: This is a boolean value that tells the user
            interface if the user wants to update the experiement
            window.
        """
        if not dev_name and not dev_ip:
            return
        # Pipython :
        from pipython import GCSDevice
        from pipython import pitools
        # Determine the type of input was entered in tkinter entry box
        if (dev_name or dev_ip):
            pass
        else:
            return

        if (dev_name and type(dev_name)!=str):
            dev_name = dev_name.get()
        else:
            pass

        if (dev_ip and type(dev_ip)!=str):
            dev_ip = dev_ip.get()
        else:
            pass
        # Looking if the devices has adapted function
        dev_list = ['C-891', 'C-863.11', 'E-816']
        if dev_name not in dev_list:
            messagebox.showinfo(title='Error', message='This device is not in the device list please make sure it is' +
                                                       'compatible with the pipython software. If so add it to the list'
                                                       + 'at line 20 of the Physics_Instrument.py file')
            return
        # Follow the right procedure assigned to a specific device
        if dev_name:
            gcs = GCSDevice(dev_name)

            self.dev_name = dev_name

            # Case controller C-891
            if dev_name == dev_list[0]:
                devices = gcs.EnumerateUSB(mask=dev_name)
                if devices == []:
                    messagebox.showinfo(title='Error', message='It seems like there is no devices connected to your computer')
                    return
                gcs.ConnectUSB(devices[0])
                self.device = gcs
                self.axes = self.device.axes[0]
                self.device.EAX(self.axes, True)

            # Case controller C-863.12
            elif dev_name == dev_list[1]:
                gcs.ConnectUSB(serialnum = '0019550022')
                self.device = gcs
                self.axes = self.device.axes[0]
                self.device.SVO(self.axes, 1)


            # Case controller E-816
            elif dev_name == dev_list[2]:

                comPorts = self.find_active_com_ports()

                for ii, comPort in enumerate(comPorts):
                    try:
                        gcs.ConnectRS232(comPort,115200)
                        break
                    except:
                        pass
                self.device = gcs
                self.axes = self.device.axes[0]
                self.device.SVO(self.axes, 1)

            self.calibration(dev_name = dev_name)
            messagebox.showinfo(title='Physics Instrument', message='Device {} is connected.'.format(dev_name))
            self.device = gcs

        elif dev_ip:
            messagebox.showinfo(title='Physics Intrument', message='This option is not completed')

        # Verifying if the device needs to be sent to experiment window
        if self.mainf:
            experiments = self.mainf.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options('Physics_Linear_Stage')


    def scanning(self, min_pos=None, max_pos=None, iteration=None,
		         wtime=None, steps=None):
        """
        This is a function to do a simple scan n number of time from a min to
        a maximum position. This is not working well as a function
        because it blocks the gui from interacting sometimes. It can be use as
        a guideline and works well in that regard.

        Parameters:
            min_pos: This is a tkinter DoubleVar that correspond to the min
            position.
            max_pos: This is a tkinter DoubleVar that correspond to the max
            position.
            iteration: This is a tkinter IntVar that correspond to the number
            of iteration of interest.
            wtime: This is a tkinter DoubleVar that correspond to the waiting
            time @ a position 'x'.
            steps: This is a tkinter DoubleVar that correspond to the step
            size that your device should do.
        """
        if not self.device:
            return

        if not max_pos and not min_pos and not iteration:
            return

        # Pipython :
        from pipython import GCSDevice
        from pipython import pitools
        # Getting variables
        iteration = iteration.get()
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        wtime = wtime.get()
        steps = steps.get()

        # Getting the max and min possible value of the device
        maxp = self.device.qTMX(self.axes).get(str(self.axes))
        minp = self.device.qTMN(self.axes).get(str(self.axes))

        # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return
        # Defines the number of steps needed to do the full range
        nsteps = int(np.abs(max_pos - min_pos)/steps)
        for i in range(iteration):
            self.device.MOV(self.axes, min_pos)
            pitools.waitontarget(self.device)
            # Time given by user is in ms
            time.sleep(wtime/1000)
            pos = min_pos
            for step in range(nsteps):
                pos += steps
                self.device.MOV(self.axes, pos)
                pitools.waitontarget(self.device)
                time.sleep(wtime/1000)
            if self.device.qPOS(self.axes) != max_pos:
                self.device.MOV(self.axes, max_pos)

    def go_2position(self, position=None):
        """
        This function allows the user to move the stage that is connected to
        you computer on the axis taken of self.axis.

        Parameters:
            position: This is the position you want to order your stage to
            go to.
        """
        import pipython.pitools as pitools

        if (not self.device) or (position is None):
            return
        import pipython.pitools as pitools

        try:
            position = position.get()
        except:
            pass
        if self.dev_name == 'E-816':
            # Convert [-250,250] um input position to MOV() units for piezo
            position = (position + 250)/5 # -> Convert to [0,100] range

            correctedMax = 15.1608

            position = position * correctedMax / 100 # -> Convert to effective values for damaged piezo


        self.device.MOV(self.axes, position)
        pitools.waitontarget(self.device)

    def get_position(self):
        """
        This function allows the user to get the exact position of the stage
        that is returned with device precision.
        """
        position = self.device.qPOS(self.axes)[self.axes]
        if (not self.device) or (position is None):
            return


        if self.dev_name == 'E-816':
            # Convert qPOS() values to [-250,250] um range for piezo

            correctedMax = 15.1608

            position = position * 100 / correctedMax # -> Convert to [0,100] range


            position = position*5 - 250 # -> Convert to [-250,250] range

        return position


    def increment_move(self, position=None, increment=None,
                       direction = None):
        """
        This is a function to move by incrementation from the GUI it is
        based on the actual position and the increment given by the GUI.

        Parameters:
            position: This is the current position of the device.
            increment: This is the increment that is sent everytime you
            click on one of the arrow.
            direction: This is either positive or negative depending on
            the side of the arrow you are clicking.
        """
        if not self.device or not position:
            return
        # The orientation of the device is based on positive and negative of
        # the 891 stage. Maybe definition is different for other stage.
        import pipython.pitools as pitools
        position2 = position.get()
        increment = increment.get()
        if direction == 'left':
            increment = -increment
        else:
            pass
        position2 += increment
        position.set(position2)
        self.device.MOV(self.axes, position2)
        pitools.waitontarget(self.device)


    def change_speed(self, factor=None):
        """
        This is a way to change your device speed using the scroll bar.

        Parameters:
            factor: This is the scrollbar postion that discretize the
            speed of a device.
        """
        if not self.device or not factor:
            return
        factor = factor+1
        # The factor is a factor based on the maximum speed ie the minimum is 250 which is 1000/4 (scale is divided by 4
        # there could be more it just need to be changed in both of the program
        # 0 (the minimum) = 250
        # 1 : 500 ...
        self.device.VEL(self.axes, factor*10)

    def set_velocity(self, vel=None):
        """
        This function allows to change the velocity of your device while
        with precision.

        Parameters:
            vel: This is a tkinter DoubleVar that indicate the new speed of
            the device.
        """
        if not self.device or not vel:
            return
        vel = vel.get()
        # Controller E-816
        if self.dev_name == 'E-816':
            pass
        else:
            self.device.VEL(self.axes, vel)


    def calibration(self, dev_name):
        """
        This function allows the user to calibrate the device that was
        connected. It is called right after the connection or can be called
        afterward.

        Parameter:
            dev_name: This is the string of your device to allow the right
            calibration process.
        """
        if not self.device:
            return
        # Pipython :
        from pipython import GCSDevice

        dev_list = ['C-891', 'C-863.11', 'E-816']

        # Controller C-891
        if dev_name == dev_list[0]:
            self.device.FRF()
            i = 0
            while self.device.IsControllerReady() != 1:
                if i == 0:
                    messagebox.showinfo(message='Wait until the orange light is closed')
                    i += 1
            messagebox.showinfo(message='Device is ready')
            self.device.SVO(self.axes, 1)

        # Controller C-863.12
        if dev_name == dev_list[1]:
            self.device.FRF()
            i = 0
            while self.device.IsControllerReady() != 1:
                if i == 0:
                    messagebox.showinfo(message='Calibration in progress')
                    i += 1
            messagebox.showinfo(message='Device is ready')
        # Controller E-816
        if dev_name == dev_list[2]:
            messagebox.showinfo(message='Device is ready')

    def find_active_com_ports(self):
        """
        I invite the person that made this function to comment on it.
        """
        import serial.tools.list_ports
        comlist = serial.tools.list_ports.comports()
        connected = []
        for element in comlist:
            connected.append(element.device)
            connected[-1] = int(connected[-1][-1])
        return connected









# never wait for more than this e.g. during wait_states
MAX_WAIT_TIME_SEC = 10

# time to wait after sending a command. This number has been arrived at by
# trial and error
COMMAND_WAIT_TIME_SEC = 0.48

# States from page 65 of the manual
STATE_NOT_REFERENCED_FROM_RESET = '0A'
STATE_NOT_REFERENCED_FROM_CONFIGURATION = '0C'
STATE_READY_FROM_HOMING = '32'
STATE_READY_FROM_MOVING = '33'

STATE_CONFIGURATION = '14'

STATE_DISABLE_FROM_READY = '3C'
STATE_DISABLE_FROM_MOVING = '3D'
STATE_DISABLE_FROM_JOGGING = '3E'

class SMC100ReadTimeOutException(Exception):
  def __init__(self):
    super(SMC100ReadTimeOutException, self).__init__('Read timed out')

class SMC100WaitTimedOutException(Exception):
  def __init__(self):
    super(SMC100WaitTimedOutException, self).__init__('Wait timed out')

class SMC100DisabledStateException(Exception):
  def __init__(self, state):
    super(SMC100DisabledStateException, self).__init__('Disabled state encountered: '+state)

class SMC100RS232CorruptionException(Exception):
  def __init__(self, c):
    super(SMC100RS232CorruptionException, self).__init__('RS232 corruption detected: %s'%(hex(ord(c))))

class SMC100InvalidResponseException(Exception):
  def __init__(self, cmd, resp):
    s = 'Invalid response to %s: %s'%(cmd, resp)
    super(SMC100InvalidResponseException, self).__init__(s)

class SMC100(object):
  """
  Class to interface with Newport's SMC100 controller.
  The SMC100 accepts commands in the form of:
    <ID><command><arguments><CR><LF>
  Reply, if any, will be in the form
    <ID><command><result><CR><LF>
  There is minimal support for manually setting stage parameter as Newport's
  ESP stages can supply the SMC100 with the correct configuration parameters.
  Some effort is made to take up backlash, but this should not be trusted too
  much.
  The move commands must be used with care, because they make assumptions
  about the units which is dependent on the STAGE. I only have TRB25CC, which
  has native units of mm. A more general implementation will move the move
  methods into a stage class.
  """

  _port = None
  _smcID = None

  _silent = True

  _sleepfunc = time.sleep

  def __init__(self, smcID, port, backlash_compensation=True, silent=True, sleepfunc=None):
    """
    If backlash_compensation is False, no backlash compensation will be done.
    If silent is False, then additional output will be emitted to aid in
    debugging.
    If sleepfunc is not None, then it will be used instead of time.sleep. It
    will be given the number of seconds (float) to sleep for, and is provided
    for ease integration with single threaded GUIs.
    Note that this method only connects to the controller, it otherwise makes
    no attempt to home or configure the controller for the attached stage. This
    delibrate to minimise realworld side effects.
    If the controller has previously been configured, it will suffice to simply
    call home() to take the controller out of not referenced mode. For a brand
    new controller, call reset_and_configure().
    """

    super(SMC100, self).__init__()

    assert smcID is not None
    assert port is not None

    if sleepfunc is not None:
      self._sleepfunc = sleepfunc

    self._silent = silent

    self._last_sendcmd_time = 0

    print('Connecting to SMC100 on %s'%(port))

    self._port = serial.Serial(
        port = port,
        baudrate = 57600,
        bytesize = 8,
        stopbits = 1,
        parity = 'N',
        xonxoff = True,
        timeout = 0.50)

    self._smcID = str(smcID)

  def reset_and_configure(self):
    """
    Configures the controller by resetting it and then asking it to load
    stage parameters from an ESP compatible stage. This is then followed
    by a homing action.
    """
    self.sendcmd('RS',expect_response=False)

    self._sleepfunc(3)

    self.wait_states(STATE_NOT_REFERENCED_FROM_RESET, ignore_disabled_states=True)

    stage = self.sendcmd('ID', '?', True)
    print('Found stage', stage)

    # enter config mode
    self.sendcmd('PW', 1, expect_response=False)

    self.wait_states(STATE_CONFIGURATION)

    # load stage parameters
    self.sendcmd('ZX', 1, expect_response=False)

    # enable stage ID check
    self.sendcmd('ZX', 2, expect_response=False)

    # exit configuration mode
    self.sendcmd('PW', 0, expect_response=False)

    # wait for us to get back into NOT REFERENCED state
    self.wait_states(STATE_NOT_REFERENCED_FROM_CONFIGURATION)

  def home(self, waitStop=True):
    """
    Homes the controller. If waitStop is True, then this method returns when
    homing is complete.
    Note that because calling home when the stage is already homed has no
    effect, and homing is generally expected to place the stage at the
    origin, an absolute move to 0 um is executed after homing. This ensures
    that the stage is at origin after calling this method.
    Calling this method is necessary to take the controller out of not referenced
    state after a restart.
    """
    self.sendcmd('OR',expect_response=False)
    if waitStop:
      # wait for the controller to be ready
      st = self.wait_states((STATE_READY_FROM_HOMING, STATE_READY_FROM_MOVING))
      if st == STATE_READY_FROM_MOVING:
        self.move_absolute_um(0, waitStop=True)
    else:
      self.move_absolute_um(0, waitStop=False)

  def stop(self):
    self.sendcmd('ST')

  def get_status(self):
    """
    Executes TS? and returns the the error code as integer and state as string
    as specified on pages 64 - 65 of the manual.
    """

    resp = self.sendcmd('TS', '?', expect_response=True, retry=10)
    errors = int(resp[0:4], 16)
    state = resp[4:]

    assert len(state) == 2
    return errors, state

  def get_position_mm(self):
    dist_mm = float(self.sendcmd('TP', '?', expect_response=True, retry=10))
    return dist_mm

  def get_position_um(self):
    return int(self.get_position_mm()*1000)

  def move_relative_mm(self, dist_mm, waitStop=True):
    """
    Moves the stage relatively to the current position by the given distance given in mm
    If waitStop is True then this method returns when the move is completed.
    """
    self.sendcmd('PR', dist_mm, expect_response=False)
    if waitStop:
      # If we were previously homed, then something like PR0 will have no
      # effect and we end up waiting forever for ready from moving because
      # we never left ready from homing. This is why STATE_READY_FROM_HOMING
      # is included.
      self.wait_states((STATE_READY_FROM_MOVING, STATE_READY_FROM_HOMING))
    self._sleepfunc(1)



  def move_relative_um(self, dist_um, **kwargs):
    """
    Moves the stage relatively to the current position by the given distance given in um. The
    given distance is first converted to an integer.
    If waitStop is True then this method returns when the move is completed.
    """
    dist_mm = int(dist_um)/1000
    self.move_relative_mm(dist_mm, **kwargs)

  def move_absolute_mm(self, position_mm, waitStop=True):
    """
    Moves the stage to the given absolute position given in mm.
    If waitStop is True then this method returns when the move is completed.
    """
    self.sendcmd('PA', position_mm, expect_response=False)
    if waitStop:
      # If we were previously homed, then something like PR0 will have no
      # effect and we end up waiting forever for ready from moving because
      # we never left ready from homing. This is why STATE_READY_FROM_HOMING
      # is included.
      self.wait_states((STATE_READY_FROM_MOVING, STATE_READY_FROM_HOMING))
    self._sleepfunc(1)

  def move_absolute_um(self, position_um, **kwargs):
    """
    Moves the stage to the given absolute position given in um. Note that the
    position specified will be floor'd first before conversion to mm.
    If waitStop is True then this method returns when the move is completed.
    """
    pos_mm = floor(position_um)/1000
    return self.move_absolute_mm(pos_mm, **kwargs)

  def wait_states(self, targetstates, ignore_disabled_states=False):
    """
    Waits for the controller to enter one of the the specified target state.
    Controller state is determined via the TS command.
    If ignore_disabled_states is True, disable states are ignored. The normal
    behaviour when encountering a disabled state when not looking for one is
    for an exception to be raised.
    Note that this method will ignore read timeouts and keep trying until the
    controller responds.  Because of this it can be used to determine when the
    controller is ready again after a command like PW0 which can take up to 10
    seconds to execute.
    If any disable state is encountered, the method will raise an error,
    UNLESS you were waiting for that state. This is because if we wait for
    READY_FROM_MOVING, and the stage gets stuck we transition into
    DISABLE_FROM_MOVING and then STAY THERE FOREVER.
    The state encountered is returned.
    """
    starttime = time.time()
    done = False
    self._emit('waiting for states %s'%(str(targetstates)))
    while not done:
      waittime = time.time() - starttime
      if waittime > MAX_WAIT_TIME_SEC:
        raise SMC100WaitTimedOutException()

      try:
        errors, state = self.get_status()
        state=str(state)
        if state in targetstates:
          self._emit('in state %s'%(state))
          return state
        elif not ignore_disabled_states:
          disabledstates = [
              STATE_DISABLE_FROM_READY,
              STATE_DISABLE_FROM_JOGGING,
              STATE_DISABLE_FROM_MOVING]
          if state in disabledstates:
            raise SMC100DisabledStateException(state)

      except SMC100ReadTimeOutException:
        self._emit('Read timed out, retrying in 1 second')
        self._sleepfunc(1)
        continue

  def sendcmd(self, command, argument=None, expect_response=True, retry=10):
    """
    Send the specified command along with the argument, if any. The response
    is checked to ensure it has the correct prefix, and is returned WITHOUT
    the prefix.
    It is important that for GET commands, e.g. 1ID?, the ? is specified as an
    ARGUMENT, not as part of the command. Doing so will result in assertion
    failure.
    If expect_response is True, a response is expected from the controller
    which will be verified and returned without the prefix.
    If expect_response is True, and retry is True or an integer, then when the
    response does not pass verification, the command will be sent again for
    retry number of times, or until success if retry is True.
    The retry option MUST BE USED CAREFULLY. It should ONLY be used read-only
    commands, because otherwise REPEATED MOTION MIGHT RESULT. In fact some
    commands are EXPLICITLY REJECTED to prevent this, such as relative move.
    """
    assert command[-1] != '?'

    if self._port is None:
      return

    if argument is None:
      argument = ''

    prefix = self._smcID + command
    tosend = prefix + str(argument)

    # prevent certain commands from being retried automatically
    no_retry_commands = ['PR', 'OR','RS']
    if command in no_retry_commands:
      retry = False

    while self._port is not None:
      if expect_response:
        self._port.flushInput()

      self._port.flushOutput()

      self._port.write(str.encode(tosend))
      self._port.write(b'\r\n')

      self._port.flush()

      if not self._silent:
        self._emit('sent', tosend)

      if expect_response:
        try:
          response = self._readline()
          if response.startswith(prefix):
            return response[len(prefix):]
          else:
            raise SMC100InvalidResponseException(command, response)
        except Exception as ex:
          if not retry or retry <=0:
            raise ex
          else:
            if type(retry) == int:
              retry -= 1
            continue
      else:
        # we only need to delay when we are not waiting for a response
        now = time.time()
        dt = now - self._last_sendcmd_time
        dt = COMMAND_WAIT_TIME_SEC - dt
        if dt > 0:
          self._sleepfunc(dt)
        
        self._last_sendcmd_time = now
        return None

  def _readline(self):
    """
    Returns a line, that is reads until \r\n.
    OK, so you are probably wondering why I wrote this. Why not just use
    self._port.readline()?
    I am glad you asked.
    With python < 2.6, pySerial uses serial.FileLike, that provides a readline
    that accepts the max number of chars to read, and the end of line
    character.
    With python >= 2.6, pySerial uses io.RawIOBase, whose readline only
    accepts the max number of chars to read. io.RawIOBase does support the
    idea of a end of line character, but it is an attribute on the instance,
    which makes sense... except pySerial doesn't pass the newline= keyword
    argument along to the underlying class, and so you can't actually change
    it.
    """
    done = False
    line = str()
    while done == False:
      c = self._port.read()
      #print('c=',c)
      #print('decoded c=',c.decode('utf-8'))
      # ignore \r since it is part of the line terminator
      if len(c) == 0:
        raise SMC100ReadTimeOutException()
      elif c == b'\r':
        continue
      elif c == b'\n':
        done = True
      elif ord(c) > 32 and ord(c) < 127:
        line += str(c.decode('utf-8'))
      else:
        raise SMC100RS232CorruptionException(c)

    self._emit('read', line)

    return line

  def _emit(self, *args):
    if len(args) == 1:
      prefix = ''
      message = args[0]
    else:
      prefix = ' ' + args[0]
      message = args[1]

    if not self._silent:
      print('[SMC100' + prefix + '] ' + message)

  def close(self):
    if self._port:
      self._port.close()
      self._port = None

  def __del__(self):
    self.close()





