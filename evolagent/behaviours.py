#!/usr/bin/env python

from spyse.core.protocols.query import QueryInitiatorBehaviour

class GetDfServicesBehaviour(QueryInitiatorBehaviour):
    def setup(self, datastore={}):
        self.__datastore = datastore

    def handle_no_participant(self):
        print('Error: Could not send message to DF')

    def handle_response(self):
        print('Got response from DF.') 

    def handle_inform(self, content):
        print('Recived: {0} from DF'.format(content))
        self.agent.peer_agents = content
        self.__datastore['providers'] = content

    def handle_agree(self):
        print('Got agree.')

    def handle_failure(self):
        print('Got failure.')

    def cancel(self):
        print('Got cancel.')

