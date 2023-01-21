from aligner.gui import manual_align


watch_acceleration = "watch_data.csv"
ins_acceleration = "ins_data.csv"
offsets = manual_align(watch_acceleration, ins=ins_acceleration)