from luu_abjad_utils import create_blank_score, create_blank_lilypond_file
import random
import abjad
import itertools
from scamp import TempoEnvelope


# TODO:
# - Have tempo curve be an argument, and calculate measure times from that
# - Maybe? Figure out spacing increments that give actual proportions (warning rabbit hole)
# - Calculate system breaks/page breaks so that they happen at relatively regular intervals

# TODO: Figure out in lilypond how to scale the size of a measure without affecting anything else, just engraving.


measure_dur_transitions = {
    4: (4, 6),
    6: (4, 8, 10),
    8: (4, 6, 12),
    10: (4,),
    12: (8, 10, 12, 14),
    14: (14, 10),
}

# measure_dur_transitions = {
#     4 : (6, ),
#     6 : (8, ),
#     8 : (4, )
# }


def build_measure_list(
    transition_dict: dict[int, tuple[int, ...]],
    start_measure_dur: int,
    total_dur_in_seconds: float,
    tempo_envelope: TempoEnvelope | float = TempoEnvelope()
) -> list[int]:
    """
    Generate a list of measure durations based on transition rules.
    
    :param transition_dict: A dictionary mapping measure durations to possible next durations.
    :param start_measure_dur: The duration of the first measure in 16th notes.
    :param total_dur_in_seconds: The total duration of the generated measures in seconds.
    :param tempo_envelope: The tempo in beats per minute, where a beat is a quarter note.
    :return: A list of measure durations in 16th notes.
    """
    if not isinstance(tempo_envelope, TempoEnvelope):
        tempo_envelope = TempoEnvelope(tempo_envelope)
        
    measure_durs_list = []
    measure_times_list = []
    beat = 0
    t = last_t = 0
    while t < total_dur_in_seconds:
        if measure_durs_list:
            last_measure_dur = measure_durs_list[-1]
            options_for_next_measure_dur = transition_dict[last_measure_dur]
            next_measure_dur = random.choice(options_for_next_measure_dur)
        else:
            next_measure_dur = start_measure_dur
            
        measure_durs_list.append(next_measure_dur)
        beat += next_measure_dur * 0.25  # since next_measure_dur is in 16th notes
        t = tempo_envelope.time_at_beat(beat)
        measure_times_list.append(t - last_t)
        last_t = t
    return measure_durs_list, measure_times_list
        


measure_durs_list, measure_times_list = build_measure_list(
    measure_dur_transitions,
    4,
    150,
    TempoEnvelope((60, 180), (120,), duration_units="time")
)

score = create_blank_score(
    measure_durs_list,
    measure_times_list,
)

lilypond_file = create_blank_lilypond_file(score)

#abjad.show(score)
print(abjad.show(lilypond_file))