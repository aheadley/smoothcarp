import hashlib
import json
import urllib2

class Api(object):
    """Grooveshark API"""
    
    CLIENT              = 'htmlshark'
    CLIENT_REVISION     = '20101222'
    SERVICE_VERSION     = '20100903'
    TOKEN_SALT          = 'quitStealinMahShit'
    HOST_GROOVESHARK    = 'grooveshark.com'
    HOST_COWBELL        = 'cowbell.' + HOST_GROOVESHARK
    HOST_LISTEN         = 'listen.' + HOST_GROOVESHARK
    
    def __init__(self):
        self._id_tokens = {
            'session': '0a1877819b50939e1f6ddfc376d1e0b7'
        }
        self._http_client_cookies = urllib2.HTTPCookieProcessor()
        self._http_client = urllib2.build_opener(self._http_client_cookies)
    
    def getCommunicationToken(self):
        try:
            return self._id_tokens['comm_token']
        except KeyError:
            self._id_tokens['comm_token'] = self._do_request(
                self._build_request('getCommunicationToken', {
                    'secretKey': self._make_secret_key()
                })
            )
        return self._id_tokens['comm_token']
    
    def authenticateUser(self, username, password, savePassword=0):
        pass
        
    def _build_request(self, method, parameters=None):
        request = urllib2.Request('https://' + self.HOST_COWBELL + '/more.php?' + method)
        request.add_header('Content-Type', 'application/json')
        request_data = {
            'header': {
                'client': self.CLIENT,
                'clientRevision': self.CLIENT_REVISION,
                'privacy': 0,
                'country': {
                    'ID': '223',
                    'CC1': '0',
                    'CC2': '0',
                    'CC3': '0',
                    'CC4': '1073741824',
                    'IPR': '82',
                },
                'session': self._id_tokens['session'],
            },
            'method': method,
            'parameters': parameters,
        }
        try:
            request_data['header']['token'] = self._get_auth_token(method)
        except KeyError:
            pass
        request.add_data(json.dumps(request_data))
        return request
    
    def _do_request(self, request):
        response = json.load(self._http_client.open(request))
        try:
            return response['result']
        except KeyError:
            raise ApiException(response['fault']['message'])
    
    def _get_php_session(self):
        try:
            return self._http_client_cookies.cookiejar['PHPSESSID'].value
        except KeyError:
            #get it the hard way
            self._http_client.open(urllib2.Request('http://' + self.HOST_LISTEN))
        return self._http_client_cookies.cookiejar['PHPSESSID'].value
    
    def _get_auth_token(self, method):
        random_number = '000004' #chosen by dice roll, guaranteed to be random
        plain_token = ':'.join([
            method,
            self._id_tokens['comm_token'],
            self.TOKEN_SALT,
            random_number,
        ])
        return random_number + hashlib.sha1(plain_token).hexdigest()
    
    def _make_secret_key(self, source_token=None):
        if source_token is None:
            source_token = self._get_php_session()
        return hashlib.md5(source_token).hexdigest()