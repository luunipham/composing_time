import abjad
from typing import Sequence
from scamp import TempoEnvelope
from importlib import resources

# ----------------------------- Abjad Utilities ---------------------------------

abjad_ily_path = resources.files('abjad.scm') / 'abjad.ily'

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

# the left tweaks don't start with a "-" because this is inserted by abjad
tempo_spanner_tweaks_left = r"""\tweak bound-details.left.text \markup \small {{\note {{ {note_type} }} #1 "= {tempo}"}} 
- \tweak bound-details.left-broken.text ##f"""

tempo_spanner_tweaks_left_parenthesized = r"""\tweak bound-details.left.text \markup \small {{"(" \note {{ {note_type} }} #1 "= {tempo})"}} 
- \tweak bound-details.left-broken.text ##f"""

# this is just concatenated to the left tweak, so does start with a "-"
tempo_spanner_tweaks_right_parenthesized = r"""- \tweak bound-details.right.text \markup \small {{"(" \note {{ {note_type} }} #1 "= {tempo})"}} 
- \tweak bound-details.right-broken.text ##f"""

tempo_spanner_padding_tweak = r"""- \tweak bound-details.right.padding #{}"""

tempo_markup = r"""\markup \small {{\note {{ {note_type} }} #1 "= {tempo}"}}"""

parenthesized_tempo_markup = r"""\markup \small {{ "(" \note {{ {note_type} }} #1 "= {tempo})"}}"""


def create_blank_score(measure_durs: Sequence[int], measure_times: Sequence[float],
                       tempo_envelope: TempoEnvelope) -> abjad.Score:
    """
    Create a blank score with the given list of measure durations.
    
    :param measure_durs: A list of measure durations in 16th notes
    :param measure_times: A corresponding list of measure durations in seconds (to account for tempo)
    :param tempo_envelope: A tempo envelope
    :return: An Abjad Score object containing measures with the specified time signatures.
    """
    score = abjad.Score()
    staff = abjad.Staff()
    
    time_signatures = [measure_dur_to_time_sig(dur) for dur in measure_durs]
    seconds_per_sixteenth = [t / dur for dur, t in zip(measure_durs, measure_times)]
    
    accumulated_beat = 0.0
    accumulated_time = 0.0
    for md, ts, sps, t in zip(measure_durs, time_signatures, seconds_per_sixteenth, measure_times):
        time_signature = abjad.TimeSignature(ts)
        measure = abjad.Voice(f"s1 * {ts[0]}/{ts[1]}")  # A whole rest placeholder
        
        # Format time as mm:ss
        minutes = int(accumulated_time // 60)
        seconds = int(accumulated_time % 60)
        timestamp_markup = abjad.Markup(f'"{minutes:02d}:{seconds:02d}"')
        abjad.attach(timestamp_markup, measure[0], direction=abjad.DOWN)

        # metronome_mark = abjad.MetronomeMark(abjad.Duration(1, 8),
        #                                      int(tempo_envelope.tempo_at(accumulated_beat)))
        # abjad.attach(metronome_mark, measure[0], direction=abjad.UP)
        
        # Attach tempo spacing adjustment
        abjad.attach(abjad.LilyPondLiteral(respace_text.format(spacing=sps * 4)), measure[0])
        abjad.attach(time_signature, measure[0])
        
        staff.append(measure)
        accumulated_beat += md
        accumulated_time += t  # Accumulate time for next measure

    tempo_voice = get_abjad_tempo_voice(tempo_envelope.scale_horizontal(0.25))
    tempo_staff = abjad.Staff([tempo_voice], name="TempoStaff")
    tempo_staff.remove_commands.extend([
        "Staff_symbol_engraver",  # Removes the actual staff lines
        "Clef_engraver",  # Removes the clef
        "Time_signature_engraver",  # Removes time signature
        "Bar_line_engraver"  # Removes bar lines
    ])
    abjad.override(tempo_staff).TextSpanner.Y_offset = -4
    abjad.override(tempo_staff).TextScript.Y_offset = -4

    score.append(tempo_staff)
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
        items=[rf'\include "{abjad_ily_path}"', layout_block, paper_block, score]
    )

    return lilypond_file


