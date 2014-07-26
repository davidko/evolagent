#!/usr/bin/env python
import pickle

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

import logging

import Pyro4
Pyro4.config.SERIALIZER='pickle'
Pyro4.config.SERIALIZERS_ACCEPTED=['json', 'marshal', 'serpent', 'pickle']
Pyro4.config.SOCK_REUSE = True

def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M.%S')

logging.basicConfig(filename='logfile-{0}.log'.format(timestamp()),
    level=logging.INFO)

class PickleBehaviour(behaviours.Behaviour):
    def action(self):
        print('Attempting to pickle...')
        self.agent.clear_behaviours()
        print(pickle.dumps(self.agent))

class PickleAgent(GaitAgent):
    def setup(self, *args, **kwargs):
        GaitAgent.setup(self, *args, **kwargs)
        self.add_behaviour(PickleBehaviour())

class MyApp(App):
    def run(self, args):
        self.start_agent(PickleAgent, 'picklemebro')

if __name__ == "__main__":
    app = MyApp()
