"""Exceptions raised by topology builders."""


class TopologyBuildError(Exception):
    """Raised when a topology cannot be built from the supplied inputs."""


class TopologyObjectNotFoundError(Exception):
    """Raised when a requested object ID is not present in the topology."""

    def __init__(self, object_id: str) -> None:
        self.object_id = object_id
        super().__init__(f"Voice object not found in topology: {object_id}")
