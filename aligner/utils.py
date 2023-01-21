import numpy as np
import pandas as pd

from common.reference import RUNE_WATCH_IDS
from common.utils.rune import get_client, get_watch_data


def load_data(neural_source, side, watch_id):
    raw_ins = pd.read_csv(
        neural_source,
        usecols=[0, 1, 2, 3], header=0, index_col=0
    )
    clean_ins = raw_ins[np.logical_not(np.isnan(raw_ins['accel_x']))]
    clean_ins.index /= 1000

    if 'left' in side or 'right' in side:
        watch_id = watch_id  # Made this a param for now, Todo: update common.reference
    else:
        raise KeyError('Unexpected neural source file! Could not parse side!')
    watch_params = {
        'patient_id': 'rcs07',  # Todo: make patient_id a param/config value for future patients
        'device_id': watch_id,
        'start_time': clean_ins.index[0],
        'end_time': clean_ins.index[-1]
    }
    watch_data = get_watch_data(get_client(), watch_params, 'accel').set_index('timestamp')

    return watch_data, clean_ins
