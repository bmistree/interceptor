import socket
import threading
import select
import os
import time
import struct

class Bridge(object):

    def __init__(self,to_listen_on_host_port_pair,
                 one_direction_plan,
                 to_connect_to_host_port_pair,
                 other_direction_plan):
        '''
        @param {HostPortPair} to_listen_on_host_port_pair ---

        @param {HostPortPair} to_connect_to_host_port_pair --- When
        get a connection, forward traffic to
        '''
        self.to_listen_on_host_port_pair = to_listen_on_host_port_pair
        self.to_connect_to_host_port_pair = to_connect_to_host_port_pair
        self.one_direction_plan = one_direction_plan
        self.other_direction_plan = other_direction_plan
        
        self.to_listen_on_socket = None
        self.to_connect_to_socket = None
        self.to_listen_on_socket_signal_pipe = None
        self.to_connect_to_socket_signal_pipe = None
        
        # we want to guarantee that we bring a set of connections down
        # just once for a pair of to_listen_on_socket and
        # to_connect_to_socket.
        self.last_connection_lock = threading.RLock()
        self.last_connection_phase_number = 0

        self.connection_setup_times = 0
        self.bound_socket = None
        
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
        # print '\nInterceptor connection setup\n'
        
        pipe = os.pipe()
        read_pipe_listen_on = pipe[0]
        self.to_listen_on_socket_signal_pipe = pipe[1]

        pipe = os.pipe()
        read_pipe_connect_to = pipe[0]
        self.to_connect_to_socket_signal_pipe = pipe[1]

        if self.connection_setup_times == 0:
            self.connection_setup_times += 1
            self.bound_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.bound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.bound_socket.bind(self.to_listen_on_host_port_pair.host_port_tuple())

        # print 'Interceptor listening ' + str(self)
        self.bound_socket.listen(1)
        self.to_listen_on_socket, addr = self.bound_socket.accept()

        # print 'Interceptor accepted ' + str(self)

        l_onoff = 1
        l_linger = 0
        self.to_listen_on_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_LINGER,
            struct.pack('ii', l_onoff, l_linger))

        self.to_listen_on_socket.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
        # print (
        #     '\nInterceptor trying to connect to ' +
        #     str(self.to_connect_to_host_port_pair.host_port_tuple()) +
        #     ' '  + str(self))
            
        while True:
            try:
                self.to_connect_to_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                self.to_connect_to_socket.connect(
                    self.to_connect_to_host_port_pair.host_port_tuple())
                break
            except Exception as inst:
                time.sleep(.5)
            
        # print (
        #     '\nInterceptor connected ' +
        #     str(self.to_connect_to_host_port_pair.host_port_tuple()) +
        #     ' '  + str(self))
        
        self.to_connect_to_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_LINGER,
            struct.pack('ii', l_onoff, l_linger))

        self.to_connect_to_socket.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        with self.last_connection_lock:
            self.last_connection_phase_number = (
                self.last_connection_phase_number + 1)
        
            # now start forwarding messages between both sides
            pair_one = _SendReceiveSocketPair(
                self.to_listen_on_socket,read_pipe_listen_on,
                self.to_connect_to_socket,
                self.one_direction_plan,self,
                self.last_connection_phase_number)

            pair_one.start()
            pair_two = _SendReceiveSocketPair(
                self.to_connect_to_socket,read_pipe_connect_to,
                self.to_listen_on_socket,
                self.other_direction_plan,self,
                self.last_connection_phase_number)
            pair_two.start()

        
    def bring_down_connection(self):
        '''
        Should only be called after both connections have already been
        made and started.  And should only be called once.
        '''
        self.one_direction_plan.notify_closed()
        self.other_direction_plan.notify_closed()

        try:
            self.to_listen_on_socket.close()
        except:
            print 'Exception closing to listen on socket'
        
        try:
            os.write(self.to_listen_on_socket_signal_pipe,'x')
            os.close(self.to_listen_on_socket_signal_pipe)
        except Exception as inst:
            print 'Exception closing pipe 1'
            print inst
        
        try:
            self.to_connect_to_socket.close()
        except Exception as inst:
            print 'Exception closing to connect to socket'
            pass

        try:
            os.write(self.to_connect_to_socket_signal_pipe,'x')
            os.close(self.to_connect_to_socket_signal_pipe)
        except:
            print 'Exception closing pipe 2'
            print inst
        

    def down_up_connection(self,phase_number):
        '''
        Bring connection down and then bring it up again.
        '''
        with self.last_connection_lock:
            if phase_number != self.last_connection_phase_number:
                return

            self.last_connection_phase_number += 1

            self.bring_down_connection()
            self.non_blocking_connection_setup()
        
        
class _SendReceiveSocketPair(object):
    def __init__(self,socket_to_listen_on,
                 close_on_selector_pipe,
                 socket_to_send_to,plan,bridge,
                 connection_phase_number):
        self.socket_to_listen_on = socket_to_listen_on
        self.close_on_selector_pipe = close_on_selector_pipe
        self.socket_to_send_to = socket_to_send_to
        self.plan = plan
        self.bridge = bridge
        self.connection_phase_number = connection_phase_number
        
    def start(self):
        t = threading.Thread(target=self.run)
        t.setDaemon(True)
        t.start()
        
    def run(self):
        try:
            while True:
                (input_ready,_,_) = select.select(
                    [self.socket_to_listen_on,self.close_on_selector_pipe],
                    [],[])
                
                if self.close_on_selector_pipe in input_ready:
                    self.bridge.down_up_connection(self.connection_phase_number)
                    break

                if self.socket_to_listen_on in input_ready:
                    recv_data = self.socket_to_listen_on.recv(1024)
                    if len(recv_data) == 0:
                        self.bridge.down_up_connection(self.connection_phase_number)
                        break

                    recv_return = self.plan.recv(recv_data,self.socket_to_send_to)
                    if recv_return is not None:
                        time.sleep(recv_return)
                        self.bridge.down_up_connection(self.connection_phase_number)
                        break
                    
        except Exception as inst:
            # can happen if someone closes the selctor pipe before we
            # go into select.
            print (
                '[DEBUG] Got an exception for ' + str(self.connection_phase_number) +
                ' ' + str(inst) + ' on bridge ' + str(self.bridge) + ' for socket ' +
                str(self.socket_to_send_to))

