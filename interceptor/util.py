

class HostPortPair(object):
    def __init__(self,host,port):
        self.host = host
        self.port = port
        
    def host_port_tuple(self):
        return (self.host,self.port)
