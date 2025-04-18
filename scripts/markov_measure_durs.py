from typing import Sequence


def make_markov_measure_durs(transition_dict: dict[int, Sequence[int]],
                             num_measures: int = None,
                             total_beats: int = None) -> list[int]:
    """
    Takes a transition dictionary and produces a list of measure durations.
    """

    if (num_measures is None and total_beats is None) or (num_measures is not None and total_beats is not None):
        raise ValueError("Exactly one of 'num_measures' or 'total_beats' must be specified")


def rotate_measure_durs(measure_durs: list[int]) -> list[int]:
    pass


def rescale_measure_durs(measure_durs: list[int], add_amount: int = None, mul_factor: float = None):
    """
    Adds/subtracts or multiplies (and rounds) measure durations
    """
    pass



