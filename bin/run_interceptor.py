#!/usr/bin/env python

import argparse
import json
import os
import sys
import time

FILE_DIR = os.path.dirname( os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_DIR,'..',))

from interceptor.util import HostPortPair
from interceptor.plan import plan_from_args
from interceptor.bridge import Bridge

INTERPOSING_HOST_FIELD = 'interposing_host'
INTERPOSING_PORT_FIELD = 'interposing_port'

TO_CONNECT_TO_HOST_FIELD = 'to_connect_to_host'
TO_CONNECT_TO_PORT_FIELD = 'to_connect_to_port'

PLAN_FIELD = 'plan'
PLAN_TYPE_FIELD = 'type'
PLAN_ADDITIONAL_ARGS_FIELD = 'additional_args'

class BridgeArguments(object):
    def __init__(self,arg_line):
        '''
        @param {string} arg_line --- Should be a json string of a
        list.  Each element has the following form:
            {
                interposing_host: <string>,
                interposing_port: <int>,

                to_connect_to_host: <string>,
                to_connect_to_port: <int>,

                plan: {
                  type: <string>,
                  additional_args: {
                  ... // specific to plan type
                  }
                }
            }
        '''
        self.bridge_list = []

        try:
            arg_list = json.loads(arg_line)
        except ValueError as ex:
            raise argparse.ArgumentTypeError(str(ex))
        
        for bridge_description in arg_list:
            interposing_host = bridge_description.get(
                INTERPOSING_HOST_FIELD,None)
            interposing_port = bridge_description.get(
                INTERPOSING_PORT_FIELD,None)

            to_connect_to_host = bridge_description.get(
                TO_CONNECT_TO_HOST_FIELD,None)
            to_connect_to_port = bridge_description.get(
                TO_CONNECT_TO_PORT_FIELD,None)
            
            plan_params = bridge_description.get(PLAN_FIELD,None)
            
            if interposing_host is None:
                raise argparse.ArgumentTypeError(
                    'Must specify interposing_host field for ' +
                    'bridge description')
            if interposing_port is None:
                raise argparse.ArgumentTypeError(
                    'Must specify interposing_port field for ' +
                    'bridge description')
            if to_connect_to_host is None:
                raise argparse.ArgumentTypeError(
                    'Must specify to_connect_to_host field for ' +
                    'bridge description')
            if to_connect_to_port is None:
                raise argparse.ArgumentTypeError(
                    'Must specify to_connect_to_port field for ' +
                    'bridge description')
            if plan_params is None:
                raise argparse.ArgumentTypeError(
                    'Must specify plan field for ' +
                    'bridge description')
            interposing_port = int(interposing_port)
            conecting_port = int(to_connect_to_port)
            
            interposition_host_port_pair = HostPortPair(
                interposing_host,interposing_port)
            to_connect_to_host_port_pair = HostPortPair(
                to_connect_to_host,to_connect_to_port)


            # decode plan
            plan_type = plan_params.get(PLAN_TYPE_FIELD,None)
            plan_additional_args = plan_params.get(
                PLAN_ADDITIONAL_ARGS_FIELD,None)
            if plan_type is None:
                raise argparse.ArgumentTypeError(
                    'Must specify plan_type field for ' +
                    'bridge description')
            if plan_additional_args is None:
                raise argparse.ArgumentTypeError(
                    'Must specify plan_additional_args field for ' +
                    'bridge description')

            plan_one_side = plan_from_args(plan_type,plan_additional_args)
            plan_other_side = plan_from_args(plan_type,plan_additional_args)

            bridge = Bridge(
                interposition_host_port_pair,plan_one_side,
                to_connect_to_host_port_pair,plan_other_side)
            self.bridge_list.append(bridge)
            
            
    def start_bridges(self):
        for bridge in self.bridge_list:
            bridge.non_blocking_connection_setup()

def bridges_help():
    return '''
Should be a json string of a list.  Each element of list
has the following form:
    {
        interposing_host: <string>,
        interposing_port: <int>,

        to_connect_to_host: <string>,
        to_connect_to_port: <int>,

        plan: {
          type: <string>,
          additional_args: {
          ... /* specific to plan type */
          }
        }
    }
'''
    

def run():
    parser = argparse.ArgumentParser(
        'Run a shim between processes that intercepts messages')
    parser.add_argument('--bridges',type=BridgeArguments,help=bridges_help())
    args = parser.parse_args()
    
    bridge_arguments = args.bridges

    bridge_arguments.start_bridges()
    while True:
        time.sleep(1)
    


if __name__ == '__main__':
    run()
