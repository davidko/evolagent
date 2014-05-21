#!/usr/bin/env python

import random
import tempfile
import subprocess
import math

from spyse.core.agents.aid import AID
from spyse.core.agents.agent import Agent
from spyse.app.app import App
from spyse.core.protocols.request import RequestInitiatorBehaviour, RequestParticipantBehaviour
from spyse.core.protocols.query import QueryInitiatorBehaviour
from spyse.core.behaviours.behaviours import TickerBehaviour, SendBehaviour
from spyse.core.platform.df import Service
from spyse.core.content.content import ACLMessage

from evolagent import Chromosome

class GaitChromosome(Chromosome):
    def fitness_function(self):
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

    def handle_agree(self):
        print('Got agree.')

    def handle_failure(self):
        print('Got failure.')

    def cancel(self):
        print('Got cancel.')

class GetDfServicesTicker(TickerBehaviour):
    def setup(self, service):
        self.service = service
    def on_tick(self):
        print('Polling df...')
        self.agent.add_behaviour(GetDfServicesBehaviour(store=AID('DF'),
            request=self.service))

class GaitAgent(Agent):
    def setup(self):
        self.add_behaviour(GetDfServicesTicker(service=Service('EvolAgent')))

class RegisterServiceBehaviour(SendBehaviour):
    def setup(self, service):
        self.performative = ACLMessage.REQUEST
        self.receivers = [ AID('DF') ]
        service = service
        self.content = service

class ServiceProviderAgent(Agent):
    def setup(self):
        self.add_behaviour(
            RegisterServiceBehaviour(service=Service('EvolAgent')))
        self.add_behaviour(GetDfServicesTicker(service=Service('EvolAgent')))
    
        
class MyApp(App):
    def run(self, args):
        self.start_agent(GaitAgent, 'agent1')
        #self.start_agent(ServiceProviderAgent, 'agent2')
        #self.start_agent(ServiceProviderAgent, 'agent3')
        self.start_agent(ServiceProviderAgent, 'agent4')

if __name__=="__main__":
    MyApp()
