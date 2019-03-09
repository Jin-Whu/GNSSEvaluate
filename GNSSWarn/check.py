#!/usr/bin/env python
# coding:utf-8

import os
import datetime
import glob
from .notificate.notificate import Notify
from collections import namedtuple
import re
import sqlite3
import platform
if platform.system() == 'Linux':
    import matplotlib
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
import numpy as np

Config = namedtuple(
    'Config',
    ('path', 'system', 'type', 'endout', 'midout', 'evaluation', 'respath'))
BadStation = namedtuple('BadStation', ('stations', 'system', 'type'))


def plot(badstations, date, endouts, respath):
    """Plot badstations.

    Args:
        badstations:station whose une has exceeded threshold.
        date:date.
        endouts:endoutput path.
        respath:result file path.

    Return:
        figpaths:figure paths.
    """

    figpaths = list()
    rfname = re.compile('(\w{4})%s\.coor' %
                        '{:0>3d}'.format(date.timetuple().tm_yday))
    for stations in badstations:
        # threshold
        if stations.type == 'DFPPP':
            yrange = np.arange(-1, 1.5, 0.5)
        elif stations.type == 'SFPPP':
            yrange = np.arange(-2, 2.5, 1)
        # endout
        if stations.system == 'BDS':
            if stations.type == 'DFPPP':
                endout = endouts[0]
            elif stations.type == 'SFPPP':
                endout = endouts[2]
        elif stations.system == 'GPS':
            if stations.type == 'DFPPP':
                endout = endouts[1]
            elif stations.type == 'SFPPP':
                endout = endouts[3]
        # find files
        sitefiles = list()
        for ifile in os.listdir(endout):
            if ifile[:4] in stations.stations and rfname.match(ifile):
                sitefiles.append(os.path.join(endout, ifile))

        # plot
        plt.style.use('ggplot')
        f, axes = plt.subplots(3, sharex=True, sharey=True)
        colors = iter(cm.rainbow(np.linspace(0, 1, 5)))
        for ifile in sitefiles:
            sitename = rfname.findall(ifile)[0]
            data = pd.read_table(
                ifile, delim_whitespace=True).apply(
                    pd.to_numeric, errors='coerce')
            color = next(colors)
            x_axis = (data.ws % 86400) / 3600.0
            axes[0].scatter(x_axis, data.U, s=1, color=color)
            axes[1].scatter(x_axis, data.N, s=1, color=color, label=sitename)
            axes[2].scatter(x_axis, data.E, s=1, color=color)
        ax = axes[1]
        ax.legend(
            bbox_to_anchor=(1.01, 1),
            loc=2,
            borderaxespad=0.,
            scatterpoints=1,
            markerscale=3,
            prop={'size': 'medium',
                  'weight': 'bold'},
            frameon=False)
        # set xaixs and yaixs
        ax.set_xlim([0, 24])
        ax.set_ylim([yrange[0], yrange[-1]])
        axes[0].set_ylabel('U[m]', weight='bold')
        axes[1].set_ylabel('N[m]', weight='bold')
        axes[2].set_ylabel('E[m]', weight='bold')
        axes[2].set_xlabel('Time[h]', weight='bold')
        axes[2].set_xticks(range(0, 30, 6))
        axes[2].set_xticklabels(range(0, 30, 6), weight='bold')

        # set tiltel
        axes[0].set_title('%s-%s At %s' %
                          (stations.system, stations.type, str(date)))

        # save fig
        if not os.path.exists(respath):
            os.makedirs(respath)
        figpath = os.path.join(respath, '%s-%s-%s.png' %
                               (stations.system, stations.type, str(date)))
        f.savefig(figpath, bbox_inches='tight')
        figpaths.append(figpath)
        plt.clf()
        plt.close()
    return figpaths


def coordinate(name):
    """Return site coordinate-(B, L)"""
    station = os.path.join(
        os.path.abspath(__file__ + '/../../'), 'station.sqlite')
    conn = sqlite3.connect(station)
    cur = conn.cursor()
    cur.execute('SELECT B, L FROM Station WHERE name=?', (name.upper(), ))
    row = cur.fetchone()
    if not row:
        return None, None
    cur.close()
    conn.close()
    return row[0], row[1]


