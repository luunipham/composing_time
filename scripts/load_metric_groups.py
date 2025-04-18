from composing_time.metric_group import MetricGroup
import abjad

mg = MetricGroup.load_from_json("bar_config.json")


# print(mg.get_bar_lengths())
# from composing_time.abjad_utils import get_tempo_annotation_key_points, get_abjad_tempo_voice
# get_abjad_tempo_voice(mg.get_tempo_envelope())
# mg.get_tempo_envelope().show_plot()

lilypond_file = mg.to_lilypond_file()
print(abjad.lilypond(lilypond_file))
abjad.show(lilypond_file)
