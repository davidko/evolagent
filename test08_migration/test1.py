#!/usr/bin/env python

import spyse
from spyse.app.app import App
import spyse.core.behaviours.behaviours as behaviours
import random
import threading

import Pyro4
Pyro4.config.SERIALIZER='pickle'
Pyro4.config.SERIALIZERS_ACCEPTED=['json', 'marshal', 'serpent', 'pickle']
Pyro4.config.SOCK_REUSE = True

class RandomMigrateBehaviour(behaviours.TickerBehaviour):
    def on_tick(self):
        # First, get a list of remote ams's
        amss = self.agent.mts.ams.find_others()
        print('Found these other amses: {0}'.format(amss))
        ams = random.choice(list(amss))
        print('Moving to {0}...'.format(ams))
        self.agent.move(ams)

class MigrateAgent(spyse.core.agents.agent.Agent):
    def setup(self):
        self.add_behaviour(RandomMigrateBehaviour())

    def execute(self):
        print('In execute()')

class MyApp(App):
    def run(self, args):
        self.start_agent(MigrateAgent)

if __name__ == "__main__":
    (nsuri, nsdaemon, bcserver) = Pyro4.naming.startNS()
    thread = threading.Thread(target=nsdaemon.requestLoop)
    thread.start()

    MyApp(port=9000, ns='local')