def readconfig():
    """Read configure file.

    If read failed, return None.

    Return:config, type:Config.
    """
    configpath = os.path.join(os.path.dirname(__file__), 'configure.ini')
    if not os.path.isfile(configpath):
        print('Not find %s' % configpath)
        return None
    paths = list()
    types = list()
    systems = list()
    endouts = list()
    midout = ''
    evaluation = ''
    respath = ''
    with open(configpath) as f:
        for line in f:
            if line.startswith('path'):
                paths.append(line.split('=')[1].strip())
            if line.startswith('system'):
                systems.append(line.split('=')[1].strip())
            if line.startswith('type'):
                types.append(line.split('=')[1].strip())
            if line.startswith('endout'):
                endouts.append(line.split('=')[1].strip())
            if line.startswith('respath'):
                respath = line.split('=')[1].strip()
            if line.startswith('midout'):
                midout = line.split('=')[1].strip()
            if line.startswith('evaluation'):
                evaluation = line.split('=')[1].strip()

    config = Config(paths, systems, types, endouts, midout, evaluation, respath)
    # check path, system and type
    for ipath in paths:
        if not os.path.exists(ipath):
            print('Not find path:%s' % ipath)
            return None
    for isystem in systems:
        if isystem not in ['BDS', 'GPS', 'GBS', 'MIX']:
            print('Not find %s' % isystem)
            return None
    for itype in types:
        if itype not in ['DFPPP', 'SFPPP', 'SFSPP']:
            print('type is invalid')
            return None
    if not os.path.exists(respath):
        print('Not find respath:%s\nTry to make it...' % respath)
        try:
            os.makedirs(respath)
            print('Make successfully!')
        except:
            print('Make %s failed!')
            return None

    for ipath in endouts:
        if not os.path.exists(ipath):
            print('Not find endout:%s' % ipath)
            return None
    if not os.path.exists(midout):
        print('Not find midout:%s' % midout)
        return None
    if not os.path.exists(evaluation):
        print('Not find evaluation path:%s' % evaluation)
        return None
    return config


def checksatnums(filepath, date, evaluation, respath):
    """read corr file and checksatnums.

    Args:
        filepath:filepath store correct file.
        date:date.
        evaluation:evaluation result path.
        respath:report path.
    """
    date_s = ''.join(str(date).split('-'))
    # retrieve coorect files
    bds_corr = ''.join(['CorrBDS', date_s, '.txt'])
    gps_corr = ''.join(['CorrGPS', date_s, '.txt'])
    bds_files = glob.glob(os.path.join(filepath, bds_corr))
    gps_files = glob.glob(os.path.join(filepath, gps_corr))
    message = ''
    if not bds_files:
        message += 'No BDS correct file\n'
    if not gps_files:
        message += 'No GPS correct file\n'
    # start read
    sat_num = dict()
    for path in bds_files:
        sat_num['BDS'] = readSatNum(path, date, 'BDS')
    for path in gps_files:
        sat_num['GPS'] = readSatNum(path, date, 'GPS')
    # check satnums
    missbds = 0
    badbds = 0
    missgps = 0
    badgps = 0
    if 'BDS' in sat_num:
        missbds = 86400 - len(sat_num['BDS'])
        badbds = len([num for num in sat_num['BDS'] if num < 4])
    if 'GPS' in sat_num:
        missgps = 86400 - len(sat_num['GPS'])
        badgps = len([num for num in sat_num['GPS'] if num < 4])
    if missbds > 2500:
        message += 'BDS Sat.Num = 0: %s\n' % missbds
    if missgps > 2500:
        message += 'GPS Sat.Num = 0: %s\n' % missgps
    if badbds > 100:
        message += 'BDS Sat.Num < 4: %s\n' % badbds
    if badgps > 100:
        message += 'GPS Sat.Num < 4: %s\n' % badgps
    if not message:
        return message, None
    message = 'Report of satellite nums:\n\n%s' % message
    if not os.path.exists(respath):
        os.makedirs(respath)
    reportpath = os.path.join(respath, 'report-%s.txt' % str(date))
    with open(reportpath, 'a') as f:
        f.write(message)
    satpath = os.path.join(evaluation, 'Correct', str(date))
    satfigs = glob.glob(os.path.join(satpath, '*.png'))
    print(message)
    return message, satfigs


