#!/usr/bin/env python

from spyse.core.agents.aid import AID
from spyse.core.agents.agent import Agent
from spyse.core.protocols.request import RequestInitiatorBehaviour, RequestParticipantBehaviour
from spyse.app.app import App
from spyse.core.behaviours.behaviours import TickerBehaviour

from random import randint
import time


class PollAgent(Agent):
    def setup(self):
        self.add_behaviour(CheckAms())

class CheckAms(TickerBehaviour):
    def on_tick(self):
        print(self.agent.mts.ams.find_agents())

class MyApp(App):
    def run(self, args):
        self.start_agent(PollAgent, 'Poll1')
        self.start_agent(PollAgent, 'Poll2')

if __name__ == "__main__":
    MyApp()
