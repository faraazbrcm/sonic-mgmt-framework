#:!/usr/bin/python
###########################################################################
#
# Copyright 2019 Dell, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###########################################################################

import sys
import time
import json
import ast
import openconfig_system_client
from rpipe_utils import pipestr
from openconfig_system_client.rest import ApiException
from scripts.render_cli import show_cli_output


import urllib3
urllib3.disable_warnings()


plugins = dict()

def util_capitalize(value):
    for key,val in list(value.items()):
        temp = key.split('_')
        alt_key = ''
        for i in temp:
            alt_key = alt_key + i.capitalize() + ' '
        value[alt_key]=value.pop(key)
    return value

def system_state_key_change(value):
    value.pop('motd_banner')
    value.pop('login_banner')
    return util_capitalize(value)


def memory_key_change(value):
    value['Total']=value.pop('physical')
    value['Used']=value.pop('reserved')
    return value

def register(func):
    """Register sdk client method as a plug-in"""
    plugins[func.__name__] = func
    return func


def call_method(name, args):
    method = plugins[name]
    return method(args)

def generate_body(func, args):
    body = None
    # Get the rules of all ACL table entries.

    if func.__name__ == 'get_openconfig_system_system_state':
        keypath = []
    elif func.__name__ == 'get_openconfig_system_system_clock':
        keypath = []
    elif func.__name__ == 'get_openconfig_system_system_memory':
        keypath = []
    elif func.__name__ == 'get_openconfig_system_system_cpus':
        keypath = []
    elif func.__name__ == 'get_openconfig_system_system_processes':
        keypath = []
    elif func.__name__ == 'get_openconfig_system_components':
        keypath = []

    else:
        body = {}

    return keypath,body


def run(func, args):
    c = openconfig_system_client.Configuration()
    c.verify_ssl = False
    aa = openconfig_system_client.OpenconfigSystemApi(api_client=openconfig_system_client.ApiClient(configuration=c))

    # create a body block
    keypath, body = generate_body(func, args)

    try:
        if body is not None:
            api_response = getattr(aa,func.__name__)(*keypath, body=body)

        else :
            api_response = getattr(aa,func.__name__)(*keypath)
        if api_response is None:
            print ("Success")
        else:
            response = api_response.to_dict()
            if 'openconfig_systemstate' in list(response.keys()):
                value = response['openconfig_systemstate']
                if value is None:
                    return
                show_cli_output(sys.argv[2], system_state_key_change(value))

            elif 'openconfig_systemmemory' in list(response.keys()):
                value = response['openconfig_systemmemory']
                if value is None:
                    return
                show_cli_output(sys.argv[2], memory_key_change(value['state']))
            elif 'openconfig_systemcpus' in list(response.keys()):
                value = response['openconfig_systemcpus']
                if value is None:
                    return
                show_cli_output(sys.argv[2], value['cpu'])
            elif 'openconfig_systemprocesses' in list(response.keys()):
                value = response['openconfig_systemprocesses']
                if 'pid' not in sys.argv:
                    if value is None:
                        return
                    show_cli_output(sys.argv[2],value['process'])
                else:
                    for proc in value['process']:
                        if proc['pid'] == int(sys.argv[3]):
                            show_cli_output(sys.argv[2],util_capitalize(proc['state']))
                            return
            else:
                print("Failed")
    except ApiException as e:
        if e.body != "":
            body = json.loads(e.body)
            if "ietf-restconf:errors" in body:
                err = body["ietf-restconf:errors"]
                if "error" in err:
                    errList = err["error"]

                    errDict = {}
                    for dict in errList:
                        for k, v in dict.items():
                            errDict[k] = v

                    if "error-message" in errDict:
                        print("%Error: " + errDict["error-message"])
                        return
                    print("%Error: Application Failure")
                    return
            print("%Error: Application Failure")
        else:
            print("Failed")

if __name__ == '__main__':

    pipestr().write(sys.argv)
    #pdb.set_trace()
    func = eval(sys.argv[1], globals(), openconfig_system_client.OpenconfigSystemApi.__dict__)
    run(func, sys.argv[2:])
