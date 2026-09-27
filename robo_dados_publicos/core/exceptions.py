class RobotStop(RuntimeError):
    """Parada deliberada por regra de segurança ou evidência insuficiente."""

class UnknownSchemaStop(RobotStop):
    pass

class EvidenceInsufficient(RobotStop):
    pass
