import abjad
from typing import Sequence


# ----------------------------- Abjad Utilities ---------------------------------

layout_block_text = r"""
\context {{
    \Score
     proportionalNotationDuration = #(ly:make-moment {pdur_numerator}/{pdur_denominator})
}}
"""

paper_block_text = r"""
#(set-paper-size '(cons (* {width} in) (* {height} in)))
ragged-right = ##t
indent = #0
"""

respace_text = r"""
\newSpacingSection
\override Score.SpacingSpanner.spacing-increment = #{spacing}
"""


# TODO: make the bars empty and with proportional notation
# TODO: add breaks after a certain number of beats

def create_blank_score(measure_durs: Sequence[int], measure_times: Sequence[float]) -> abjad.Score:
    """
    Create a blank score with the given list of measure durations.
    
    :param measure_durs: A list of measure durations in 16th notes
    :param measure_times: A corresponding list of measure durations in seconds (to account for tempo)
    :return: An Abjad Score object containing measures with the specified time signatures.
    """
    score = abjad.Score()
    staff = abjad.Staff()
    
    time_signatures = [measure_dur_to_time_sig(dur) for dur in measure_durs]
    seconds_per_sixteenth = [t / dur for dur, t in zip(measure_durs, measure_times)]
    
    accumulated_time = 0.0  # Start time for first measure
    for ts, sps, t in zip(time_signatures, seconds_per_sixteenth, measure_times):
        time_signature = abjad.TimeSignature(ts)
        measure = abjad.Voice(f"s1 * {ts[0]}/{ts[1]}")  # A whole rest placeholder
        
        # Format time as mm:ss
        minutes = int(accumulated_time // 60)
        seconds = int(accumulated_time % 60)
        timestamp_markup = abjad.Markup(f'"{minutes:02d}:{seconds:02d}"')
        abjad.attach(timestamp_markup, measure[0], direction=abjad.UP)
        
        # Attach tempo spacing adjustment
        abjad.attach(abjad.LilyPondLiteral(respace_text.format(spacing=sps * 4)), measure[0])
        abjad.attach(time_signature, measure[0])
        
        staff.append(measure)
        accumulated_time += t  # Accumulate time for next measure
    
    score.append(staff)
    
    return score



def create_blank_lilypond_file(score: abjad.Score, proportional_duration: tuple[int, int] = (1, 20), 
                               page_size_in: tuple[float, float] = (17, 11)) -> abjad.LilyPondFile:
    
    # Set proportional notation
    layout_block = abjad.Block("layout")
    layout_block.items.append(
        layout_block_text.format(pdur_numerator=proportional_duration[0],
                                 pdur_denominator=proportional_duration[1])    
    )

    # Set page dimensions
    paper_block = abjad.Block("paper")
    paper_block.items.append(
        paper_block_text.format(width=page_size_in[0], height=page_size_in[1])    
    )

    # Wrap everything in a Score with LilyPond headers
    lilypond_file = abjad.LilyPondFile(
        items=[layout_block, paper_block, score]
    )

    return lilypond_file


def measure_dur_to_time_sig(dur_in_16ths: int):
    if dur_in_16ths % 2 == 0:
        return (dur_in_16ths // 2,  8)
    else:
        return (dur_in_16ths, 16)
    