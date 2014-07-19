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
import pickle
import evolagent

agent = evolagent.agent.EvolAgent('testagent', None, ChromosomeClass=evolagent.Chromosome)
mystr = pickle.dumps(agent)
