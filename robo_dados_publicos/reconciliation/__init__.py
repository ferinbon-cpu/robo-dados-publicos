from .planner import ReconciliationPlanner, ReconciliationTask
from .resolvers import LimeiraContractsResolver, TcespExpenseResolver, ReconciliationExecutor, ResolutionResult
from .contract_candidate_policy import install_fail_closed_contract_candidate_policy

# Candidate qualification is a separate semantic policy from public-form transport.
# Install it once at package import so every normal import path (including direct
# imports from reconciliation.resolvers) uses the same fail-closed rule without
# duplicating the stateful transport implementation.
install_fail_closed_contract_candidate_policy(LimeiraContractsResolver)

__all__ = [
    "ReconciliationPlanner", "ReconciliationTask", "LimeiraContractsResolver",
    "TcespExpenseResolver", "ReconciliationExecutor", "ResolutionResult",
]
