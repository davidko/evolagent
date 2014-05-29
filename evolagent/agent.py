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
import time
import uuid

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

class MateInitiatorBehaviour(SequentialBehaviour):
    MAX_PROPOSALS = 2
    class TrimProvidersBehaviour(Behaviour):
        def setup(self, providers=[], max_providers = 10):
            self.__max_providers = max_providers
            self.__providers = providers 

        def action(self):
            if len(self.__providers) > self.__max_providers:
                sample = random.sample( self.__providers, self.__max_providers)
                self.__providers[:] = []
                self.__providers += sample
                logging.info('{0} trimmed providers to {1}'.format(
                    self.agent.name,
                    self.__providers))
            self.set_done()
            
    class SelectMateBehaviour(ContractNetInitiatorBehaviour):
        def __init__(self, *args, **kwargs):
            logging.info('Select Mate Behaviour Init.')
            datastore = {}
            datastore['call'] = 'mate'
            datastore['providers'] = kwargs['providers']
            ContractNetInitiatorBehaviour.__init__(
                self,
                *args, 
                datastore=datastore,
                **kwargs)

        def setup(self, providers=None):
            pass

        def select_proposal(self, proposals):
            # Just select the best one
            logging.info('{0} received proposals: {1}'.format(
                self.agent.name,
                proposals))
            return max(proposals, key=lambda x: x.content['fitness'])

        def process_result(self, result=None):
            # result should be a Chromosome, if it is a result.
            if result is None:
                return
            # Create a new child here, TODO
            logging.info('{0} Creating new child! {1}'.format(
                self.agent.name,
                result.content))
            new_chro=self.agent.chromosome.crossover(result.content['chromosome'])
            self.agent.mts.ams.start_agent(
                EvolAgent, 
                'gaitagent-{0}'.format(str(uuid.uuid4())),
                ChromosomeClass=self.agent._chromosome_class,
                chromosome=new_chro.genes)

    def __init__(self, *args, **kwargs):
        super(MateInitiatorBehaviour, self).__init__(*args, **kwargs)
        # First, get df services
        if 'datastore' in kwargs:
            datastore = kwargs['datastore']
        else:
            datastore = {}
        self.evol_agents=[]
        self.add_behaviour(
            evolagent.behaviours.GetDfServicesBehaviour(store=AID('DF'),
                request=Service('EvolAgent'),
                provider_results=self.evol_agents))
        # Trim the list of potential providers to a more managable number
        self.add_behaviour(self.TrimProvidersBehaviour(
            providers=self.evol_agents,
            max_providers = self.MAX_PROPOSALS))
        # Next, choose a remote agent and get its fitness/chromosome
        # This is the Contract-Net protocol. 
        logging.info('Adding Select Mate Behaviour...')
        self.add_behaviour(self.SelectMateBehaviour(
            deadline=time.time()+10,
            providers=self.evol_agents)) 

class MateParticipantBehaviour(ContractNetParticipantBehaviour):
    def make_proposal(self, call):
        logging.info('{0} making proposal...'.format(self.agent.name))
        content = {}
        content['fitness'] = self.agent.fitness
        proposal = call.create_reply()
        proposal.content = content
        proposal.performative = ACLMessage.PROPOSE
        return proposal

    def execute_contract(self, conclusion):
        logging.info('{0} executing contract...'.format(self.agent.name))
        result = {}
        result['fitness'] = self.agent.fitness
        result['chromosome'] = self.agent.chromosome
        return result

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
            self.agent.add_behaviour(MateInitiatorBehaviour())
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
        self.add_behaviour(MateParticipantBehaviour())

