import time
import random

class Plan(object):
    def recv(self,received_data):
        '''
        Called when we read data from one socket and returns data to
        send to other socket.
        
        @returns {string or None} --- If string, returns some data to
        send to other side.  If returns None, then close entire
        connection.
        '''
    def notify_closed(self):
        '''
        Tell this plan that the connection it was forwarding for was
        closed.
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

class RandomDelayPlan(Plan):
    def __init__(self,uniform_lower_bound_seconds,
                 uniform_upper_bound_seconds):
        '''
        @param {float} uniform_upper_bound_seconds,
        uniform_lower_bound_seconds
        '''
        self.uniform_lower_bound_seconds = uniform_lower_bound_seconds
        self.uniform_upper_bound_seconds = uniform_upper_bound_seconds

    def recv(self):
        time_to_wait = random.uniform(
            self.uniform_lower_bound_seconds,self.uniform_upper_bound_seconds)
        time.sleep(time_to_wait)
        return time_to_wait

    
class DropPlan(Plan):
    def recv(self,received_data):
        return ''
