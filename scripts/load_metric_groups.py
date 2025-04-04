from metric_group import MetricGroup
import abjad

mg = MetricGroup.load_from_json("bar_config.json")

# print(mg.get_bar_lengths())
# print(mg.get_tempo_envelope().show_plot())

lilypond_file = mg.to_lilypond_file()
print(abjad.lilypond(lilypond_file))
abjad.show(mg.to_lilypond_file())
