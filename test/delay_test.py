#!/usr/bin/env python

import os
import sys
import socket
import threading
import time
FILE_DIR = os.path.dirname( os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_DIR,'..',))

from interceptor.bridge import Bridge
from interceptor.util import HostPortPair
from interceptor.plan import ConstantDelayPlan

TEST_NAME = 'DELAY TEST'

def run_and_print():
    succeed_string = 'SUCCEEDED'
    if not run():
        succeed_string = 'FAILED'
    
    print ('\n%(test_name)s: %(succeed)s\n' %
           {'test_name': TEST_NAME,
            'succeed': succeed_string})
           
INTERPOSITION_LISTENER_PORT = 5555
TO_CONNECT_TO_PORT = INTERPOSITION_LISTENER_PORT + 1

# FIXME: probably could refactor this test and pass through test.
# Lots of code duplication.

def run():
    '''
    @returns {boolean} --- True if test succeeds, false if test fails.
    '''
    interposition_host_port_pair = HostPortPair(
        '127.0.0.1',INTERPOSITION_LISTENER_PORT)
    to_connect_to_host_port_pair = HostPortPair(
        '127.0.0.1',TO_CONNECT_TO_PORT)

    # start a thread listening on connection
    listener_connection = ListenerConnection(to_connect_to_host_port_pair)
    listener_connection.start()
    time.sleep(1)
    
    # now, create a bridge
    bridge = Bridge(
        interposition_host_port_pair,ConstantDelayPlan(1),
        to_connect_to_host_port_pair,ConstantDelayPlan(1))
    bridge.non_blocking_connection_setup()

    time.sleep(2)
    
    # now, try connecting to port on bridge.
    sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sending_socket.connect(interposition_host_port_pair.host_port_tuple())
    
    # now, send data to other side
    AMOUNT_OF_DATA_TO_SEND = 500
    expected_data_on_other_side = ''
    for i in range(0,AMOUNT_OF_DATA_TO_SEND):
        to_send = str(i)
        expected_data_on_other_side += to_send
        sending_socket.sendall(to_send)

    time.sleep(5)

    # check that other side got the expected data
    
    if expected_data_on_other_side != listener_connection.read_data:
        print ('\nExpected: %(expected)s, \nReceived: %(received)s\n' %
               { 'expected': expected_data_on_other_side,
                 'received': listener_connection.read_data})
        return False
    
    return True


class ListenerConnection(threading.Thread):
    def __init__(self,host_port_pair_to_listen_to):
        self.host_port_pair_to_listen_to = host_port_pair_to_listen_to
        # all data read from the connection thus far.
        self.read_data = ''
        
        super(ListenerConnection,self).__init__()
        self.setDaemon(True)
        
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(self.host_port_pair_to_listen_to.host_port_tuple())
        s.listen(1)
        to_listen_on_socket, addr = s.accept()

        while True:
            data = to_listen_on_socket.recv(1024)
            if len(data) == 0:
                break
            self.read_data += data
            

if __name__ == '__main__':
    run_and_print()
    
