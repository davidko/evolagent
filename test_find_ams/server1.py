#!/usr/bin/env python

from spyse.core.agents.aid import AID
from spyse.core.agents.agent import Agent
from spyse.core.protocols.request import RequestInitiatorBehaviour, RequestParticipantBehaviour
from spyse.app.app import App
from spyse.core.behaviours.behaviours import TickerBehaviour

from random import randint
import time


class StoreAgent(Agent):
    def setup(self):
        self.add_behaviour(RequestParticipantBehaviour(
            send_response=self._send_response,
            perform_request=self._perform_request,
            send_result=self._send_result,
            cancel=self._cancel
        ))

    def _send_response(self):
        print "Agent", self.name, "sending response"
        
    def _perform_request(self, request):
        print "Agent", self.name, "performing request:",request
        return True

    def _cancel(self):
        print "Agent", self.name, "cancelling client's subscription"

    def _send_result(self):
        if randint(0,9) < 5:
            print "Agent", self.name, "sending inform-done"
            return None
        else:
            res = randint(0,9)
            print "Agent", self.name, "sending inform:",res
            return res

class CheckRemoteAmsTick(TickerBehaviour):
    def on_action(self):
        print(self.agent.ams.get_containers_info())

class CustomerAgent(Agent):
    def setup(self, store, request):
        self.add_behaviour(RequestInitiatorBehaviour(
            store=store,
            request=request,
            handle_no_participant=self._handle_no_participant,
            handle_response=self._handle_response,
            handle_agree=self._handle_agree,
            handle_refuse=self._handle_refuse,
            handle_inform=self._handle_inform,
            handle_inform_done=self._handle_inform_done,
            handle_failure=self._handle_failure,
            cancel=self._cancel,
            check_cancel=self._check_cancel
        ))

    def _handle_no_participant(self, participant):
        print "Agent", self.name, "could not find participant:",participant
        
    def _handle_response(self):
        print "Agent", self.name, "handling response"

    def _handle_agree(self):
        print "Agent", self.name, "handling agreement"

    def _handle_refuse(self):
        print "Agent", self.name, "handling refusal"

    def _handle_inform(self, content):
        print "Agent", self.name, "handling inform with result:", content
        
    def _handle_inform_done(self, content):
        print "Agent", self.name, "handling inform done"
        
    def _handle_failure(self):
        print "Agent", self.name, "handling failure"

    def _cancel(self):
        print "Agent", self.name, "cancelling my subscription"

    def _check_cancel(self):
        return False


class MyApp(App):
    def run(self, args):
        self.start_agent(StoreAgent, 'Pub')
        store=AID('Pub')
        request='gimme'
        self.start_agent(CustomerAgent, 'Red', store=store, request=request)
        self.start_agent(CustomerAgent, 'Hot', store=store, request=request)
        self.start_agent(CustomerAgent, 'Che', store=AID('NotExisting'), request=request)

if __name__ == "__main__":
    MyApp()
