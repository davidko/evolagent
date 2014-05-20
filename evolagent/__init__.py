#!/usr/bin/env python

from spyse.core.agents.agent import Agent
from spyse.core.behaviours.fsm import FSMBehaviour, State
from spyse.core.behaviours.behaviours import Behaviour

import random

class EvolError(Exception):
    def __init__(self, *args, **kwargs):
        super(EvolError, self).__init__(*args, **kwargs)

class Chromosome():
    def __init__(self, genes=None):
        self._genes = genes

    def crossover(self, other):
        if len(self.genes) != len(other.genes):
            raise EvolError('Gene lengths do not match.')
        cutpoint = random.randint(1, len(self.genes)-1)
        # Use a random number to determine whose genes go first during
        # crossover
        if random.randint(0, 1):
            new_chro = self.genes[0:cutpoint] + other.genes[cutpoint:]
        else:
            new_chro = other.genes[0:cutpoint] + self.genes[cutpoint:]
        return Chromosome(newchro)

    def __get_genes(self):
        return self._genes

    def __set_genes(self, genes):
        self._genes = genes

    genes = property(__get_genes, __set_genes, None, "list of genes")

    def fitness_function(self):
        raise Exception('fitness_function() must be overridden.')

class EvolAgent(Agent):
    def setup(self, chromosome):
        pass
