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
import threading

import evolagent

class ReportFitnessBehaviour(Behaviour):
    def action(self):
        # Report our fitness to the master agent
        msg = ACLMessage(performative=ACLMessage.INFORM)
        content = { 'fitness':self.agent.fitness, 
                    'chromosome':self.agent.genes}
        msg.content = serpent.dumps(content)
        msg.receivers = [ AID('MasterAgent') ]
        msg.protocol = 'report_fitness'
        self.agent.send_message(msg)
        self.set_done()

class ComputeFitnessBehaviour(Behaviour):
    def action(self):
        logging.info('{0} Begin compute fitness.'.format(self.agent.name))
        self.agent.fitness = self.agent.run_fitness_function()
        logging.info(
            '{0} Done computing fitness, sent report to Master'.format(
                self.agent.shortname))
        self.set_done()

class SelectMateBehaviour(ContractNetInitiatorBehaviour):
    def __init__(self, *args, **kwargs):
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
            list(map(lambda x: x.sender, proposals))))
        try:
            return max(proposals, key=lambda x: x.content['fitness'])
        except:

            logging.exception('Could not select proposal.')
            return None

    def process_result(self, result=None):
        # result should be a Chromosome, if it is a result.
        if result is None:
            return
        # Create a new child here, TODO
        logging.info('{0} Creating new child! {1}'.format(
            self.agent.name,
            result.content))
        new_chro=self.agent.crossover(result.content['chromosome'])
        self.agent.spawn_new_agent(
            'gaitagent-{0}'.format(str(uuid.uuid4())),
            new_chro)
        """
        self.agent.mts.ams.start_agent(
            EvolAgent, 
            'gaitagent-{0}'.format(str(uuid.uuid4())),
            chromosome=new_chro)
        """

class MateInitiatorBehaviour(SequentialBehaviour):
    MAX_PROPOSALS = 3
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
        self.add_behaviour(SelectMateBehaviour(
            deadline=time.time()+30,
            providers=self.evol_agents)) 

class MateParticipantBehaviour(ContractNetParticipantBehaviour):
    def make_proposal(self, call):
        logging.info(
            '{0} making proposal to {1}'.format(
                self.agent.name, call.sender))
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
        result['chromosome'] = self.agent.genes
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
            self.result_msg = self.agent.genes
        elif content == 'reproduce':
            self.result_msg = None
            logging.info(
                '{0} received reproduce message.'.format(self.agent.name))
            self.agent.add_behaviour(MateInitiatorBehaviour())
        elif content == 'migrate':
            self.result_msg = None
            logging.info(
                '{0} received migrate message. Remote agencies: {1}'.format(
                    self.agent.name,
                    self.agent.mts.ams.find_others()))
            self.agent.migrate()

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
        logging.info('{0} terminating...'.format(self.agent.name))
        self.agent.die()

class MigrateBehaviour(Behaviour):
    def action(self):
        # Send an unregister message to the Master
        msg = ACLMessage(performative=ACLMessage.INFORM)
        msg.content = serpent.dumps(self.agent.aid)
        msg.receivers = [ AID('MasterAgent') ]
        msg.protocol = 'unregister'
        self.agent.send_message(msg)
        remote_ams = self.agent.choose_remote_ams()
        logging.info('{0} emigrating...'.format(self.agent.name))
        self.agent.move(remote_ams)
        self.set_done()

class EvolAgent(Agent):
    fitness_function_lock = threading.Condition()
    fitness_function_num_instances = 0
    fitness_function_max_instances = 4
    def setup(self, chromosome=None, fitness=None):
        self.init_stage1_behaviours(chromosome, fitness)
        self.init_stage2_behaviours()

    def init_stage1_behaviours(self, chromosome=None, fitness=None):
        if chromosome is None:
            chromosome = [random.randint(0, 255) for _ in range(120)]
       
        self.genes = chromosome
        self.add_behaviour(ComputeFitnessBehaviour())

    def init_stage2_behaviours(self):
        behaviours = SequentialBehaviour()
        behaviours.add_behaviour(ReportFitnessBehaviour())
        behaviours.add_behaviour(
            RegisterServiceBehaviour(service=Service('EvolAgent')))
        self.add_behaviour(behaviours)
        self.add_behaviour(EvolAgentHandleRequestBehaviour())
        self.add_behaviour(MateParticipantBehaviour())

    def migrate(self):
        seq = SequentialBehaviour()
        seq.add_behaviour(UnregisterServiceBehaviour(service=Service('EvolAgent')))
        seq.add_behaviour(MigrateBehaviour())
        self.add_behaviour(seq)
        logging.info('{0} added migration behaviour...'.format(self.name))

    def execute(self):
        """ This method is executed after an agent migration. """
        logging.info('{0} immigrated here.'.format(self.agent.name))
        self.init_stage2_behaviours()

    def choose_remote_ams(self):
        amss = self.mts.ams.find_others()
        ams = random.choice(list(amss))
        return ams

    def __get_genes(self):
        return self._genes

    def __set_genes(self, genes):
        self._genes = genes

    genes = property(__get_genes, __set_genes, None, "list of genes")
    
    def run_fitness_function(self):
        EvolAgent.fitness_function_lock.acquire()
        logging.info('Lock.')
        while EvolAgent.fitness_function_num_instances >= \
            EvolAgent.fitness_function_max_instances:
                EvolAgent.fitness_function_lock.wait()

        EvolAgent.fitness_function_num_instances += 1
        logging.info("Running fitness function...  {0}".format(
            EvolAgent.fitness_function_num_instances))
        EvolAgent.fitness_function_lock.release()

        fitness = self.fitness_function()

        EvolAgent.fitness_function_lock.acquire()
        EvolAgent.fitness_function_num_instances -= 1
        EvolAgent.fitness_function_lock.notify_all()
        logging.info('Unlock.')
        EvolAgent.fitness_function_lock.release()
        self.fitness = fitness
        return fitness

    def fitness_function(self):
        """ Override this function to return the fitness of the chromosome."""
        raise Exception('fitness_function() must be overridden.')

    def crossover(self, other):
        """ Override this function to return the perform a crossover with
        another chromosome. """
        raise Exception('crossover() must be overridden.')

    def spawn_new_agent(self, name, chromosome):
        """ Override this function to start a new agent with the
        given chromosome. """
        raise Exception('spawn_new_agent() must be overridden.')

