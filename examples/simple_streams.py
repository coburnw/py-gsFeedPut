import socket
import random

import gs_feedput as gs

class RollingAverage():
    def __init__(self, filter_constant, initial_value=0):
        self.n = filter_constant
        self.value= initial_value

        return

    def update(self, new_sample):
        result = self.value
        
        result -= self.value / self.n
        result += new_sample / self.n

        self.value = result
        
        return result

    
class TemperatureStream(gs.RandomStream):
    def __init__(self, stream_id, location, filter_constant):
        super().__init__(stream_id, 'FLOAT')

        name = '{}.{}'.format(location, 'degC')
        self.set_name(name)
        self.set_description('Frame Temperature')
        self.set_units('celcius')

        self.filter = RollingAverage(filter_constant)
        return

    def update(self):
        value = random.randrange(0, 100)
        value = self.filter.update(value)

        self.values.clear()
        self.values.append(round(value, 1))

        return

    
class PhStream(gs.RandomStream):
    def __init__(self, stream_id, location, filter_constant):
        super().__init__(stream_id, 'FLOAT')

        name = '{}.{}'.format(location, 'ph')
        self.set_name(name)
        self.set_description('uncalibrated potential of Hydrogen (pH)')
        self.set_units('milli_volts')

        self.filter = RollingAverage(filter_constant)
        return

    def update(self):
        value = random.randrange(-7*54, 7*54)/1000
        value = self.filter.update(value)
        
        self.values.clear()
        self.values.append(round(value, 3))
        
        return

    
class EhStream(gs.RandomStream):
    def __init__(self, stream_id, location, filter_constant):
        super().__init__(stream_id, 'FLOAT')

        name = '{}.{}'.format(location, 'eh')
        self.set_name(name)
        self.set_description('uncalibrated oxidation reduction potential (Eh)')
        self.set_units('milli_volts')
        
        self.filter = RollingAverage(filter_constant)
        return

    def update(self):
        value = random.randrange(-7*54, 7*54)/1000*2
        value = self.filter.update(value)

        self.values.clear()
        self.values.append(round(value, 3))
        
        return

    
class IpaStream(gs.PointStream):
    def __init__(self, stream_id, location):
        super().__init__(stream_id, 'STRING')

        name = '{}.{}'.format(location, 'ipa')
        self.set_name(name)
        self.set_description('Local IP Address')
        self.set_units('noSymbol')
        
        return

    def update(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # a tuple with any address...
            s.connect(('grovestreams.com', 80))
            ipa = s.getsockname()[0]
        except:
            ipa = '127.0.0.1'
        finally:
            s.close()

        self.values.clear()
        self.values.append(ipa)
        
        return


        
