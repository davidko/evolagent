#!/usr/bin/env python

from spyse.core.protocols.query import QueryInitiatorBehaviour

class GetDfServicesBehaviour(QueryInitiatorBehaviour):
    def setup(self, provider_results=[]):
        self.__provider_results = provider_results

    def handle_no_participant(self):
        print('Error: Could not send message to DF')

    def handle_response(self):
        print('Got response from DF.') 

    def handle_inform(self, content):
        print('{0} Received: {1} from DF'.format(self.agent.name, content))
        self.agent.peer_agents = content
        self.__provider_results[:] = []
        self.__provider_results += content

    def handle_agree(self):
        print('Got agree.')

    def handle_failure(self):
        print('Got failure.')

    def cancel(self):
        print('Got cancel.')

