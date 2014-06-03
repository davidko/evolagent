#!/usr/bin/env python

from spyse.core.protocols.query import QueryInitiatorBehaviour
import logging

class GetDfServicesBehaviour(QueryInitiatorBehaviour):
    def setup(self, provider_results=[]):
        self.__provider_results = provider_results

    def handle_no_participant(self):
        logging.warning('Error: Could not send message to DF')

    def handle_response(self):
        pass

    def handle_inform(self, content):
        self.agent.peer_agents = content
        self.__provider_results[:] = []
        self.__provider_results += content

