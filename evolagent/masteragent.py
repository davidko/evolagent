#!/usr/bin/env python
from spyse.core.agents.agent import Agent
from spyse.core.behaviours.behaviours import TickerBehaviour, ReceiveBehaviour
from spyse.core.platform.df import Service
from spyse.core.content.content import MessageTemplate
from spyse.core.agents.aid import AID

import evolagent

class GetDfServicesTicker(TickerBehaviour):
    def setup(self, service, datastore={}):
        self.service = service
        self.__datastore = datastore

    def on_tick(self):
        print('Polling df...')
        self.agent.add_behaviour(
            evolagent.behaviours.GetDfServicesBehaviour(store=AID('DF'),
                request=self.service, datastore=self.__datastore))

class KillAgentTicker(TickerBehaviour):
    def on_tick(self):
        if self.agent.sorted_fitnesses is None or \
            len(self.agent.sorted_fitnesses) == 0:
                return
        print ('Current list of agents and fitnesses:')
        for entry in self.agent.sorted_fitnesses:
            print entry['fitness']
        # If there are too many agents, kill the weakest ones
        while len(self.agent.sorted_fitnesses) > self.agent.max_agent_population:
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
    def setup(self, max_agent_population=20):
        self.max_agent_population = max_agent_population
        self.datastore = {}
        self.df_datastore = {}
        self.add_behaviour(GetDfServicesTicker(service=Service('EvolAgent'),
            datastore=self.df_datastore))
        self.add_behaviour(KillAgentTicker())
        self.add_behaviour(ReceiveAgentFitnessBehaviour())
        self.fitness_datastore = {}
        self.sorted_fitnesses = []
    