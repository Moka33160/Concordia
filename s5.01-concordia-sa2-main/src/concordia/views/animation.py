"""
File: animation.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 09-09-2026
Description: The easing curve and the frame delay the animations use.
"""

FRAME_MS = 16
LIFT_STEP = 0.14


def ease_out_cubic(progress: float) -> float:
    """Ease a 0..1 progress out: quick to leave, gentle to arrive."""
    progress = min(1.0, max(0.0, progress))
    return 1 - (1 - progress) ** 3


def step_toward(current: float, target: float, step: float) -> float:
    """
    Walk a value one frame's worth towards its target, never past it.

    :param current: Where the value stands now.
    :param target: Where it is heading.
    :param step: The most it may move this frame.
    :return: The value after one frame.
    """
    if abs(target - current) <= step:
        return target
    return current + step if target > current else current - step
