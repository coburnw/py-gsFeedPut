 
# derived from GroveStreams.com Python 3.2 Feed Example
# Copyright 2025 Coburn Wightman
# Copyright 2014 GroveStreams LLC.
# Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
import json
import http.client
import socket
import io
import gzip
import netrc
import time

class Stream:
    def __init__(self, stream_id, value_type='INTEGER'):
        self.stream_id = stream_id

        if value_type.upper() not in ['INTEGER', 'FLOAT', 'BOOL', 'STRING']:
            raise ValueError

        self.timestamp = None
        self.values = []

        self.name = 'stream.{}'.format(stream_id)
        self.description = 'No Description'
        self.value_type = value_type.upper()
        self.units_id = 'noSymbol'
        
        return

    def set_name(self, value):
        self.name = value
        
        return

    def set_description(self, value):
        self.description = value
        
        return
    
    def set_units(self, value):        
        self.units_id = value
        
        return

    def get_defaults(self):
        raise NotImplemented
    
    def clear(self):
        self.values.clear()
        
        return

    def update(self):
        raise NotImplemented

    # def rollup(self):
    #     result = self.values[-1]
    #     self.clear()
    #     self.values.append(result)

    #     return

    def serialize(self, comp_id, initialize=False):
        serialized = dict()

        if initialize:
            serialized['defaults'] = self.get_defaults()
            
        if comp_id:
            serialized['compId'] = comp_id
            
        serialized['streamId'] = self.stream_id
        serialized['data'] = self.values 
        
        return serialized


class PointStream(Stream):
    def __init__(self, stream_id, value_type='INTEGER'):
        super().__init__(stream_id, value_type)
        
        return

    def get_defaults(self):
        defaults = {'streamType': 'point_stream',
                    'description': self.description,
                    'name': self.name,
                    'valueType': self.value_type,
                    'unitId': self.units_id
                    }
        
        return defaults

        
class RandomStream(Stream):
    def __init__(self, stream_id, value_type='INTEGER'):
        super().__init__(stream_id, value_type)
        
        return

    def get_defaults(self):
        defaults = {'streamType': 'rdm_stream',
                    'description': self.description,
                    'name': self.name,
                    'valueType': self.value_type,
                    'unitId': self.units_id
                    #'baseCycleId': '20',
                    #'rollupCalendarId': 'standard'
                    }
        
        return defaults

    # def rollup(self):
    #     if self.value_type == 'STRING':
    #         raise TypeError('cant rollup a string')
        
    #     result = 0
    #     sample_count = len(self.values)
    #     for value in self.values:
    #         result += value / sample_count

    #     self.clear()
    #     self.values.append(result)

    #     return
        
class Streams():
    def __init__(self, comp_id):
        self.comp_id = comp_id
        self.streams = dict()
        
        return

    def append(self, stream):
        #stream.comp_id = self.comp_id
        self.streams[stream.stream_id] = stream

        return

    def clear(self):
        for key, stream in self.streams.items():
            stream.clear()

        return
            
    def update(self):
        for key, stream in self.streams.items():
            stream.update()

        return
            
    # def rollup(self):
    #     for key, stream in self.streams.items():
    #         stream.rollup()

    #     return
            
    def serialize(self, initialize=False):
        serialized = []
        
        for key, stream in self.streams.items():
            serialized.append(stream.serialize(self.comp_id, initialize))

        return serialized
            
class Component():
    def __init__(self, comp_id, template_id=None):
        self.comp_id = comp_id
        self.template_id = template_id

        self.folder_id = None
        self.streams = Streams(None)
        self.defaults = {}

        return

    def set_name(self, value):
        self.defaults['name'] = value
        return
    
    def set_description(self, value):
        self.defaults['description'] = value
        return
    
    def clear(self):
        self.streams.clear()
        return

    def update(self):
        self.streams.update()
        return
    
    # def rollup(self):
    #     self.streams.rollup()
    #     return
    
    def serialize(self, initialize=False):
        serialized = dict()
        
        serialized['componentId'] = self.comp_id
        if initialize:
            serialized['createDefault'] = False

            if self.template_id:
                serialized['compTmplId'] = self.template_id
                
            if self.folder_id:
                self.defaults['folderPath'] = self.folder_id
                
            serialized['defaults'] = self.defaults

        serialized['stream'] = self.streams.serialize(initialize)

        return serialized

