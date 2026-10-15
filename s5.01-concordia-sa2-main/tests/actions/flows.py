"""
File: flows.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Helpers to run a card action in a test and answer what it asks.
"""
from concordia.actions.drivers import run_flow


class Script:
    """Answers an action from a fixed list and records the requests."""

    def __init__(self, *answers):
        """
        :param answers: What to answer, in the order the action asks.
        """
        self.answers = list(answers)
        self.requests = []

    def __call__(self, request):
        """Answer one request, and note it down."""
        self.requests.append(request)

        if not self.answers:
            raise AssertionError(
                f"the action asked more than the script answers: "
                f"{type(request).__name__}({request.prompt!r})"
            )

        answer = self.answers.pop(0)

        return answer(request) if callable(answer) else answer

    @property
    def prompts(self) -> list[str]:
        """What the action asked, in order."""
        return [request.prompt for request in self.requests]

    @property
    def asked(self) -> list[str]:
        """The kind of every request the action made, in order."""
        return [type(request).__name__ for request in self.requests]


def run(flow, *answers) -> tuple[bool, Script]:
    """Drive an action to its end from a script."""
    script = Script(*answers)
    return run_flow(flow, script), script


def first(request):
    """Answer with the first option the request offered."""
    return request.options[0]


def last(request):
    """Answer with the last option the request offered."""
    return request.options[-1]


def option(key):
    """Answer with the branch carrying a given key."""
    def pick(request):
        for choice in request.options:
            if choice.key == key:
                return choice
        raise AssertionError(
            f"{key!r} was not offered: "
            f"{[choice.key for choice in request.options]}"
        )

    return pick


def named(name):
    """Answer with the option whose name matches, for cities and cards."""
    def pick(request):
        for choice in request.options:
            if getattr(choice, "name", choice) == name:
                return choice
        raise AssertionError(f"{name!r} was not offered")

    return pick


def stop_after(flow, *answers) -> Script:
    """Answer some of an action's questions, then give the card up."""
    script = Script(*answers)

    try:
        request = next(flow)

        while script.answers:
            request = flow.send(script(request))
    except StopIteration:
        raise AssertionError(
            "the action finished before the card could be given up"
        ) from None

    flow.close()

    return script
