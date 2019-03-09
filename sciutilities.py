# coding:utf-8
"""Data filter."""

import numpy as np


def is_outlier(data, thresh=3.5):
    """Return a boolean array with Ture if data is outlier and False otherwise.

    Use double median absolute deviation.

    Arg:
        data:numpy ndarray.

    Return:
        A length consitent with data boolean array.
    """
    m = np.median(data)
    abs_md = np.abs(data - m)
    left_mad = np.median(abs_md[data <= m])
    rigth_mad = np.median(abs_md[data >= m])
    data_mad = np.zeros(len(data))
    data_mad[data <= m] = left_mad
    data_mad[data >= m] = rigth_mad
    modified_z_score = 0.6745 * abs_md / data_mad
    return modified_z_score > thresh
