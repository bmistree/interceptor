import time
import random
import argparse

def plan_from_args(plan_type,additional_args):
    '''
    @param {PlanType} plan_type
    @param {dict} additional_args --- Additional arguments for loading
    plan type.

    @throws argparse.ArgumentTypeError if unkown plan type or missing
    fields.
    '''
    if plan_type == PlanType.PASS_THROUGH_PLAN:
        return PassThroughPlan()
    elif plan_type == PlanType.CONSTANT_DELAY_PLAN:
        seconds_to_delay = additional_args.get('delay_seconds',None)
        if seconds_to_delay is None:
            raise argparse.ArgumentTypeError(
                'Error: delay plan type requires argument delay_seconds ' +
                'to be specified.')
        seconds_to_delay = float(seconds_to_delay)
        return ConstantDelayPlan(seconds_to_delay)
    elif plan_type == PlanType.RANDOM_DELAY_PLAN:
        lower_bound = additional_args.get('lower_delay_seconds',None)
        upper_bound = additional_args.get('upper_delay_seconds',None)
        if (lower_bound is None) or (upper_bound is None):
            raise argparse.ArgumentTypeError(
                'Error: delay plan type requires argument ' +
                'lower_delay_seconds and upper_delay_seconds ' +
                'to be specified.')
        lower_bound = float(lower_bound)
        upper_bound = float(upper_bound)
        return RandomDelayPlan(lower_bound,upper_bound)
    elif plan_type == PlanType.DROP_PLAN:
        return DropPlan()

    raise argparse.ArgumentTypeError('Unknown plan type')

    
class PlanType(object):
    PASS_THROUGH_PLAN = 'pass_through'
    CONSTANT_DELAY_PLAN = 'constant_delay'
    RANDOM_DELAY_PLAN = 'random_delay'
    DROP_PLAN = 'drop'

    
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
