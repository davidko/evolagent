#!/usr/bin/env python

"""
Spyse demonstration of the ContractNet protocol, modelled after the JADE bookTrading demo

When run, the demo starts three agents: a buyer and two sellers.  The buyer expresses a wish to purchase a book and the sellers make offers to sell that book at quoted prices.

To use, start the program and then enter "MAS" into the buyer's "Title" box.

To exit, press control-C.  FIXME: currently on GNU the app must be killed.
"""

from spyse.core.platform.df import Service
from spyse.core.agents.aid import AID
from spyse.core.agents.tkagent import TkinterAgent
from spyse.core.agents.agent import Agent
from spyse.core.behaviours.behaviours import Behaviour, TickerBehaviour, SendBehaviour, ReceiveBehaviour
from spyse.core.behaviours.composite import SequentialBehaviour
from spyse.core.content.content import ACLMessage
from spyse.core.protocols.contractnet import ContractNetInitiatorBehaviour, ContractNetParticipantBehaviour
from spyse.app.app import App

import time
import random
from sets import Set
from Tkinter import *

import Pyro4

Pyro4.config.SERIALIZER='pickle'
Pyro4.config.SERIALIZERS_ACCEPTED=['json', 'marshal', 'serpent', 'pickle']
Pyro4.config.SOCK_REUSE = True

class DummyBehaviour(Behaviour):
    def setup(self):
        self.i = 0

    def action(self):
        self.i += 1

class SearchServiceAgentsBehaviour(SendBehaviour):
    def setup(self, service):
        self.performative = ACLMessage.QUERY_REF
        self.receivers = [ AID('DF') ]
        self.content = service

class ReceiveServiceAgentsBehaviour(ReceiveBehaviour):

    def setup(self, datastore):
        self.datastore = datastore

    def handle_message(self, msg):
        # Overrides
        content = msg.content
        if content is not None:
            perf = msg.performative
            if perf == ACLMessage.INFORM:
                self.datastore['providers'] = content
        self.set_done()

class SearchSellerAgentsBehaviour(TickerBehaviour):
    def setup(self, datastore):
        self.datastore = datastore

    def setService(self, service):
        self.__service = service

    def on_action(self):
        pass
        #if (self.tick_count > 0) & (self.datastore['providers']!=[]):
        #    print "Providers found", self.datastore['providers']
            #self.set_done()

    def on_tick(self):
        self.agent.add_behaviour(SearchServiceAgentsBehaviour(service=self.__service))
        self.agent.add_behaviour(ReceiveServiceAgentsBehaviour(datastore=self.datastore))
        if (self.tick_count > 0) & (self.datastore['providers']!=[]):
            print "Providers found", self.datastore['providers']

class RegisterServiceBehaviour(SendBehaviour):
    def setup(self, service):
        self.performative = ACLMessage.REQUEST
        self.receivers = [ AID('DF') ]
        service = service
        self.content = service

class BookSellerAgent(Agent):
    def setup(self):
        self.datastore = {'providers':[]}
        self.__library = {}
        self.__library['MAS'] = random.randint(50, 150)
        service = Service('book-selling')
        self.add_behaviour(RegisterServiceBehaviour(service=service))
        search_behaviour=SearchSellerAgentsBehaviour(
            datastore=self.datastore,
            period=1)
        search_behaviour.setService(service)
        self.add_behaviour(search_behaviour)

class MyApp(App):
    def run(self, args):
        self.create_agent(BookSellerAgent, 'Bookseller A')
        self.create_agent(BookSellerAgent, 'Bookseller B')
        self.invoke_all_agents()

if __name__ == "__main__":
    MyApp()

