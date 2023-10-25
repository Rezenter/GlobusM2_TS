import win32com.client
import msgpack

db_path: str = '//192.168.10.41/d/data/db/'

class Sensor:
    diffuser: int = 1  # diffuser (0, ('N/A',))
    measurement_mode: int = 1  # MeasMode (1, ('Power', 'Energy'))
    pulse_length: int = 0 # PulseLengths (0, ('30uS', '1.0mS'))
    measurement_range: int = 2  #Ranges (2, ('10.0J', '2.00J', '200mJ', '20.0mJ', '2.00mJ', '200uJ'))
    wavelength: int = 3  #Wavelengths (3, (' 193', ' 248', ' 532', '1064', '2100', '2940'))

    def __init__(self):
        self.OphirCOM = None
        self.DeviceHandle = None
        self.connected: bool = False
        self.ready: bool = False
        self.armed: bool = False
        self.is_plasma: bool = False
        self.shotn: int = 0

    def status(self) -> int:
        if not self.connected:
            return -1
        if self.armed:
            return 1
        if not self.ready:
            return 2
        return 0

    def connect(self):
        print('Ophir connecting...')
        self.connected = False
        self.ready = False
        self.armed = False
        self.OphirCOM = win32com.client.Dispatch("OphirLMMeasurement.CoLMMeasurement")
        # Stop & Close all devices
        self.OphirCOM.StopAllStreams()
        self.OphirCOM.CloseAll()
        # Scan for connected Devices
        DeviceList = self.OphirCOM.ScanUSB()
        if len(DeviceList) == 0:
            print('\n\nOphir failed!!! zero devices\n\n')
            return False
        Device = DeviceList[0]
        self.DeviceHandle = self.OphirCOM.OpenUSBDevice(Device)  # open first device
        exists = self.OphirCOM.IsSensorExists(self.DeviceHandle, 0)
        if exists:
            print('diffuser', self.OphirCOM.GetDiffuser(self.DeviceHandle, 0))
            print('MeasMode', self.OphirCOM.GetMeasurementMode(self.DeviceHandle, 0))
            print('PulseLengths', self.OphirCOM.GetPulseLengths(self.DeviceHandle, 0))
            print('Ranges', self.OphirCOM.GetRanges(self.DeviceHandle, 0))
            print('Wavelengths', self.OphirCOM.GetWavelengths(self.DeviceHandle, 0))

            #self.OphirCOM.StopStream(self.DeviceHandle, 0)
            #self.OphirCOM.SetDiffuser(self.DeviceHandle, 0, self.diffuser)
            self.OphirCOM.SetMeasurementMode(self.DeviceHandle, 0, self.measurement_mode)
            self.OphirCOM.SetPulseLength(self.DeviceHandle, 0, self.pulse_length)
            self.OphirCOM.SetRange(self.DeviceHandle, 0, self.measurement_range)
            self.OphirCOM.SetWavelength(self.DeviceHandle, 0, self.wavelength)
            self.connected = True
            self.ready = True
            print('Ophir connect OK')
            return True
        print('\n\nOphir failed!!!\n\n')

    def arm(self, is_plasma=False, shotn=0):
        self.is_plasma = is_plasma
        self.shotn = shotn
        if self.connected and self.ready:
            exists = self.OphirCOM.IsSensorExists(self.DeviceHandle, 0)
            if exists:
                self.OphirCOM.StartStream(self.DeviceHandle, 0)  # start measuring
                self.ready = False
                self.armed = True
                #print('Armed OK')
                return True
            print('Not exists!')
        else:
            print('Sensor is not connected!')
        return False

    def disarm(self) -> list[(float, float)]:
        if self.connected and self.armed:
            exists = self.OphirCOM.IsSensorExists(self.DeviceHandle, 0)
            if exists:
                self.ready = False
                self.armed = False
                data = self.OphirCOM.GetData(self.DeviceHandle, 0)
                self.OphirCOM.StopStream(self.DeviceHandle, 0)

                events: list[(float, float)] = []
                for i in range(0, len(data[0]), 2):
                    events.append((data[1][i] - data[1][0], data[0][i]))
                self.ready = True
                #print('Disarmed OK')
                return events
            print('Not exists!')
        else:
            print('Sensor is not connected!')
        return []

    def __del__(self):
        if self.OphirCOM is not None:
            self.OphirCOM.StopAllStreams()
            self.OphirCOM.CloseAll()
            self.OphirCOM = None
class Ophir:
    HOST = '192.168.10.55'
    PORT = 8888
    SOCK_TIMEOUT = 1  # timeout for network operations
    BUFFER_SIZE = 64
    ENCODING = 'utf-8'
    sensor: Sensor = Sensor()
    def connect(self):
        self.sensor.connect()

    def status(self) -> dict:
        res = {
            'ok': False,
            'connected': False,
            'ready': False,
            'armed': False
        }

        status = self.sensor.status()
        if status == 0:
            res['connected'] = True
            res['ready'] = True
            res['armed'] = False
        elif status == 1:
            res['connected'] = True
            res['ready'] = False
            res['armed'] = True
        elif status == 2:
            res['connected'] = True
            res['ready'] = False
            res['armed'] = False
        else:
            res['connected'] = False
            res['ready'] = False
            res['armed'] = False
        return res

    def arm(self, is_plasma: bool, shotn: int):
        self.sensor.arm(is_plasma=is_plasma, shotn=shotn)

    def disarm(self):
        if self.sensor.armed:
            meas = self.sensor.disarm()
            path = db_path
            if self.sensor.is_plasma:
                path += 'plasma/'
            else:
                path += 'debug/'
            path += 'ophir/%05d.msgpk' % self.sensor.shotn
            with open(path, 'wb') as file:
                if len(meas) > 0:
                    msgpack.dump(meas, file)
            print('Ophir got %d shots' % len(meas))
        else:
            print('Ophir is not armed')
