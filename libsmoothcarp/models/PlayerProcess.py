from multiprocessing import Process, Queue
from ao import AudioDevice
from mad import MadFile
from urllib2 import urlopen
from Queue import Empty
from time import sleep


def _process_run(command_queue):
    audio_device = AudioDevice('pulse')
    action = None
    target = None
    buffer = None
    paused = False
    while action is not False:
        try:
            action = command_queue.get()
            print 'Got action: %s' % str(action)
        except Empty:
            print 'No action'
            print repr(action)
            pass
        if action is PlayerProcess.CMD_DIE:
            print 'Dying'
            target = None
            buffer = None
            paused = False
            action = False
            continue
        elif action is PlayerProcess.CMD_STOP:
            print 'Stopping'
            target = None
            buffer = None
            paused = False
        elif action is PlayerProcess.CMD_PAUSE and target is not None:
            print 'Pausing'
            paused = True
        elif isinstance(action, str):
            print 'Setting new target'
            #target = MadFile(urlopen(action))
            target = MadFile(open('/home/aheadley/devel/smoothcarp/run_away.mp3', 'rb'))
        elif (action is PlayerProcess.CMD_PLAY and target is not None) or \
            (action is None and target is not None):
            print 'Trying to play'
            buffer = target.read()
            if buffer is not None:
                print 'Playing: %i bytes' % len(buffer)
                audio_device.play(buffer)
            else:
                print 'Song ended'
                target = None
        else:
            print 'Sleeping'
            sleep(PlayerProcess.SLEEP_TIME)
        action = None
    print 'Loop ending'

class PlayerProcess(object):
    
    CMD_PLAY    = 1
    CMD_STOP    = 2
    CMD_PAUSE   = 4
    CMD_DIE     = 256
    
    SLEEP_TIME  = .5
    READ_SIZE   = 2048
    
    def __init__(self):
        self.__process_command_queue = Queue()
        self.__process = Process(group=None, target=_process_run,
                                args=(self.__process_command_queue,))
        self.__process.start()
    
    def __del__(self):
        try:
            if self.__process.is_alive():
                self.__process_command_queue.put(self.CMD_DIE, True)
                self.__process.join()
        except AttributeError:
            pass
    
    def set_song(self, song_url):
        self.__process_command_queue.put(song_url, False)
        
    def play(self):
        self.__process_command_queue.put(self.CMD_PLAY, False)
        
    def stop(self):
        self.__process_command_queue.put(self.CMD_STOP, False)
    
    def pause(self):
        self.__process_command_queue.put(self.CMD_PAUSE, False)
        