def readSatNum(filepath, date, gsystem):
    """Read satellite number of correct file.

    Args:
        filepath:coorect filepath.
        date:file date.
        gsystem:GNSS system.

    Return:
        sat_num:satellite number, type:OrderedDict.
    """
    sat_num = list()
    day_flag = (date.timetuple().tm_wday + 1) % 7
    with open(filepath) as f:
        for line in f:
            if line.startswith(gsystem):
                satnum = int(line.split()[1])
                sattime = int(line.split()[2])
                day = datetime.timedelta(seconds=sattime).days
                if day == day_flag:
                    sat_num.append(satnum)
    return sat_num


def readreport(filepath, gsystem, etype, date, respath):
    """read report file.

    Args:
        filepath:report file path.
        gsystem:gnss system, including BDS, GPS, GBS, MIX.
        etype:evaluation type, including DFPPP, SFPPP, SFSPP.
        date:date, type:date.
        respath:result file path.

    Return:
        stations:bad stations.
        reportpath:report path.
    """
    if etype == 'DFPPP':
        threshold = 1
    elif etype == 'SFPPP':
        threshold = 2
    elif etype == 'SFSPP':
        threshold = 10

    nullstations = list()
    badstations = list()
    stations = None
    count = 0
    with open(filepath) as f:
        for line in f:
            if line.startswith('name'):
                continue
            count += 1
            pieces = line.split()
            name, data = pieces[0], list(map(float, pieces[5:8]))
            # check if null station
            if not all(data):
                nullstations.append(name)
            for value in data:
                if value > threshold:
                    badstations.append([name, data])
                    break
    message = ''
    report = ''
    if len(nullstations) > 5:
        message += '%s-%s, %s/%s stations had empty data:%s\n\n' % (
            gsystem, etype, len(nullstations), count, ' '.join(nullstations))
        report = message
    if len(badstations) / float(count) > 0.5:

        message += '%s-%s, %s/%s stations 95%% UNE exceeded %sm' % (
            gsystem, etype, len(badstations), count, threshold)
        report = message + ':\n\n'
        report += '{}{:>10}{:>10}{:>10}{:>10}{:>10}\n'.format('site', 'B', 'L',
                                                              'U', 'N', 'E')

        badstations.sort(lambda x, y: y[1][0] > x[1][0])

        def f(t):
            b, l = coordinate(t[0])
            return '%s:%10.2f%10.2f%10.2f%10.2f%10.2f' % (t[0], b, l, t[1][0],
                                                          t[1][1], t[1][2])

        report += '\n'.join(list(map(f, badstations)))
        report += '\n\n'
        if gsystem in ['BDS', 'GPS'] and etype in ['DFPPP', 'SFPPP']:
            stations = BadStation([tmp[0] for tmp in badstations[:5]], gsystem,
                                  etype)

    reportpath = None
    if report:
        if not os.path.exists(respath):
            os.makedirs(respath)
        reportpath = os.path.join(respath, 'report-%s.txt' % str(date))
        if not os.path.exists(reportpath):
            with open(reportpath, 'w') as f:
                f.write('Report of position quality:\n\n')
        with open(reportpath, 'a') as f:
            f.write(report)

    return stations, reportpath, message


def check():
    """check report."""
    # read configure file
    config = readconfig()
    if not config:
        print('Read configure.ini failed, program will not check!')
        return

    # start check
    date = datetime.datetime.now().date() - datetime.timedelta(days=1)
    respath = os.path.join(config.respath, str(date))
    # check position quality
    subject = 'Position report of %s' % str(date)
    message = ''
    badstations = list()
    files = list()
    for ipath, isystem, itype in zip(config.path, config.system, config.type):
        filepath = glob.glob(os.path.join(ipath, str(date), '*.csv'))
        if not filepath:
            continue
        path = filepath[0]
        stations, reportpath, unemsg = readreport(path, isystem, itype, date,
                                                  respath)
        if unemsg:
            message += unemsg + '\n'
        if reportpath and reportpath not in files:
            files.append(reportpath)
        if stations:
            badstations.append(stations)
    figpaths = plot(badstations, date, config.endout, respath)
    if figpaths:
        files.extend(figpaths)
        message = 'Report of position quality:\n\n' + message + '\n\n'
    # check satellite nums
    satmsg, satfigs = checksatnums(config.midout, date, config.evaluation,
                                   respath)
    if satmsg:
        message += satmsg
    if satfigs:
        files.extend(satfigs)

    # notificate
    if message:
        notify = Notify()
        notify.notificate(subject, message, files)
