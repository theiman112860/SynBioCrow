class SynBioCrowError(RuntimeError): pass
class BackendUnavailableError(SynBioCrowError): pass
class BackendExecutionError(SynBioCrowError): pass
class ContractViolation(SynBioCrowError): pass
