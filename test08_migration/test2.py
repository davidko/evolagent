#!/usr/bin/env python

import spyse
from spyse.app.app import App
import spyse.core.behaviours.behaviours as behaviours
import spyse.core.behaviours.composite as cbehaviours
import random
import threading
import datetime
import evolagent

import Pyro4
Pyro4.config.SERIALIZER='pickle'
Pyro4.config.SERIALIZERS_ACCEPTED=['json', 'marshal', 'serpent', 'pickle']
Pyro4.config.SOCK_REUSE = True
import logging
import gaitagent

def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M.%S')

logging.basicConfig(filename='logfile-{0}.log'.format(timestamp()),
    level=logging.INFO)

class RandomMigrateBehaviour(behaviours.TickerBehaviour):
    def on_tick(self):
        if self.agent.initialized == False:
            self.agent.initialized = True
            return
        # First, get a list of remote ams's
        amss = self.agent.mts.ams.find_others()
        print('Found these other amses: {0}'.format(amss))
        ams = random.choice(list(amss))
        print('Moving to {0}...'.format(ams))
        self.agent.move(ams)

class MigrateAgent(gaitagent.GaitAgent):
    mycond = threading.Condition()
    def setup(self):
        self.add_behaviour(RandomMigrateBehaviour())
        self.initialized = False

    def execute(self):
        self.initialized = False
        logging.info('bloob')
        print('In execute()')

if __name__ == "__main__":
    App(port=9001, ns='local')

