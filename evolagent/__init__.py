#!/usr/bin/env python

from spyse.core.agents.agent import Agent
from spyse.core.behaviours.fsm import FSMBehaviour, State
from spyse.core.behaviours.behaviours import Behaviour

from evolagent.agent import EvolAgent
from evolagent.masteragent import MasterAgent
import evolagent.behaviours

import random

class EvolError(Exception):
    def __init__(self, *args, **kwargs):
        super(EvolError, self).__init__(*args, **kwargs)

class Chromosome():
    def __init__(self, genes=None):
        self._genes = genes
        self._fitness = None

    def __str__(self):
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

    def fitness_function(self):
        """ Override this function to return the fitness of the chromosome."""
        raise Exception('fitness_function() must be overridden.')

