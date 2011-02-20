import hashlib
import json
import urllib2

class ApiException(Exception):
    pass
class ApiFaultException(ApiException):
    """JSON fault from Grooveshark API"""
    def __init__(self, fault):
        self._fault = fault
    def __str__(self):
        return str(self._fault)
    def __repr__(self):
        return str(self)
class ApiMethodException(ApiException):
    pass
    
class Api(object):
    """Grooveshark API"""
    
    JS_CLIENT               = 'jsqueue'
    JS_CLIENT_REVISION      = '20101222.34'
    HTML_CLIENT             = 'htmlshark'
    HTML_CLIENT_REVISION    = '20101222'
    SERVICE_VERSION         = '20100903'
    TOKEN_SALT              = 'quitStealinMahShit'
    HOST_GROOVESHARK        = 'grooveshark.com'
    HOST_COWBELL            = 'cowbell.' + HOST_GROOVESHARK
    HOST_LISTEN             = 'listen.' + HOST_GROOVESHARK
    
    _LISTEN_METHODS      = [
        'getUserByID',
        'userGetPlaylists',
        'getFavorites',
        'getUserSidebar',
        'getRecentlyActiveUsers',
        'userGetLibraryTSModified',
        'getRecentlyActiveUsers',
        'getCombinedProcessedFeedData',
        'getSearchResultsEx',
        'getArtistAutocomplete',
        'getTokenForSong',
        'getArtistByID',
        'artistGetSongs',
        'albumGetSongs',
    ]
    _COWBELL_METHODS     = [
        'getCommunicationToken',
        'initiateQueue',
        'getQueueSongListFromSongIDs',
        'authenticateUser',
        'getSubscriptionDetails',
        'addSongsToQueue',
        'getStreamKeyFromSongIDEx',
        'markSongDownloadedEx',
        'markSongQueueSongPlayed',
        'updateStreamKeyLength',
        'markStreamKeyOver30Seconds',
        'markSongComplete',
    ]
    _VALID_METHODS = _LISTEN_METHODS + _COWBELL_METHODS
    _JS_CLIENT_METHODS    = [
        'getStreamKeyFromSongIDEx',
        'addSongsToQueue',
        'getQueueSongListFromSongIDs',
        'initiateQueue',
        'markSongQueueSongPlayed',
        'markSongDownloadedEx',
        'markStreamKeyOver30Seconds',
        'markSongComplete',
    ]
    
    _QUERY_TYPES = [
        'Songs',
        'Albums',
        'Artists',
    ]
    
    def __init__(self):
        self._id_tokens = {}
        self._http_client_cookies = urllib2.HTTPCookieProcessor()
        self._http_client = urllib2.build_opener(self._http_client_cookies)
        
    def __getattr__(self, method_name):
        if method_name in self._VALID_METHODS:
            return lambda **parameters: self._do_request(
                self._build_request(method_name, parameters or None))
        else:
            raise AttributeError(method_name)
        
    def _get_method_request_data(self, method):
        data = {
            'url': None,
            'client': None,
            'client_revision': None,
        }
        if method in self._COWBELL_METHODS:
            data['url'] = 'https://' + self.HOST_COWBELL + '/more.php?' + method
        elif method in self._LISTEN_METHODS:
            data['url'] = 'https://' + self.HOST_LISTEN + '/more.php?' + method
        else:
            raise ApiMethodException(method)
        if method in self._JS_CLIENT_METHODS:
            data['client'] = self.JS_CLIENT
            data['client_revision'] = self.JS_CLIENT_REVISION
        else:
            data['client'] = self.HTML_CLIENT
            data['client_revision'] = self.HTML_CLIENT_REVISION
        return data
    
    def _get_country(self):
        return {'ID': '223','CC1': '0','CC2': '0','CC3': '0','CC4': '1073741824','IPR': '82'}
    
    def _build_request(self, method, parameters=None):
        method_data = self._get_method_request_data(method)
        request = urllib2.Request(method_data['url'])
        request.add_header('Content-Type', 'application/json')
        request_data = {
            'header': {
                'client': method_data['client'],
                'clientRevision': method_data['client_revision'],
                'privacy': 0,
                'country': self._get_country(),
                'session': self._get_php_session(),
            },
            'method': method,
            'parameters': parameters,
        }
        if method != 'getCommunicationToken':
            try:
                request_data['header']['token'] = self._get_auth_token(method)
            except KeyError:
                pass
        request.add_data(json.dumps(request_data))
        return request
    
    def _do_request(self, request):
        response = self._http_client.open(request)
        try:
            response_json = json.load(response)
        except ValueError, e:
            print response.read()
            raise e
        try:
            return response_json['result']
        except KeyError:
            raise ApiFaultException(response_json['fault'])
    
    def _get_php_session(self):
        try:
            return self._id_tokens['php_session']
        except KeyError:
            #get it the hard way
            self._http_client.open(urllib2.Request('http://' + self.HOST_LISTEN))
            for cookie in self._http_client_cookies.cookiejar:
                if cookie.name == 'PHPSESSID':
                    self._id_tokens['php_session'] = cookie.value
        return self._id_tokens['php_session']
    
    def _get_comm_token(self):
        #this has a short shelf life (30 min maybe?), need to check it
        try:
            return self._id_tokens['comm_token']
        except KeyError:
            self._id_tokens['comm_token'] = self.getCommunicationToken(secretKey=self._get_secret_key())
        return self._id_tokens['comm_token']
    
    def _get_auth_token(self, method):
        random_number = '000004' #chosen by dice roll, guaranteed to be random
        plain_token = ':'.join([
            method,
            self._get_comm_token(),
            self.TOKEN_SALT,
            random_number,
        ])
        return random_number + hashlib.sha1(plain_token).hexdigest()
    
    def _get_secret_key(self):
        return hashlib.md5(self._get_php_session()).hexdigest()