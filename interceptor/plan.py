import time
import random
import argparse
import Queue
import threading

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
    elif plan_type == PlanType.RANDOM_FAIL_PLAN:
        failure_probability = additional_args.get('failure_probability',None)
        if failure_probability is None:
            raise argparse.ArgumentTypeError(
                'Error: random fail plan requires argument ' +
                'failure_probability argument to be specified.')

        return RandomFailPlan(float(failure_probability))
    
    raise argparse.ArgumentTypeError('Unknown plan type')

    
class PlanType(object):
    PASS_THROUGH_PLAN = 'pass_through'
    CONSTANT_DELAY_PLAN = 'constant_delay'
    RANDOM_DELAY_PLAN = 'random_delay'
    DROP_PLAN = 'drop'
    RANDOM_FAIL_PLAN = 'random_fail_plan'

    
class Plan(object):
    def recv(self,received_data,socket_to_send_data_to):
        '''
        Called when we read data from one socket and returns data to
        send to other socket.

        @returns {float or None} --- If None, then should not close
        socket.  If float, wait for this number of seconds and then
        close the socket.
        '''
    def notify_closed(self):
        '''
        Tell this plan that the connection it was forwarding for was
        closed.
        '''

class PassThroughPlan(Plan):
    def recv(self,received_data,socket_to_send_data_to):
        socket_to_send_data_to.sendall(received_data)
        return None

    
class DropPlan(Plan):
    def recv(self,received_data,socket_to_send_data_to):
        return None

class DelayDataElement(object):
    def __init__(self,data,socket,received_time_seconds):
        self.data = data
        self.socket = socket
        self.received_time_seconds = received_time_seconds

    def send_data(self):
        self.socket.sendall(self.data)
        
    
class DelayPlan(Plan):
    def __init__(self, sending_thread_target):
        '''
        @param {function} --- thread to start to handle sending 
        '''
        # contains all data received so far, in order and the socket
        # to send the data out on when ready.
        self.data_queue = Queue.Queue()

        t = threading.Thread(target=sending_thread_target)
        t.setDaemon(True)
        t.start()

    def notify_closed(self):
        with self.data_queue.queue.mutex:
            self.data_queue.queue.clear()
        
    def recv(self,received_data,socket_to_send_data_to):
        self.data_queue.put(
            DelayDataElement(
                received_data,socket_to_send_data_to,
                # FIXME: assuming time.time will give me better than
                # second accuracy.
                time.time()))
        return None

class ConstantDelayPlan(DelayPlan):
    def __init__(self,seconds_to_delay_before_forwarding):
        '''
        @param {float} seconds_to_delay_before_forwarding
        '''
        self.seconds_to_delay_before_forwarding = (
            seconds_to_delay_before_forwarding)
        super(ConstantDelayPlan,self).__init__(self.sending_thread)

    def sending_thread(self):
        while True:
            delay_data_element = self.data_queue.get()            
            current_time = time.time()
            
            time_should_send = (
                self.seconds_to_delay_before_forwarding +
                delay_data_element.received_time_seconds)

            time_to_sleep = time_should_send - current_time
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)

            try:
                # socket is closed.  everything will eventually shut
                # down on its own.
                delay_data_element.send_data()
            except:
                pass

    
class RandomDelayPlan(DelayPlan):
    def __init__(self,uniform_lower_bound_seconds,
                 uniform_upper_bound_seconds):
        '''
        @param {float} uniform_upper_bound_seconds,
        uniform_lower_bound_seconds
        '''
        self.uniform_lower_bound_seconds = uniform_lower_bound_seconds
        self.uniform_upper_bound_seconds = uniform_upper_bound_seconds

        super(ConstantDelayPlan,self).__init__(self.sending_thread)

    def sending_thread(self):
        while True:
            delay_data_element = self.data_queue.get()            
            current_time = time.time()

            seconds_to_delay_before_forwarding = random.uniform(
                self.uniform_lower_bound_seconds,
                self.uniform_upper_bound_seconds)
            time_should_send = (
                seconds_to_delay_before_forwarding +
                delay_data_element.received_time_seconds)

            time_to_sleep = time_should_send - current_time
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)

            try:
                # socket is closed.  everything will eventually shut
                # down on its own.
                delay_data_element.send_data()
            except:
                pass

class RandomFailConstantDelayPlan(Plan):
    def __init__(self,failure_probability,seconds_to_wait_to_fail):
        '''
        @param {float} failure_probability, seconds_to_wait_to_fail
        '''
        self.failure_probability = failure_probability
        self.seconds_to_wait_to_fail = seconds_to_wait_to_fail
        
    def recv(self,received_data,socket_to_send_data_to):
        socket_to_send_data_to.sendall(received_data)
        if random.random() < self.failure_probability:
            # fail instantly
            return self.seconds_to_wait_to_fail
        return None

            
class RandomFailPlan(RandomFailConstantDelayPlan):
    def __init__(self,failure_probability):
        super(RandomFailPlan,self).__init__(failure_probability,0)
