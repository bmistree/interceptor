import socket
import threading

class Bridge(object):

    def __init__(self,to_listen_on_host_port_pair,
                 to_connect_to_host_port_pair):
        '''
        @param {HostPortPair} to_listen_on_host_port_pair ---

        @param {HostPortPair} to_connect_to_host_port_pair --- When
        get a connection, forward traffic to
        '''
        self.to_listen_on_host_port_pair = to_listen_on_host_port_pair
        self.to_connect_to_host_port_pair = to_connect_to_host_port_pair

        self.to_listen_on_socket = None
        self.to_connect_to_socket = None

        
    def non_blocking_connection_setup(self):
        '''
        Calls connection_setup in separate thread.
        '''
        t = threading.Thread(target = self.connection_setup)
        t.setDaemon(True)
        t.start()
        
        
    def connection_setup(self):
        '''
        Listen for a connection.  When receive connection, try to
        connect to other side.  Blocking.
        '''
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(self.to_listen_on_host_port_pair.host_port_tuple())
        s.listen(1)
        self.to_listen_on_socket, addr = s.accept()

        to_connect_to_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.to_connect_to_socket.connect(
            self.to_connect_to_host_port_pair.host_port_tuple())

        # now start forwarding messages between both sides
        pair_one = _SendReceiveSocketPair(
            self.to_listen_on_socket,self.to_connect_to_socket)
        pair_one.start()
        pair_two = _SendReceiveSocketPair(
            self.to_connect_to_socket,self.to_listen_on_socket)
        pair_two.start()

    def bring_down_connection(self):
        '''
        Should only be called after both connections have already been
        made and started.  And should only be called once.
        '''
        try:
            self.to_listen_on_socket.close()
        except:
            pass
        
        try:
            self.to_connect_to_socket.close()
        except:
            pass


class _SendReceiveSocketPair(object):
    def __init__(self,socket_to_listen_on, socket_to_send_to):
        self.socket_to_listen_on = socket_to_listen_on
        self.socket_to_send_to = socket_to_send_to

    def start(self):
        t = threading.Thread(target=self.run)
        t.setDaemon(true)
        t.start()
        
    def run(self):
        while True:
            try:
                data = self.socket_to_listen_on.recv(1024)
                self.socket_to_send_to.write(data)
            except:
                break
