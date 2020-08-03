import os
import threading

from pcaspy import Driver, SimpleServer, Severity

DETECTOR_ID = 0

prefix = '13PIXET:cam1:'
pvdb = {
    # detector info
    'Model_RBV': {'type': 'str'},
    'MaxSizeX_RBV':  {'type': 'int'},
    'MaxSizeY_RBV':  {'type': 'int'},
    # acquisition control and status
    'Acquire': {
        'type': 'enum',
        'enums': ['Stop', 'Start'],
        'asyn': True
    },
    'AcquireTime':              {'units': 's', 'prec':  2, 'value': 0.1},
    'NumImages':                {'type': 'int', 'value': 1},

    # image data descriptors, areaDetector NDPluginStdArrays compatible
    'NDimensions_RBV': {'type': 'int', 'value': 3},
    'Dimensions_RBV':  {'type': 'int', 'count': 3},
    'DataType_RBV':    {'type': 'enum', 'enums': ['Int8','UInt8','Int16','UInt16','Int32','UInt32'], 'value': 5},
    'ArraySizeX_RBV':  {'type': 'int'},
    'ArraySizeY_RBV':  {'type': 'int'},
    'ArraySizeZ_RBV':  {'type': 'int'},
    'ArrayData':       {'type': 'int', 'count': 6553600},
    'ColorMode_RBV':   {'type': 'enum', 'enums': ['Mono'], 'value': 0},

    # file saving control, areaDetector NDFile compatible
    'FilePath':           {'type': 'char', 'count': 128},
    'FileName':           {'type': 'char', 'count': 128, 'value': 'test'},
    'FileNumber':         {'type': 'int'},
    'FileTemplate':       {'type': 'str', 'value': '%s_%04d.h5'},
    'AutoIncrement':      {'type': 'enum', 'enums': ['No', 'Yes'], 'value': 1},
    'AutoSave':           {'type': 'enum', 'enums': ['No', 'Yes'], 'value': 1},
    'FullFileName_RBV':   {'type': 'char', 'count': 256},
    'FilePathExists_RBV': {'type': 'enum', 'enums': ['No', 'Yes'],
        'states': [Severity.MAJOR_ALARM, Severity.NO_ALARM]
    },
}


class PixetDriver(Driver):
    def __init__(self):
        Driver.__init__(self)
        self.tid = None
        self.images = None
        self.device = pixet.devices()[DETECTOR_ID]
        self.setParam('Model_RBV', self.device.fullName())
        self.setParam('MaxSizeX_RBV', self.device.width())
        self.setParam('MaxSizeY_RBV', self.device.height())

    def write(self, reason, value):
        status = True
        # take proper actions
        if reason == 'Acquire':
            self.setParam(reason, value)
            if self.tid is None and value == 1:
                self.tid = threading.Thread(target=self.runAcquisition)
                self.tid.start()
            if self.device.isBusy() and value == 0:
                self.device.abortOperation()
        elif reason == 'FilePath':
            self.setParam('FilePathExists_RBV',
                    os.path.exists(value) and os.access(value, os.W_OK))
        elif reason.endswith('_RBV'):
            status = False

        # store the values
        if status:
            self.setParam(reason, value)
        self.updatePVs()
        return status

    def dataCallback(self, value):
        print(value)
        # get data
        frame = self.device.lastAcqFrameRefInc()
        data = frame.data()
        frame.destroy()
        # areaDetector describes image as column, row, layer
        shape = (self.device.width(), self.device.height())
        self.setParam('NDimensions_RBV', len(shape))
        self.setParam('Dimensions_RBV', shape)
        self.setParam('ArrayData', data)
        self.setParam('ArraySizeX_RBV', shape[0])
        self.setParam('ArraySizeY_RBV', shape[1])
        self.setParam('ArraySizeZ_RBV', 0)

    def runAcquisition(self):
        acqTime = self.getParam('AcquireTime')
        frames = self.getParam('NumImages')
        path = self.getParam('FilePath')
        name = self.getParam('FileName')
        number = self.getParam('FileNumber')
        template = self.getParam('FileTemplate')
        increment = self.getParam('AutoIncrement')
        auto_save = self.getParam('AutoSave')

        fullFileName = os.path.join(path, template % (name, number))
        self.setParam('FullFileName_RBV', fullFileName)

        # register data callback
        self.device.registerEvent(pixet.PX_EVENT_ACQ_FINISHED, self.dataCallback, self.dataCallback)
        # acquire (blocking)
        self.device.doSimpleAcquisition(frames, acqTime, pixet.PX_FTYPE_AUTODETECT, fullFileName)
        # unregister data callback
        self.device.unregisterEvent(pixet.PX_EVENT_ACQ_FINISHED, self.dataCallback, self.dataCallback)

        if increment:
            self.setParam('FileNumber', number + 1)

        self.setParam('Acquire', 0)
        self.callbackPV('Acquire')
        self.updatePVs()

        self.tid = None

abort = False
def onAbort():
    global abort
    abort = True

# kill the server
def exitCallback(value):
    onAbort()

if __name__ == '__main__':
    server = SimpleServer()
    server.createPV(prefix, pvdb)
    driver = PixetDriver()

    pixet.registerEvent("Exit", exitCallback, exitCallback)
    while not abort:
        server.process(0.1)
    # since Pixet could start/stop the server
    # make sure we start as new each time.
    pixet.unregisterEvent("Exit", exitCallback, exitCallback)
    del driver
    del server

