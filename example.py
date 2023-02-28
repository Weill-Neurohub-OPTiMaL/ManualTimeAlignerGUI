from aligner.gui import manual_align
from aligner.utils import load_csv, norm_df


watch = norm_df(load_csv('example_data/watch_accel.csv'))
rcs_left = norm_df(load_csv('example_data/rcs_left_accel.csv', time_scale_to_seconds=1000))
rcs_right = norm_df(load_csv('example_data/rcs_right_accel.csv', time_scale_to_seconds=1000))
offsets = manual_align(watch, rcs_left=rcs_left, rcs_right=rcs_right)
for name, value in offsets.items():
    print(f'{name} offset: {value}')