class Components(): 
    def __init__(self, folder_id=None):
        self.folder_id = None
        if folder_id:
            self.folder_id = '/Components/{}'.format(folder_id)
            
        self.components = []

        return

    def append(self, component):
        component.folder_id = self.folder_id
        
        self.components.append(component)

        return
    
    def clear(self):
        for comp in self.components:
            comp.clear()

        return
        
    def update(self):
        for comp in self.components:
            comp.update()

        return
    
    # def rollup(self):
    #     for comp in self.components:
    #         comp.rollup()

    #     return
    
    def serialize(self, initialize=False):
        serialized = []
        
        for comp in self.components:
            serialized.append(comp.serialize(initialize))
        
        return serialized

class Feed:
    def __init__(self, project_id, compress=False):
        self.compress = compress

        try:
            rc = netrc.netrc()
        except netrc.NetrcParseError as err:
            print(err)
            if 'access too permissive' in err.args[0]:
                print('try "chmod -v 0600 ~/.netrc"')
        
        grovestreams = 'www.grovestreams.com'
        creds = rc.hosts[project_id]
        self.api_key = creds[2]
        
        self.conn = http.client.HTTPConnection(grovestreams)
        self.url = '/api/feed'

        self.initialized = False
        
        return

    def put(self, components, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time()) * 1000
            
        headers = {}
        headers["Cookie"] = "api_key="+self.api_key

        feed = dict()
        feed['time'] = [timestamp]
        
        initialize = not self.initialized            
        feed['component'] = components.serialize(initialize)
        
        body = dict()
        body['feed'] = feed
        body = self._encode(body, headers)
        
        original_size = len(body)
        # print(headers) # exposes api_key
        print(body)

        if self.compress:
            body = self._compress(body, headers)

        compression = (original_size - len(body)) / original_size
        print('upload size of {} bytes with {}% compression'.format(len(body), round(compression*100)))
              
        self.initialized = self._put(body, headers)
        
        components.clear() # dump data points
        
        return self.initialized

    def _encode(self, body, headers):
        body = json.dumps(body);
        headers["Content-type"] = "application/json"
        
        return body
    
    def _compress(self, body, headers):
        body = gzip.compress(body.encode('utf-8'))
        headers["Content-Encoding"] = "gzip"

        return body

    def _put(self, body, headers):
        headers["Connection"] = "close"

        status = True
        try:
            self.conn.request("PUT", self.url, body, headers)
             
            #Check for errors
            response = self.conn.getresponse()
            status = response.status
           
            if status != 200 and status != 201:
                status = False
                try:
                    if (response.reason != None):
                        print('HTTP Failure Reason: ' + response.reason + ' body: ' + response.read().decode(encoding='UTF-8'))
                    else:
                        print('HTTP Failure Body: ' + response.read().decode(encoding='UTF-8'))
                except Exception as e:
                    print('HTTP Failure Status : %d' % (status) )

        except Exception as e:
            status = False
            print('HTTP Failure: ' + str(e))
       
        finally:
            if self.conn != None:
                self.conn.close()
       
        return status

        
if __name__ == '__main__':
    import time
    import datetime
    import random
    #import grovestreams as gs

    # 'last reboot' for boot counter
    
    hostname = socket.gethostname()
    ipa = socket.gethostbyname(hostname + '.local')
        
    feed = Feed(compress=True)
    components = Components()
    
    for i in range(3):
        comp_id = '{}_frame-{}'.format(hostname, i)
        comp_name = '{} ({})'.format(comp_id, ipa)        

        frame = FrameComponent(comp_id, comp_name)
        components.append(frame)
    
    while True:
       
        ph_val = random.randrange(-7*54, 7*54)/1000
        temp_val = random.randrange(0, 100)
        components.update()
        feed.upload(components)
        
        #Pause for ten seconds
        time.sleep(10)
         
    # quit
    exit(0)
