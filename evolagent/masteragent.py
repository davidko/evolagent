#!/usr/bin/env python
from spyse.core.agents.agent import Agent
from spyse.core.behaviours.behaviours import TickerBehaviour, ReceiveBehaviour
from spyse.core.platform.df import Service
from spyse.core.content.content import MessageTemplate
from spyse.core.agents.aid import AID
from spyse.core.protocols.request import RequestInitiatorBehaviour

import random
import logging
import sets
import serpent
import time
import numpy

import evolagent

class ReproLottoTicker(TickerBehaviour):
    def setup(self, population=None, wait_ticks=3):
        self.__population = population
        self.__wait_ticks = wait_ticks

    def on_tick(self):
        if self.__wait_ticks:
            self.__wait_ticks -= 1
            return
        """
        try:
            if len(self.__population) > self.agent.max_agent_population:
                return
            agents = random.sample(
                self.__population,
                self.agent.max_agent_population - len(self.__population))
        except:
            agents = self.__population

        for agent in agents:
            logging.info('Master send Repro message to {0}'.format(agent))
            self.agent.add_behaviour(
                RequestInitiatorBehaviour(
                    store=agent,
                    request='reproduce'))
        """
        evolagent.Chromosome.fitness_function_lock.acquire()
        sample_n = evolagent.Chromosome.fitness_function_max_instances - \
            evolagent.Chromosome.fitness_function_num_instances
        evolagent.Chromosome.fitness_function_lock.release()
        agents = random.sample(self.__population, sample_n)
        for agent in agents:
            logging.info('Master send Repro message to {0}'.format(agent))
            self.agent.add_behaviour(
                RequestInitiatorBehaviour(
                    store=agent,
                    request='reproduce'))

class GetDfServicesTicker(TickerBehaviour):
    def setup(self, service, provider_results = None):
        self.service = service
        self.__provider_results = provider_results

    def on_tick(self):
        self.agent.add_behaviour(
            evolagent.behaviours.GetDfServicesBehaviour(store=AID('DF'),
                request=self.service, provider_results=self.__provider_results))

class KillAgentTicker(TickerBehaviour):
    def on_tick(self):
        if self.agent.sorted_fitnesses is None or \
            len(self.agent.sorted_fitnesses) == 0:
                return
        # If there are too many agents, kill the weakest ones
        while len(self.agent.sorted_fitnesses) > self.agent.max_agent_population:
            try:
                agent = self.agent.sorted_fitnesses.pop(0)['agent_id']
                logging.info('Sending kill command to {0}...'.format(agent))
                self.agent.add_behaviour(
                    RequestInitiatorBehaviour(
                        store=agent,
                        request='die'))
                # Need to remove entry for that entry in our list
                del self.agent.fitness_datastore[agent]
                
            except Exception as e:
                logging.exception('Could not kill agent(s).')
                pass

class ReceiveAgentFitnessBehaviour(ReceiveBehaviour):
    def __init__(self, **namedargs):
        self.__num_children = 0
        template = MessageTemplate(performative=MessageTemplate.INFORM)
        template.protocol = 'report_fitness'
        super(ReceiveAgentFitnessBehaviour, self).__init__(
            template=template, **namedargs)

    def handle_message(self, message):
        self.__num_children += 1
        logging.info('Master got fitness from agent: {0}'.format(message.content))
        #try:
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
        # Calculate mean fitness
        mean = numpy.mean( 
            map(lambda x: x['fitness'], self.agent.sorted_fitnesses))

        logging.info('MASTER AGENT DATA: {0} {1} {2} {3} {4} {5}'.format(
            time.time(),
            self.__num_children,
            self.agent.sorted_fitnesses[0]['fitness'],
            mean,
            self.agent.sorted_fitnesses[-1]['fitness'],
            self.population_diversity(self.agent.sorted_fitnesses)))

        #except: 
        #    pass


    def population_diversity(self, population):
        sums = [0 for _ in range(len(population[0]['chromosome']['_genes']))]
        for p in population:
            c = p['chromosome']['_genes']
            sums = [x+y for x,y in zip(sums, c)]
        centroids = map(lambda x: float(x) / len(population), sums)
        inertia = 0
        for i in range(len(sums)):
            s = 0
            for j in range(len(population)):
                s += (population[j]['chromosome']['_genes'][i] - \
                      centroids[i])**2
            inertia += s
        return inertia
        
class MasterAgent(Agent):
    def setup(self, max_agent_population=20):
        self.max_agent_population = max_agent_population
        self.datastore = {}
        self.df_datastore = {}
        self.evolagent_providers = []
        self.add_behaviour(GetDfServicesTicker(service=Service('EvolAgent'),
            provider_results=self.evolagent_providers))
        self.add_behaviour(KillAgentTicker())
        self.add_behaviour(ReceiveAgentFitnessBehaviour())
        self.add_behaviour(ReproLottoTicker(population=self.evolagent_providers))
        self.fitness_datastore = {}
        self.sorted_fitnesses = []
    
