class NorthstarPipelineError(Exception):
    """Base exception for Northstar pipeline failures."""

class DataQualityError(NorthstarPipelineError):
    """Raised when source data violates pipeline quality policy."""

class PipelineConfigurationError(NorthstarPipelineError):
    """Raised when pipeline configuration is invalid."""

class TransientPipelineError(NorthstarPipelineError):
    """Raised for temporary infrastructure failures."""

class InjectedPipelineFailure(NorthstarPipelineError):
    """Raised only for controlled pipeline integration testing."""