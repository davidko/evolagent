#!/usr/bin/env python

from spyse.core.agents.agent import Agent
from spyse.core.behaviours.fsm import FSMBehaviour, State
from spyse.core.behaviours.behaviours import Behaviour

class EvolAgent(Agent):
    def setup(self):
