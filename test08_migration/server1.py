#!/usr/bin/env python

import random
import tempfile
import subprocess
import math
import threading

from spyse.app.app import App
import spyse.core.behaviours.behaviours as behaviours
from spyse.core.protocols.request import RequestInitiatorBehaviour
from evolagent import Chromosome, EvolAgent, MasterAgent

from gaitagent import GaitAgent, GaitMasterAgent

import datetime
import time
import serpent
import uuid

import logging

import Pyro4
Pyro4.config.SERIALIZER='pickle'
Pyro4.config.SERIALIZERS_ACCEPTED=['json', 'marshal', 'serpent', 'pickle']
Pyro4.config.SOCK_REUSE = True

def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M.%S')

logging.basicConfig(filename='logfile-{0}.log'.format(timestamp()),
    level=logging.INFO)

class MyApp(App):
    def run(self, args):
        population = 20
        for i in range(population):
            self.start_agent(GaitAgent, 'gaitagent{0}'.format(uuid.uuid4()))
        self.start_agent(GaitMasterAgent, 
                         'MasterAgent', 
                         max_agent_population=population)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print('Usage: {0} <local_ip_address>'.format(sys.argv[0]))
        sys.exit(0)
    (nsuri, nsdaemon, bcserver) = Pyro4.naming.startNS(
        host=sys.argv[1],
        bchost=sys.argv[1])
    thread = threading.Thread(target=nsdaemon.requestLoop)
    thread.start()

    MyApp(port=9000, ns=sys.argv[1]+':9090')
