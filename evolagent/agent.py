#!/usr/bin/env python

from spyse.core.behaviours.behaviours import SendBehaviour, Behaviour
from spyse.core.behaviours.composite import SequentialBehaviour
from spyse.core.protocols.contractnet import ContractNetInitiatorBehaviour, \
    ContractNetParticipantBehaviour
from spyse.core.protocols.request import RequestInitiatorBehaviour, \
    RequestParticipantBehaviour
from spyse.core.agents.agent import Agent
from spyse.core.platform.df import Service
from spyse.core.content.content import ACLMessage, MessageTemplate
from spyse.core.agents.aid import AID

import random
import serpent
import logging

import evolagent

class ComputeFitnessBehaviour(Behaviour):
    def action(self):
        self.agent.fitness = self.agent.chromosome.fitness_function()
        # Report our fitness to the master agent
        msg = ACLMessage(performative=ACLMessage.INFORM)
        content = { 'fitness':self.agent.fitness, 
                    'chromosome':self.agent.chromosome}
        msg.content = serpent.dumps(content)
        msg.receivers = [ AID('MasterAgent') ]
        msg.protocol = 'report_fitness'
        self.agent.send_message(msg)
        self.set_done()

class MateBehaviour(SequentialBehaviour):
    MAX_PROPOSALS = 10
    class TrimProvidersBehaviour(Behaviour):
        def setup(self, datastore, max_providers = 10):
            self.__max_providers = max_providers
            self.__datastore = datastore

        def action(self):
            self.__datastore['providers'] = random.sample(
                self.__datastore['providers'], self.__max_providers)
            
    class SelectMateBehaviour(ContractNetInitiatorBehaviour):
        def setup(self):
            pass

        def select_proposal(self, proposals):
            # Just select the best one
            best_fitness = 0
            best_proposal = None
            for proposal in proposals:
                if proposal['fitness'] > best_fitness:
                    best_fitness = proposal['fitness']
                    best_proposal = proposal
            return best_proposal

        def process_result(self, result=None):
            # result should be a Chromosome, if it is a result.
            if result is None:
                return
            # Create a new child here, TODO

    def __init__(self, *args, **kwargs):
        super(MateBehaviour, self).__init__(*args, **kwargs)
        # First, get df services
        if 'datastore' in kwargs:
            datastore = kwargs['datastore']
        else:
            datastore = {}
        self.add_behaviour(GetDfServicesBehaviour(store=AID('DF'),
            request=Service('EvolAgent'),
            datastore=datastore))
        # Trim the list of potential providers to a more managable number
        self.add_behaviour(TrimProvidersBehaviour(datastore=datastore,
            max_providers = MAX_PROPOSALS))
        # Next, choose a remote agent and get its fitness/chromosome
        # This is the Contract-Net protocol. 
        self.add_behaviour(SelectMateBehaviour()) 

class EvolAgentHandleRequestBehaviour(RequestParticipantBehaviour):
    def perform_request(self, content):
        if content == 'die':
            seq = SequentialBehaviour()
            seq.add_behaviour(
                UnregisterServiceBehaviour(service=Service('EvolAgent')))
            seq.add_behaviour(
                DieBehaviour() )
            self.agent.add_behaviour(seq)
            self.dieflag = True
            self.result_msg = None
        elif content == 'fitness':
            self.result_msg = self.agent.fitness
        elif content == 'genes':
            self.result_msg = self.agent.chromosome
        elif content == 'reproduce':
            self.result_msg = None
            logging.info(
                '{0} received reproduce message.'.format(self.agent.name))
        else:
            self.dieflag = False

        return True

    def send_result(self):
        return self.result_msg

class RegisterServiceBehaviour(SendBehaviour):
    def setup(self, service):
        self.performative = ACLMessage.REQUEST
        self.receivers = [ AID('DF') ]
        service = service
        self.content = service

class UnregisterServiceBehaviour(SendBehaviour):
    def setup(self, service):
        self.performative = ACLMessage.CANCEL
        self.receivers = [ AID('DF') ]
        service = service
        self.content = service

class DieBehaviour(Behaviour):
    def action(self):
        self.agent.die()

class EvolAgent(Agent):
    def setup(self, ChromosomeClass=None, chromosome=None, fitness=None):
        if chromosome is None:
            chromosome = [random.randint(0, 255) for _ in range(120)]
       
        self._chromosome_class = ChromosomeClass
        self.chromosome = ChromosomeClass(chromosome)
        if not isinstance(self.chromosome, evolagent.Chromosome):
            raise evolagent.EvolError('ChromosomeClass must subclass Chromosome.')
        behaviours = SequentialBehaviour()
        behaviours.add_behaviour(ComputeFitnessBehaviour())
        behaviours.add_behaviour(
            RegisterServiceBehaviour(service=Service('EvolAgent')))
        behaviours.add_behaviour(EvolAgentHandleRequestBehaviour())
        self.add_behaviour(behaviours)

