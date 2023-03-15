import numpy as np
import pandas as pd


def load_csv(file_path, time_scale_to_seconds=1.0):
    raw_ins = pd.read_csv(
        file_path, header=0, index_col=0
    )
    raw_ins.index = pd.to_datetime(raw_ins.index / time_scale_to_seconds, unit='s')
    return raw_ins


def norm_df(df, column_names=None):
    """
    Convenience function to collapse multidimensional data into a single normed dimension

    If you have data from a 3-axis accelerometer, visualizing just on axis might miss information important for time
    alignment, and plotting all three axes at once gets confusing very quickly. Therefore, we can take the L2
    norm of all three axes to get one axis that conveys the 'magnitude' of acceleration at all timepoints

    :param df: long-form dataframe with data to normalize. Each column is a separate axis/dimension of the data
    :param column_names: The names of columns, as a list, to include in the L2 norm. by default will pull all columns
        except those including the word 'time'

    :return: DataFrame with the same index as the original dataframe but with only one data column, named 'values'
    which contains the L2 normed data.
    """

    if column_names is None:
        column_names = col_names(df, exclude='time')

    squared = np.array([df[col]**2 for col in column_names]).T
    normed = np.sqrt(np.sum(squared, axis=1))
    return pd.DataFrame(normed, index=df.index)


def timestamp_to_elapsed(timestamps, start=None):
    """Convert from pandas timestamps to time, in seconds, since the start of the recording"""
    start = start if start is not None else timestamps[0]
    return [t.total_seconds() for t in timestamps - start]


def col_names(df, exclude=None, include=None):
    """
    Extract the desired column names from a dataframe

    :param df:
    :param exclude: string. If this is included in the column name, that column is excluded
    :param include: string. If this is included in the column name, the column is included
    :return:
    """

    names = df.columns

    if include is not None:
        # Only include columns that include the include string in their names
        reduced_names = []
        for c in df.columns:
            try:
                if exclude in c:
                    reduced_names.append(c)
            except TypeError:
                pass
        names = reduced_names

    if exclude is not None:
        # Only include columns that do not include the exclude string in their names
        reduced_names = []
        for c in df.columns:
            try:
                if exclude not in c:
                    reduced_names.append(c)
            except TypeError:
                reduced_names.append(c)
        names = reduced_names

    return names