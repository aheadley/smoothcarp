from random import randint
from urllib import quote_plus
from Api import Api
from PlayerProcess import PlayerProcess

class Player(object):
    """Audio Player wrapper object"""
    
    _STREAM_URL     = 'http://%s/stream.php?streamKey=%s'
    
    def __init__(self):
        self.__api = Api()
        self.__player = PlayerProcess()
        self.__song_queue = []
        self.__song_queue_position = None
        self.__playing = False
        self.__shuffle = False
        self.__repeat = False
        
    def play(self):
        if not self.__playing:
            if self.__song_queue_position is None:
                pass
            else:
                self.__player.set_song(self.__get_song_url(
                    self.__song_queue[self.__song_queue_position]))
                self.__player.play()
                self.__playing = True

    def stop(self):
        self.__player.stop()
        self.__playing = False
        
    def pause(self):
        self.__player.pause()
        self.__playing = False
        
    def is_playing(self):
        return self.__playing
    
    def next(self):
        self.stop()
        self.__song_queue_position = self.__get_next(self.__song_queue_position)
        self.play()
        
    def previous(self):
        self.stop()
        self.__song_queue_position = self.__get_previous(self.__song_queue_position)
        self.play()

    def skip_to_in_queue(self, offset):
        offset = self.__constrain_offset(offset)
        self.stop()
        self.__song_queue_position = offset
        self.play()
    
    def set_shuffle(self, status=None):
        if status is None:
            self.__shuffle = not self.__shuffle
        else:
            self.__shuffle = bool(status)
        return self.__shuffle
    
    def set_repeat(self, status=None):
        if status is None:
            self.__repeat = not self.__repeat
        else:
            self.__repeat = bool(status)
        return self.__repeat

    def add_song_to_queue(self, song_id):
        if song_id not in self.__song_queue:
            self.__song_queue.append(int(song_id))
            if self.__song_queue_position is None:
                self.__song_queue_position = 0
            
    def remove_song_from_queue(self, song_id):
        if song_id in self.__song_queue:
            if song_id is self.__song_queue[self.__song_queue_position]:
                self.next()
            self.__song_queue.remove(song_id)
            if len(self.__song_queue) is 0:
                self.__song_queue_position = None
            
    def add_playlist_to_queue(self, playlist_id):
        #playlist = getplaylist(playlist_id)
        #for id in [int(song[SongID]) for song in playlist]: song_queue.append(id)
        pass
    
    def clear_queue(self):
        self.stop()
        self.__song_queue = []
        
    def get_queue(self):
        return self.__song_queue
    
    def get_queue_song(self, offset):
        return self.__song_queue[self.__constrain_offset(offset)]
    
    def __constrain_offset(self, offset):
        return max(min(offset, len(self.__song_queue)), 0)
    
    def __get_next(self, current_position):
        if self.__shuffle:
            return randint(0, len(self.__song_queue))
        elif self.__repeat:
            return (current_position + 1) % len(self.__song_queue)
        else:
            if current_position + 1 > len(self.__song_queue):
                return current_position
            else:
                return current_position + 1
        
    def __get_previous(self, current_position):
        if self.__shuffle:
            return randint(0, len(self.__song_queue))
        else:
            return abs(current_position - 1 % len(self.__song_queue))
    
    def __get_song_url(self, song_id):
        streamkey_info = self.__api.getStreamKeyFromSongIDEx(
            mobile=False,
            country=self.__api.get_country(),
            prefetch=False,
            songID=int(song_id))
        return self._STREAM_URL % (streamkey_info['ip'], quote_plus(streamkey_info['streamKey']))
    