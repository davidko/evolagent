#!/usr/bin/env python

import tempfile
import subprocess
import math
from evolagent import EvolError
from evolagent import Chromosome, EvolAgent, MasterAgent
import random
from evolagent.agent import EvolAgent
import spyse.core.behaviours.behaviours as behaviours
import logging

class GaitAgent(EvolAgent):
    def fitness_function(self):
        # First, save fitness to a temporary file
        f = tempfile.NamedTemporaryFile()
        gene_str = '\n'.join(map(str, self.genes))
        f.write(gene_str.encode('utf-8'))
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
        f.close()
        return distance

    def crossover(self, other):
        if len(self.genes) != len(other):
            raise EvolError('Gene lengths do not match.')
        cutpoint = random.randint(1, len(self.genes)-1)
        # Use a random number to determine whose genes go first during
        # crossover
        new_chro = None
        if random.randint(0, 1):
            new_chro = self.genes[0:cutpoint] + other[cutpoint:]
        else:
            new_chro = other[0:cutpoint] + self.genes[cutpoint:]
        return new_chro

    def spawn_new_agent(self, name, chromosome):
        self.mts.ams.start_agent(GaitAgent, name, chromosome=chromosome)

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
        #self.add_behaviour(TellAgentMigrateBehaviour())

