#!/usr/bin/env python

from spyse.core.agents.agent import Agent
from spyse.core.behaviours.fsm import FSMBehaviour, State
from spyse.core.behaviours.behaviours import Behaviour

from evolagent.agent import EvolAgent
from evolagent.masteragent import MasterAgent
import evolagent.behaviours

import random
import threading
import logging

class EvolError(Exception):
    def __init__(self, *args, **kwargs):
        super(EvolError, self).__init__(*args, **kwargs)

class Chromosome():
    fitness_function_lock = threading.Condition()
    fitness_function_num_instances = 0
    fitness_function_max_instances = 4

    def __init__(self, genes=None, agent=None):
        self._genes = genes
        self._fitness = None
        #self.agent = agent

    def __str__(self):
        if self._genes is None:
            return 'None'
        else:
            return '\n'.join(map(str, self.genes))

    def crossover(self, other):
        "Override this function..."
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
        return Chromosome(new_chro)

    def __get_genes(self):
        return self._genes

    def __set_genes(self, genes):
        self._genes = genes

    genes = property(__get_genes, __set_genes, None, "list of genes")

    def run_fitness_function(self):
        cls = self.__class__
        cls.fitness_function_lock.acquire()
        logging.info('Lock.')
        while cls.fitness_function_num_instances >= \
            cls.fitness_function_max_instances:
                cls.fitness_function_lock.wait()

        cls.fitness_function_num_instances += 1
        logging.info("Running fitness function...  {0}".format(
            cls.fitness_function_num_instances))
        cls.fitness_function_lock.release()

        fitness = self.fitness_function()

        cls.fitness_function_lock.acquire()
        cls.fitness_function_num_instances -= 1
        cls.fitness_function_lock.notify_all()
        logging.info('Unlock.')
        cls.fitness_function_lock.release()
        #logging.info("{0} Finished fitness function.".format(self.agent.name))

        return fitness

    def fitness_function(self):
        """ Override this function to return the fitness of the chromosome."""
        raise Exception('fitness_function() must be overridden.')

