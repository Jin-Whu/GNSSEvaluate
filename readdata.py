# coding:utf-8
"""Read file, include read coor file, corr file."""

import sys
import os
import glob
import re
import datetime
import pandas as pd
import numpy as np
from collections import defaultdict, OrderedDict


class Read(object):
    """Read data."""

    def readcoor(self, filepath, date):
        """Read coor file and produce report.

        Read coor file and calculate 'U_rms', 'N_rms', 'E_rms', 'H_rms',
        'U_95', 'N_95', 'E_95', 'H_95', 'effective_rate'.

        Args:
            filepath:coor files store path.
            date:coor file's date, type:datetime

        Returns:
            report:UNETH report, type:pandas.Dataframe.
        """
        doy = date.timetuple().tm_yday
        filelist = glob.glob(
            os.path.join(filepath, ''.join(
                ['*', '{:0>3d}.{:0>2d}'.format(doy, date.year % 100), 'coor'])))
        if not filelist:
            print("Can't find %s's coor file in %s" % (str(date), filepath))
            return None

        report = defaultdict(list)
        refname = re.compile(r'(\w+)\d{3}\.\d{2}coor')
        for path in filelist:
            station = refname.findall(path)[0]
            report['name'].append(station)
            try:
                data = pd.read_table(
                    path, delim_whitespace=True).apply(
                        pd.to_numeric, errors='coerce')
                if 'U' not in data or 'N' not in data or 'E' not in data:
                    raise ValueError
            except:
                report['U_rms'].append(0)
                report['N_rms'].append(0)
                report['E_rms'].append(0)
                report['H_rms'].append(0)
                report['U_95'].append(0)
                report['N_95'].append(0)
                report['E_95'].append(0)
                report['H_95'].append(0)
                report['effective_rate'].append(0)
                continue
            num = data.shape[0]
            if num == 0:
                report['U_rms'].append(0)
                report['N_rms'].append(0)
                report['E_rms'].append(0)
                report['H_rms'].append(0)
                report['U_95'].append(0)
                report['N_95'].append(0)
                report['E_95'].append(0)
                report['H_95'].append(0)
                report['effective_rate'].append(0)
                continue

            threshold_index = int(num * 0.95)
            u_rms = np.sqrt(data.U.pow(2).sum() / num)
            n_rms = np.sqrt(data.N.pow(2).sum() / num)
            e_rms = np.sqrt(data.E.pow(2).sum() / num)
            report['U_rms'].append(u_rms)
            report['N_rms'].append(n_rms)
            report['E_rms'].append(e_rms)
            data_H = np.sqrt((data.N.pow(2) + data.E.pow(2)))
            report['H_rms'].append(np.sqrt(data_H.pow(2).sum() / num))
            report['U_95'].append(data.U.abs().sort_values().iloc[
                threshold_index])
            report['N_95'].append(data.N.abs().sort_values().iloc[
                threshold_index])
            report['E_95'].append(data.E.abs().sort_values().iloc[
                threshold_index])
            report['H_95'].append(data_H.abs().sort_values().iloc[
                threshold_index])
            report['effective_rate'].append(num / 86400.0)

        cols = [
            'name', 'U_rms', 'N_rms', 'E_rms', 'H_rms', 'U_95', 'N_95', 'E_95',
            'H_95', 'effective_rate'
        ]
        report = pd.DataFrame(report, columns=cols).sort_values('name')
        return report

    def readsatnum(self, filepath, date):
        """Read satellite number of corr file.

        Args:
            filepath:correct file store path.
            date:correct file date, type:datetime.

        Return:
            sat_num:correct file satellite number data, type:dict.
        """
        date_s = ''.join(str(date).split('-'))
        # retrieve coorect files
        bds_corr = ''.join(['CorrBDS', date_s, '.txt'])
        gps_corr = ''.join(['CorrGPS', date_s, '.txt'])
        bds_files = glob.glob(os.path.join(filepath, bds_corr))
        gps_files = glob.glob(os.path.join(filepath, gps_corr))
        if not bds_files:
            print('Not find %s in %s' % (bds_corr, filepath))
        if not gps_files:
            print('Not find %s in %s' % (gps_corr, filepath))
        # start read
        sat_num = dict()
        for path in bds_files:
            sat_num['BDS'] = readSatNum(path, date, 'BDS')
        for path in gps_files:
            sat_num['GPS'] = readSatNum(path, date, 'GPS')

        return sat_num

    def readsatiode(self, filepath, date, prn):
        """Read satellite iode.

        Args:
            filepath:correct file store path.
            date:correct file date, type:datetime.
            prn:satellite prn.
        Return:
            satiode:satellite iode, type:OrderedDict.
        """
        # retrieve coorect files
        gsystem = 'GPS' if prn[0] == 'G' else 'BDS'
        correct_fname = ''.join(
            ['Corr', gsystem, ''.join(str(date).split('-')), '.txt'])
        correct_file = os.path.join(filepath, correct_fname)
        # start read
        if not os.path.exists(correct_file):
            print('Not find %s in %s' % (correct_fname, filepath))
            return None
        satiode = OrderedDict()
        day_flag = (date.timetuple().tm_wday + 1) % 7
        hour = 0
        readiode = False
        with open(correct_file) as f:
            for line in f:
                if line.startswith(gsystem):
                    time = int(line.split()[2])
                    day = datetime.timedelta(seconds=time).days
                    # convert week seconds to hour
                    if day_flag == day:
                        hour = datetime.timedelta(seconds=time).seconds / 3600.
                        readiode = True
                    else:
                        readiode = False
                if line.startswith(prn) and readiode:
                    satiode[hour] = int(line.split()[1])
        return satiode

    def readorbitc(self, filepath, date, prn):
        """Read orbit and clock errors.

        Args:
            filepath:correct file store path.
            date:correct file date.
            prn:satellite prn.

        Return:
            orbitc:orbit errors and clock errors, type:pd.DataFrame.
        """
        # retrieve coorect files
        gsystem = 'GPS' if prn[0] == 'G' else 'BDS'
        correct_fname = ''.join(
            ['Corr', gsystem, ''.join(str(date).split('-')), '.txt'])
        correct_file = os.path.join(filepath, correct_fname)
        # start read
        if not os.path.exists(correct_file):
            print('Not find %s in %s' % (correct_fname, filepath))
            return None

        orbitc = defaultdict(list)
        day_flag = (date.timetuple().tm_wday + 1) % 7
        hour = 0
        readorbit = False
        with open(correct_file) as f:
            for line in f:
                if line.startswith(gsystem):
                    time = int(line.split()[2])
                    day = datetime.timedelta(seconds=time).days
                    if day_flag == day:
                        hour = datetime.timedelta(seconds=time).seconds / 3600.
                        readorbit = True
                    else:
                        readorbit = False
                if line.startswith(prn) and readorbit:
                    line_s = line.split()
                    orbitc['hour'].append(hour)
                    orbitc['do_r'].append(float(line_s[2]))
                    orbitc['do_c'].append(float(line_s[3]))
                    orbitc['do_a'].append(float(line_s[4]))
                    orbitc['clock'].append(float(line_s[5]))
        cols = ['hour', 'do_r', 'do_c', 'do_a', 'clock']
        orbitc = pd.DataFrame(orbitc, columns=cols)
        return orbitc


def readSatNum(filepath, date, gsystem):
    """Read satellite number of correct file.

    Args:
        filepath:coorect filepath.
        date:file date.
        gsystem:GNSS system.

    Return:
        sat_num:satellite number, type:OrderedDict.
    """
    sat_num = OrderedDict()
    day_flag = (date.timetuple().tm_wday + 1) % 7
    with open(filepath) as f:
        for line in f:
            if line.startswith(gsystem):
                satnum = int(line.split()[1])
                sattime = int(line.split()[2])
                # convert week seconds to hour
                day = datetime.timedelta(seconds=sattime).days
                if day == day_flag:
                    hour = datetime.timedelta(seconds=sattime).seconds / 3600.0
                    sat_num[hour] = satnum
    return sat_num
