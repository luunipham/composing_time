from abc import ABC, abstractmethod
from scamp import TempoEnvelope
import json
from .abjad_utils import create_blank_lilypond_file, create_blank_score
from itertools import accumulate


# lilypond: trying to make blank measures that are strictly proportional in width to the time
# that they take. So want to be able to have a floating poitn scaling factor set that, when 2
# doubles the width, when 3.4, makes it 3.4 times as wide etc.
# \override Score.SpacingSpanner.spacing-increment seems like it gets close, but isn't exact/has some distortion

# TODO:
# - Make clicktrack from metric group
# - add unit_dur to metric group class, so that it applies to self and all subgroups
# - Implement methods like total time for MetricGroup
# - Use this to generate notation
# - Some sort of printout or rendering of a metric group as a timeline


class MetricGroup(ABC):
    """Abstract base class for metric groups, with shared functionality."""

    @abstractmethod
    def get_bar_lengths(self) -> list[float]:
        pass

    @abstractmethod
    def get_tempo_envelope(self) -> TempoEnvelope:
        pass

    def total_beat_duration(self) -> float:
        """Returns the total number of beats across all bars."""
        return sum(self.get_bar_lengths())
    
    @classmethod
    def load_from_json(cls, file_path):
        with open(file_path, 'r') as f:
            return cls.parse_json(json.load(f))

    @classmethod
    def parse_json(cls, data: dict) -> "MetricGroup":
        """Recursively parses a JSON dictionary into a MetricGroup object."""
        if "subgroups" in data:
            return CompositeMetricGroup([cls.parse_json(subgroup) for subgroup in data["subgroups"]])
        else:
            return SimpleMetricGroup(
                bar_lengths=data["bar_lengths"],
                tempo_envelope=cls._parse_tempo_envelope(data)
            )

    @staticmethod
    def _parse_tempo_envelope(group: dict) -> TempoEnvelope:
        """Creates a TempoEnvelope from JSON, handling different formats."""
        if "tempo_envelope" in group:
            return TempoEnvelope(**group["tempo_envelope"])
        else:
            start_tempo = group["tempo"]
            end_tempo = group.get("end_tempo", start_tempo)
            curvature = group.get("tempo_curvature", 0)
            return TempoEnvelope(
                levels=[start_tempo, end_tempo],
                durations=[sum(group["bar_lengths"])],
                curve_shapes=[curvature]
            )

    def to_lilypond_file(self):
        bar_lengths_beats = self.get_bar_lengths()
        tempo_env = self.get_tempo_envelope()
        bar_line_location = list(accumulate([0] + bar_lengths_beats))
        bar_lengths_times = [
            tempo_env.time_at_beat(end_beat) - tempo_env.time_at_beat(start_beat)
            for start_beat, end_beat in zip(bar_line_location[:-1], bar_line_location[1:])
        ]
        
        score = create_blank_score(
            bar_lengths_beats,
            bar_lengths_times,
            tempo_env
        )

        return create_blank_lilypond_file(score)


class SimpleMetricGroup(MetricGroup):
    def __init__(self, bar_lengths: list[int], tempo_envelope: TempoEnvelope):
        self.bar_lengths = bar_lengths
        total_bar_length = self.total_beat_duration()
        self.tempo_envelope = (tempo_envelope.
                               extend_to(total_bar_length).
                               truncate_at(total_bar_length))

    def get_bar_lengths(self) -> list[int]:
        return self.bar_lengths

    def get_tempo_envelope(self) -> TempoEnvelope:
        return self.tempo_envelope


class CompositeMetricGroup(MetricGroup):
    def __init__(self, groups: list[MetricGroup]):
        self.groups = groups

    def get_bar_lengths(self) -> list[float]:
        return [bar for group in self.groups for bar in group.get_bar_lengths()]

    def get_tempo_envelope(self) -> TempoEnvelope:
        envelopes = [group.get_tempo_envelope() for group in self.groups]
        tempo_envelope = envelopes[0].duplicate()
        for te in envelopes[1:]:
            tempo_envelope.append_envelope(te)
        return tempo_envelope


if __name__ == '__main__':
    # Run some tests!
    # Simple metric group with a constant tempo
    simple1 = SimpleMetricGroup(
        bar_lengths=[5, 6, 2],
        tempo_envelope=TempoEnvelope(60)  # Constant tempo of 60 BPM
    )

    # Simple metric group with an accelerando
    simple2 = SimpleMetricGroup(
        bar_lengths=[4, 3, 1, 7],
        tempo_envelope=TempoEnvelope(levels=[60, 130], durations=[20])  # Accelerating from 60 to 130 BPM
    )

    # Composite metric group containing the two simple metric groups
    composite1 = CompositeMetricGroup(groups=[simple1, simple2])

    # Another SimpleMetricGroup with a tempo envelope defined in time
    simple3 = SimpleMetricGroup(
        bar_lengths=[5, 6, 2, 4],
        tempo_envelope=TempoEnvelope(levels=[60, 90, 40], durations=[2, 3], duration_units="time")
    )

    # Composite metric group containing a mix of simple and composite groups
    composite2 = CompositeMetricGroup(groups=[composite1, simple3])

    # Test outputs
    print("Simple1 Bar Lengths:", simple1.get_bar_lengths())
    print("Simple1 Tempo Envelope:", simple1.get_tempo_envelope())
    simple1.get_tempo_envelope().show_plot()

    print("Simple2 Bar Lengths:", simple2.get_bar_lengths())
    print("Simple2 Tempo Envelope:", simple2.get_tempo_envelope())
    simple2.get_tempo_envelope().show_plot()

    print("Composite1 Bar Lengths:", composite1.get_bar_lengths())
    print("Composite1 Tempo Envelope:", composite1.get_tempo_envelope())
    composite1.get_tempo_envelope().show_plot()

    print("Simple3 Bar Lengths:", simple3.get_bar_lengths())
    print("Simple3 Tempo Envelope:", simple3.get_tempo_envelope())
    simple3.get_tempo_envelope().show_plot()

    print("Composite2 Bar Lengths:", composite2.get_bar_lengths())
    print("Composite2 Tempo Envelope:", composite2.get_tempo_envelope())
    composite2.get_tempo_envelope().show_plot()
    
    
