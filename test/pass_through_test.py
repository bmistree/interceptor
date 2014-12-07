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


TEST_NAME = 'PASS THROUGH TEST'

def run_and_print():
    succeed_string = 'SUCCEEDED'
    if not run():
        succeed_string = 'FAILED'
    
    print ('\n%(test_name)s: %(succeed)s\n' %
           {'test_name': TEST_NAME,
            'succeed': succeed_string})
           
INTERPOSITION_LISTENER_PORT = 5555
TO_CONNECT_TO_PORT = INTERPOSITION_LISTENER_PORT + 1

def run():
    '''
    Test starts listening on a port.  Then, it starts a bridge (which
    will connect any connection it receives to that port).  Then, it
    tries connecting to the interposition port, and sends messages to
    other side.  Messages sent should be equal to messages received
    (because bridge just passes messages through).

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
        interposition_host_port_pair,to_connect_to_host_port_pair)
    bridge.non_blocking_connection_setup()
    
    # now, try connecting to port on bridge.
    sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sending_socket.connect(interposition_host_port_pair.host_port_tuple())
    
    # now, send data to other side
    AMOUNT_OF_DATA_TO_SEND = 500
    expected_data_on_other_side = ''
    for i in range(0,AMOUNT_OF_DATA_TO_SEND):
        to_send = str(i)
        expected_data_on_other_side += to_send
        sending_socket.write(expected_data_on_other_side)

    time.sleep(1)

    # check that other side got the expected data
    
    if expected_data_on_other_side != listener_connection.read_data:
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
            self.read_data += data


if __name__ == '__main__':
    run_and_print()
    
