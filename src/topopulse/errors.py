"""Domain-specific errors with actionable alignment context."""


class TopoPulseError(Exception):
    """Base class for package errors."""


class AlignmentError(TopoPulseError):
    """Base class for identifier/time alignment errors."""


class UnknownNodeError(AlignmentError):
    """Node data contains identifiers absent from the network."""


class MissingNodeDataError(AlignmentError):
    """Network nodes are absent from node data."""


class DuplicateNodeError(AlignmentError):
    """A node identifier is duplicated where uniqueness is required."""


class UnknownEdgeError(AlignmentError):
    """Edge data refers to an edge absent from the network."""


class TimeAlignmentError(AlignmentError):
    """Node and edge time coordinates cannot be aligned."""


class LabelMismatchError(AlignmentError):
    """Supplied labels do not match the data shape."""


class RenderingError(TopoPulseError):
    """Rendering or media encoding failed."""
