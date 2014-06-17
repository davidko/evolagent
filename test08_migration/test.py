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

import datetime
import time
import serpent

import logging

def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M')

logging.basicConfig(filename='logfile-{0}.log'.format(timestamp()),
    level=logging.INFO)

class GaitChromosome(Chromosome):
    def fitness_function(self):
        # First, save fitness to a temporary file
        f = tempfile.NamedTemporaryFile()
        f.write(str(self).encode('utf-8'))
        f.flush()
        command = [ 'gait_fitness',  
                    '--disable-graphics',  
                    '--load-coefs', '{}'.format(f.name)]
        print(command)
        output = subprocess.check_output(command)
        positions = output.split()
        distance = 0.0;
        for p in positions:
          distance = distance + float(p)**2
        distance = math.sqrt(distance)
        print(distance)
        self.__fitness = distance
        f.close()
        return distance

    def crossover(self, other):
        if len(self.genes) != len(other.genes):
            raise EvolError('Gene lengths do not match.')
        cutpoint = random.randint(1, len(self.genes)-1)
        # Use a random number to determine whose genes go first during
        # crossover
        new_chro = None
        if random.randint(0, 1):
            new_chro = self.genes[0:cutpoint] + other.genes[cutpoint:]
        else:
            new_chro = other.genes[0:cutpoint] + self.genes[cutpoint:]
        return GaitChromosome(new_chro)

class TellAgentMigrateBehaviour(behaviours.TickerBehaviour):
    def on_tick(self):
        if self.agent.sorted_fitnesses is None or \
            len(self.agent.sorted_fitnesses) == 0:
                return
        try:
            agent = random.choice(self.agent.sorted_fitnesses)['agent_id']
            logging.info('Sending migrate command to {0}...'.format(agent))
            self.agent.add_behaviour(
                RequestInitiatorBehaviour(
                    store=agent,
                    request='migrate'))
            
        except Exception as e:
            logging.exception('ERROR: Could not migrate agent(s). {0}'.format(e))
            pass


class GaitMasterAgent(MasterAgent):
    def setup(self, *args, **kwargs):
        super(GaitMasterAgent, self).setup(*args, **kwargs)
        self.add_behaviour(TellAgentMigrateBehaviour())

class MyApp(App):
    def run(self, args):
        population = 20
        for i in range(population):
            self.start_agent(EvolAgent, 'gaitagent{0}'.format(i), 
                ChromosomeClass=GaitChromosome)
        self.start_agent(GaitMasterAgent, 
                         'MasterAgent', 
                         max_agent_population=population,
                         ChromosomeClass = GaitChromosome)

if __name__=="__main__":
    MyApp()
