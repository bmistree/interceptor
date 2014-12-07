import time

class Plan(object):
    def recv(self,received_data):
        '''
        Called when we read data from one socket and returns data to
        send to other socket.
        
        @returns {string or None} --- If string, returns some data to
        send to other side.  If returns None, then close entire
        connection.
        '''

class PassThroughPlan(Plan):
    def recv(self,received_data):
        return received_data
        
class ConstantDelayPlan(Plan):
    def __init__(self,seconds_to_delay_before_forwarding):
        '''
        @param {float} seconds_to_delay_before_forwarding
        '''
        self.seconds_to_delay_before_forwarding = (
            seconds_to_delay_before_forwarding)

    def recv(self,received_data):
        time.sleep(self.seconds_to_delay_before_forwarding)
        return recevied_data

class DropPlan(Plan):
    def recv(self,received_data):
        return ''
