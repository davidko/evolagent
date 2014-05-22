#!/usr/bin/env python

import random
import tempfile
import subprocess
import math
import threading

from spyse.core.agents.aid import AID
from spyse.core.agents.agent import Agent
from spyse.app.app import App
from spyse.core.protocols.request import RequestInitiatorBehaviour, \
    RequestParticipantBehaviour
from spyse.core.protocols.query import QueryInitiatorBehaviour
from spyse.core.behaviours.behaviours import TickerBehaviour, SendBehaviour, \
    Behaviour, ReceiveBehaviour
from spyse.core.behaviours.composite import SequentialBehaviour
from spyse.core.platform.df import Service
from spyse.core.content.content import ACLMessage, MessageTemplate

from evolagent import Chromosome

import datetime
import time
import serpent

import logging

def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M')

logging.basicConfig(filename='logfile-{0}.log'.format(timestamp()),
    level=logging.DEBUG)

class GaitChromosome(Chromosome):
    fitness_function_lock = threading.Condition()
    fitness_function_num_instances = 0
    fitness_function_max_instances = 4

    def fitness_function(self):
        cls = self.__class__
        cls.fitness_function_lock.acquire()
        while cls.fitness_function_num_instances > \
            cls.fitness_function_max_instances:
                cls.fitness_function_lock.wait()

        cls.fitness_function_num_instances += 1
        cls.fitness_function_lock.release()

        # First, save fitness to a temporary file
        f = tempfile.NamedTemporaryFile()
        f.write(str(self).encode('utf-8'))
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
        cls.fitness_function_lock.acquire()
        cls.fitness_function_num_instances -= 1
        cls.fitness_function_lock.notify_all()
        cls.fitness_function_lock.release()
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

class GetDfServicesBehaviour(QueryInitiatorBehaviour):
    def handle_no_participant(self):
        print('Error: Could not send message to DF')

    def handle_response(self):
        print('Got response from DF.') 

    def handle_inform(self, content):
        print('Recived: {0} from DF'.format(content))
        self.agent.peer_agents = content

    def handle_agree(self):
        print('Got agree.')

    def handle_failure(self):
        print('Got failure.')

    def cancel(self):
        print('Got cancel.')

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

class GaitAgentHandleRequestBehaviour(RequestParticipantBehaviour):
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
        else:
            self.dieflag = False

        return True

    def send_result(self):
        return self.result_msg

class GaitAgent(Agent):
    def setup(self, chromosome=None, fitness=None):
        if chromosome is None:
            chromosome = [random.randint(0, 255) for _ in range(120)]
        
        self.chromosome = GaitChromosome(chromosome)
        behaviours = SequentialBehaviour()
        behaviours.add_behaviour(ComputeFitnessBehaviour())
        behaviours.add_behaviour(
            RegisterServiceBehaviour(service=Service('EvolAgent')))
        behaviours.add_behaviour(GaitAgentHandleRequestBehaviour())
        self.add_behaviour(behaviours)

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

class GetDfServicesTicker(TickerBehaviour):
    def setup(self, service):
        self.service = service
    def on_tick(self):
        print('Polling df...')
        self.agent.add_behaviour(GetDfServicesBehaviour(store=AID('DF'),
            request=self.service))

class KillAgentTicker(TickerBehaviour):
    def on_tick(self):
        print ('Current list of agents and fitnesses:')
        for entry in self.agent.sorted_fitnesses:
            print entry['fitness']
        # Kill the weakest agent
        try:
            agent = self.agent.sorted_fitnesses.pop(0)['agent_id']
            print('Sending kill command to {0}...'.format(agent))
            self.agent.add_behaviour(
                RequestInitiatorBehaviour(
                    store=agent,
                    request='die'))
            # Need to remove entry for that entry in our list
            
        except:
            pass

class ReceiveAgentFitnessBehaviour(ReceiveBehaviour):
    def __init__(self, **namedargs):
        template = MessageTemplate(performative=MessageTemplate.INFORM)
        template.protocol = 'report_fitness'
        super(ReceiveAgentFitnessBehaviour, self).__init__(
            template=template, **namedargs)

    def handle_message(self, message):
        print('Master got fitness from agent: {0}'.format(message.content))
        try:
            content = serpent.loads(message.content)
            self.agent.fitness_datastore[message.sender] = \
                { 'timestamp':time.time(),
                  'fitness':content['fitness'],
                  'chromosome':content['chromosome'] }
            logging.info('{0} reports fitness {1}'.format(message.sender,
                content['fitness']))
            # Create sorted list of fitnesses
            self.agent.sorted_fitnesses = []
            for (sender_id, item) in self.agent.fitness_datastore.items():
                self.agent.sorted_fitnesses.append( {
                    'agent_id':sender_id,
                    'fitness':item['fitness'],
                    'chromosome':item['chromosome'] } )
            self.agent.sorted_fitnesses.sort(
                key=lambda x: x['fitness'] )

        except: 
            pass

class MasterAgent(Agent):
    def setup(self):
        self.add_behaviour(GetDfServicesTicker(service=Service('EvolAgent')))
        self.add_behaviour(KillAgentTicker())
        self.add_behaviour(ReceiveAgentFitnessBehaviour())
        self.fitness_datastore = {}
        self.sorted_fitnesses = []
    
        
class MyApp(App):
    def run(self, args):
        for i in range(10):
            self.start_agent(GaitAgent, 'gaitagent{0}'.format(i))
        #self.start_agent(MasterAgent, 'agent2')
        #self.start_agent(MasterAgent, 'agent3')
        self.start_agent(MasterAgent, 'MasterAgent')

if __name__=="__main__":
    MyApp()
