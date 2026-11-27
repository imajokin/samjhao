"""Errors the outside services can cause. The learner never sees the detail."""


class ServiceDown(Exception):
    """A service failed, was too slow, or sent something unusable, even after
    one retry. `service` is "judging" or "speech"."""

    def __init__(self, service: str, detail: str = ""):
        super().__init__(f"{service}: {detail}")
        self.service = service


class DailyCap(ServiceDown):
    """Today's limit on paid model calls is used up."""

    def __init__(self):
        super().__init__("judging", "daily model-call cap reached")