def get_abjad_tempo_voice(tempo_envelope: TempoEnvelope, parenthesized_end_offset=0.25):
    annotation_key_points = get_tempo_annotation_key_points(tempo_envelope)


    # list of (start_beat, end_beat, annotation_value)
    #    - always has start_beat
    #    - only arrow have end_beat
    #    - annotation_value is the abjad annotation e.g. MetronomeMark
    annotations = []

    last_tempo = None
    last_segment_was_constant_tempo = False

    for i in range(0, len(annotation_key_points), 2):
        start_kp, end_kp = annotation_key_points[i: i + 2]
        next_start_tempo = annotation_key_points[i + 2][1] if i + 2 < len(annotation_key_points) else None
        start_beat, start_tempo = start_kp
        end_beat, end_tempo = end_kp

        if start_tempo == end_tempo:  # constant segment
            if start_tempo != last_tempo or not last_segment_was_constant_tempo:
                annotations.append((
                    start_beat,
                    None,
                    abjad.Markup(
                        tempo_markup.format(note_type=8, tempo=round(start_tempo))
                    )
                ))
            last_segment_was_constant_tempo = True
        elif next_start_tempo is None or end_tempo != next_start_tempo:
            # not a constant segment, since the first if statement failed, and we need to note the end tempo, since it's
            # not going to be given at the start of the next segments (either because of subito change or end of score)
            tweaks = (tempo_spanner_tweaks_left_parenthesized
                      if start_tempo == last_tempo else tempo_spanner_tweaks_left).format(note_type=8,
                                                                                          tempo=round(start_tempo))
            tweaks += "\n" + tempo_spanner_tweaks_right_parenthesized.format(note_type=8, tempo=round(end_tempo))
            tweaks += "\n" + tempo_spanner_padding_tweak.format(1)
            right_before_end_beat = end_beat - parenthesized_end_offset
            annotations.append((
                start_beat,
                right_before_end_beat,
                abjad.StartTextSpan(
                    style=tweaks
                )
            ))
            last_segment_was_constant_tempo = False
        else:
            # not a constant segment, but the end tempo matches the beginning of the next segment, so just add a
            # metronome mark and and arrow
            tweaks = (tempo_spanner_tweaks_left_parenthesized
                      if start_tempo == last_tempo else tempo_spanner_tweaks_left).format(note_type=8,
                                                                                          tempo=round(start_tempo))
            tweaks += "\n" + tempo_spanner_padding_tweak.format(1)

            annotations.append((
                start_beat,
                end_beat,
                abjad.StartTextSpan(
                    style=tweaks
                )
            ))
            last_segment_was_constant_tempo = False
        last_tempo = end_tempo

    tempo_voice, beats_to_skip_objects = create_tempo_skip_voice(annotations)
    for start_beat, end_beat, annotation_object in annotations:
        if end_beat is not None:
            abjad.text_spanner([beats_to_skip_objects[start_beat], beats_to_skip_objects[end_beat]],
                               start_text_span=annotation_object)
        else:
            abjad.attach(annotation_object, beats_to_skip_objects[start_beat])

    return tempo_voice


def get_tempo_annotation_key_points(tempo_envelope: TempoEnvelope):
    annotations = []  # list of (beat, tempo_at_beat)
    b = 0
    for segment_duration in tempo_envelope.durations:
        if segment_duration == 0:
            continue
        annotations.append((b, tempo_envelope.tempo_at(b)))
        annotations.append((b + segment_duration, tempo_envelope.tempo_at(b + segment_duration, from_left=True)))
        b += segment_duration
    return annotations


def create_tempo_skip_voice(
        annotations,
        skip_duration=0.25,
        voice_name="TempoVoice"
):
    """
    Creates a voice filled with fixed-duration skips and maps annotation time points to the appropriate skips.

    Args:
        annotations: List of (start_beat, end_beat, annotation_value) tuples
        skip_duration: Duration of each skip (default: 16th note)
        voice_name: Name of the created voice

    Returns:
        A tuple containing:
        - abjad.Voice: The created voice filled with skips
        - dict: Mapping from annotation time points to skip objects
    """
    # Extract all time points from the annotations
    time_points = set()
    for start_beat, end_beat, _ in annotations:
        time_points.add(start_beat)
        if end_beat is not None:
            time_points.add(end_beat)

    # Sort the time points
    time_points = sorted(time_points)

    if not time_points:
        return abjad.Voice([], name=voice_name), {}

    # Find the maximum beat needed
    max_beat = max(time_points)

    # Create a list of skips that spans the entire duration
    skips = []
    beat_to_skip = {}  # Mapping from beats to skips

    current_beat = 0.0
    while current_beat <= max_beat:
        skip = abjad.Skip(skip_duration / 4)
        skips.append(skip)

        # Check if any annotation time points fall within this skip's duration
        for point in time_points:
            if current_beat <= point < current_beat + skip_duration:
                beat_to_skip[point] = skip

        current_beat += skip_duration

    # Create the voice
    voice = abjad.Voice(skips, name=voice_name)

    return voice, beat_to_skip


def measure_dur_to_time_sig(dur_in_16ths: int):
    if dur_in_16ths % 2 == 0:
        return dur_in_16ths // 2,  8
    else:
        return dur_in_16ths, 16
    