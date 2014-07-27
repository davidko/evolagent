#!/usr/bin/env python

import spyse
from spyse.app.app import App
import spyse.core.behaviours.behaviours as behaviours
import spyse.core.behaviours.composite as cbehaviours
from spyse.core.platform.df import Service
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

def bloob(arg):
    pass

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
        chromosome = [random.randint(0, 255) for _ in range(120)]
       
        self.genes = chromosome
        seq = cbehaviours.SequentialBehaviour()
        #seq.add_behaviour(evolagent.agent.ComputeFitnessBehaviour())
        #seq.add_behaviour(evolagent.agent.ReportFitnessBehaviour())
        #seq.add_behaviour(
        #    evolagent.agent.RegisterServiceBehaviour(service=Service('EvolAgent')))
        #self.add_behaviour(evolagent.agent.EvolAgentHandleRequestBehaviour())
        #self.add_behaviour(evolagent.agent.MateParticipantBehaviour())
        seq.add_behaviour(RandomMigrateBehaviour())
        self.add_behaviour(seq)
        self.initialized = False
        self.blah = MigrateAgent

    def execute(self):
        self.initialized = False
        logging.info('bloob')
        print('In execute()')
        print('My name is: ' + self.name)
        self.add_behaviour(RandomMigrateBehaviour())
        self.initialized = False

class MyApp(App):
    def run(self, args):
        population = 1
        for _ in range(population):
            self.start_agent(MigrateAgent)
        #self.start_agent(gaitagent.GaitMasterAgent, "MasterAgent",
        #    max_agent_population=population)

if __name__ == "__main__":
    (nsuri, nsdaemon, bcserver) = Pyro4.naming.startNS()
    thread = threading.Thread(target=nsdaemon.requestLoop)
    thread.start()

    MyApp(port=9000, ns='local')
