#!/usr/bin/env python
import pickle
from spyse.core.protocols.contractnet import ContractNetInitiatorBehaviour, \
    ContractNetParticipantBehaviour, MakeProposalBehaviour

from evolagent.agent import MateParticipantBehaviour, MateInitiatorBehaviour

c = ContractNetInitiatorBehaviour()
pickle.dumps(c)
c = ContractNetParticipantBehaviour()
pickle.dumps(c)
c = MateParticipantBehaviour()
pickle.dumps(c)
c = MateInitiatorBehaviour()
pickle.dumps(c)

