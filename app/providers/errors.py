"""Errors the outside services can cause. The learner never sees the detail."""


class ServiceDown(Exception):
    """A service failed, was too slow, or sent something unusable, even after
    one retry. `service` is "judging" or "speech"."""

    def __init__(self, service: str, detail: str = ""):
        super().__init__(f"{service}: {detail}")
        self.service = service
