import numpy as np


def norm_columns(df, column_names=None):

    if column_names is None:
        column_names = col_names(df, exclude='time')

    squared = np.array([df[col]**2 for col in column_names]).T
    return np.sqrt(np.sum(squared, axis=1))


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