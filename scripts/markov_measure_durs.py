from typing import Sequence
import random


def make_markov_measure_durs(transition_dict: dict[int, Sequence[int]],
                             num_measures: int = None,
                             total_beats: int = None) -> list[int]:

    measure_dur_space = list(transition_dict.keys())
    measure_durs_list = [random.choice(measure_dur_space)]
    if (num_measures is None and total_beats is None) or (num_measures is not None and total_beats is not None):
        raise ValueError("Exactly one of 'num_measures' or 'total_beats' must be specified")
    
    elif (num_measures is not None):
            measure = 1
            while measure < num_measures:
                last_measure_dur = measure_durs_list[-1]
                options_for_next_measure_dur = transition_dict[last_measure_dur]
                next_measure_dur = random.choice(options_for_next_measure_dur)
                measure_durs_list.append(next_measure_dur)
                measure += 1
            return measure_durs_list
    else:
              beat = (measure_durs_list[0] / 2)
              while beat < total_beats:
                  last_measure_dur = measure_durs_list[-1]
                  options_for_next_measure_dur = transition_dict[last_measure_dur]
                  next_measure_dur = random.choice(options_for_next_measure_dur)
                  measure_durs_list.append(next_measure_dur)
                  beat += (next_measure_dur / 2)
              return measure_durs_list
                  
mark = {
    2: (3, 2, 4),
    3: (2, 3, 4),
    4: (2, 3, 4)
}

print(make_markov_measure_durs(mark, total_beats=30))


def rotate_measure_durs(measure_durs: list[int]) -> list[int]:
    pass


def rescale_measure_durs(measure_durs: list[int], add_amount: int = None, mul_factor: float = None):
    """
    Adds/subtracts or multiplies (and rounds) measure durations
    """
    pass



