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
        msg.content = (self.agent.fitness, self.agent.chromosome)
        msg.receivers = [ AID('MasterAgent') ]
        self.agent.send_message(msg)
        self.set_done()

class GaitAgentHandleRequestBehaviour(RequestParticipantBehaviour):
    def perform_request(self, content):
        if content == 'die':
            self.agent.add_behaviour(
                UnregisterServiceBehaviour(service=Service('EvolAgent')))
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
        # Report fitness to master
        """
        behaviours.add_behaviour(
            SendBehaviour(
                performative=ACLMessage.INFORM,
                receivers=[ AID('MasterAgent') ],
                content=self.fitness))
        """
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

class GetDfServicesTicker(TickerBehaviour):
    def setup(self, service):
        self.service = service
    def on_tick(self):
        print('Polling df...')
        self.agent.add_behaviour(GetDfServicesBehaviour(store=AID('DF'),
            request=self.service))

class KillAgentTicker(TickerBehaviour):
    def on_tick(self):
        # Find a random agent and send it the kill message
        try:
            print('peer agents: {0}'.format(self.agent.peer_agents))
            agent = random.choice(self.agent.peer_agents)
            print('Sending kill command to {0}...'.format(agent))
            self.agent.add_behaviour(
                RequestInitiatorBehaviour(
                    store=agent,
                    request='die'))
        except:
            pass

class ReceiveAgentFitnessBehaviour(ReceiveBehaviour):
    def __init__(self, **namedargs):
        template = MessageTemplate(performative=MessageTemplate.INFORM)
        super(ReceiveAgentFitnessBehaviour, self).__init__(
            template=template, **namedargs)

    def handle_message(self, message):
        print('Master got fitness from agent: {0}'.format(message.content))
        self.agent.fitness_datastore[message.sender] = message.content

class MasterAgent(Agent):
    def setup(self):
        self.add_behaviour(GetDfServicesTicker(service=Service('EvolAgent')))
        #self.add_behaviour(KillAgentTicker())
        self.add_behaviour(ReceiveAgentFitnessBehaviour())
        self.fitness_datastore = {}
    
        
class MyApp(App):
    def run(self, args):
        for i in range(40):
            self.start_agent(GaitAgent, 'gaitagent{0}'.format(i))
        #self.start_agent(MasterAgent, 'agent2')
        #self.start_agent(MasterAgent, 'agent3')
        self.start_agent(MasterAgent, 'MasterAgent')

if __name__=="__main__":
    MyApp()
