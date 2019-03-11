# coding:utf-8
"""Dataprocess include manual and auto run."""

import multiprocessing
import os
import datetime
import time
import pandas as pd
import numpy as np
from collections import defaultdict
import preprocess
import readdata
import plotdata
import sciutilities
from GNSSWarn import check


class Dataprocess(object):
    """Dataprocess.

    Data process include manual and auto run.

    Attributes:
        endoutput:coor file path, type:list, element type:str.
        midoutput:corr file path, type:list, element type:str.
        respath:result file path, type:str.
        gsystem:GNSS system, type:list, element type:str.
        ctype:calculate type, type:list, elemnt type:str.
        duration:duration include start time and end time, type:list,
            element type:datetime.
    """

    def __init__(self):
        """Initialize Dataprocess."""
        self.endoutput = list()
        self.midoutput = list()
        self.respath = None
        self.gsystem = list()
        self.ctype = list()
        self.duration = list()
        self.prn = list()

    def readarg(self, args):
        """Read command arguments."""
        if len(args) == 1:
            self.autorun()
        elif len(args) == 2:
            self.manual(args)
        else:
            print('Arguments wrong! You can use --help to see commands!')

    def manual(self, args):
        """Manual execute."""
        # read manual configure file
        pre_process = preprocess.Preprocess()
        pre_process.readconfig('manual.ini')
        self.endoutput = pre_process.endoutput
        self.midoutput = pre_process.midoutput
        self.respath = pre_process.respath
        self.gsystem = pre_process.gsystem
        self.ctype = pre_process.ctype
        self.duration = pre_process.duration
        self.prn = pre_process.prn
        # choose moduel
        if args[1].upper() == '-A':
            # start process
            process = list()
            process.append(multiprocessing.Process(target=self.enu))
            process.append(multiprocessing.Process(target=self.uh))
            process.append(multiprocessing.Process(target=self.satnum))
            process.append(multiprocessing.Process(target=self.satiode))
            process.append(multiprocessing.Process(target=self.satorbitc))
            [p.start() for p in process]
            [p.join() for p in process]
            print('All Done!')
        elif args[1].upper() == '-R':
            self.report()
            print('Done!')
        elif args[1].upper() == '--ENU':
            self.enu()
            print('Done!')
        elif args[1].upper() == '--HV':
            self.uh()
            print('Done!')
        elif args[1].upper() == '--HVM':
            self.uhmean()
            print('Done!')
        elif args[1].upper() == '--SAT':
            self.satnum()
            print('Done!')
        elif args[1].upper() == '--IODE':
            self.satiode()
            print('Done!')
        elif args[1].upper() == '--ORBITC':
            self.satorbitc()
            print('Done!')
        elif args[1].upper() == '--HELP' or args[1]:
            print('Arg:')
            print('\t-a -A:execute all module.')
            print('\t-r -R:zdpos report')
            print('\t--ENU:plot ENU')
            print('\t--HV:plot horizontal and vertical errors')
            print('\t--HVM:plor mean of horizontal and vertical errors')
            print('\t--SAT:plot satellite number')
            print('\t--IODE:plot satellite iode')
            print('\t--ORBITC:plot orbit and clock errors')

    def autorun(self):
        """Auto run."""
        # read autorun configure file
        pre_process = preprocess.Preprocess()
        pre_process.readconfig('autorun.ini')
        self.endoutput = pre_process.endoutput
        self.midoutput = pre_process.midoutput
        self.respath = pre_process.respath
        self.gsystem = pre_process.gsystem
        self.ctype = pre_process.ctype
        yesterday = datetime.datetime.now().date() + datetime.timedelta(-1)
        self.duration = [yesterday, yesterday]
        # start process
        process = list()
        process.append(multiprocessing.Process(target=self.enu))
        process.append(multiprocessing.Process(target=self.uh))
        process.append(multiprocessing.Process(target=self.satnum))
        [p.start() for p in process]
        [p.join() for p in process]
        # check evaluation quality
        check.check()
        now = datetime.datetime.now().replace(second=0, microsecond=0)
        print('%s: The process of %s Done!' % (str(now), str(yesterday)))

    def report(self):
        """Report zdpos errors."""
        read_coor = readdata.Read()
        for date in self.getdaterange():
            for filepath, gsystem, ctype in zip(self.endoutput, self.gsystem,
                                                self.ctype):
                report = read_coor.readcoor(filepath, date)

                # save report
                report_fname = '-'.join(
                    [ctype, gsystem, str(date), 'report.csv'])
                report_path = os.path.join(self.respath, str(date), '-'.join([ctype, gsystem]))
                if not os.path.exists(report_path):
                    os.makedirs(report_path)
                report.to_csv(
                    os.path.join(report_path, report_fname),
                    sep='\t',
                    na_rep=' ',
                    index=False,
                    float_format='%.2f')

    def enu(self):
        """Plot ENU."""
        enu_plot = plotdata.Plot()
        for date in self.getdaterange():
            for filepath, gsystem, ctype in zip(self.endoutput, self.gsystem,
                                                self.ctype):
                enu_plot.plotENU(filepath, date, gsystem, ctype, self.respath)

    def uh(self):
        """Plot UH Errors."""
        read_coor = readdata.Read()
        uh_plot = plotdata.Plot()
        for date in self.getdaterange():
            for filepath, gsystem, ctype in zip(self.endoutput, self.gsystem,
                                                self.ctype):
                report = read_coor.readcoor(filepath, date)
                if report is not None:
                    uh_plot.plotUH(report, date, gsystem, ctype, self.respath)

    def uhmean(self):
        """Report mean."""
        read_coor = readdata.Read()
        station_U = defaultdict(list)
        station_H = defaultdict(list)
        for filepath, gsystem, ctype in zip(self.endoutput, self.gsystem,
                                            self.ctype):
            for date in self.getdaterange():
                report = read_coor.readcoor(filepath, date)
                if report is None:
                    continue
                for index in report.index.tolist():
                    name = report.at[index, 'name']
                    station_U[name].append(report.at[index, 'U_95'])
                    station_H[name].append(report.at[index, 'H_95'])

            # remove outlier and mean
            for name in station_U:
                station_u = np.array(station_U[name])
                station_h = np.array(station_H[name])
                station_U[name] = np.mean(station_u[~sciutilities.is_outlier(
                    station_u)])
                station_H[name] = np.mean(station_h[~sciutilities.is_outlier(
                    station_h)])
            # convert station_U, station_H to dataframe
            report_m = pd.DataFrame(
                index=range(len(station_U)), columns=['name', 'U_95', 'H_95'])
            report_m.name = station_U.keys()
            report_m.U_95 = station_U.values()
            report_m.H_95 = station_H.values()
            # start plot
            uh_plot = plotdata.Plot()
            date = '--'.join([str(self.duration[0]), str(self.duration[1])])
            uh_plot.plotUH(report, date, gsystem, ctype, self.respath)

    def satnum(self):
        """Plot satellite number."""
        read_satnum = readdata.Read()
        plot_satnum = plotdata.Plot()
        for date in self.getdaterange():
            for filepath in self.midoutput:
                sat_num = read_satnum.readsatnum(filepath, date)
                if sat_num is not None:
                    plot_satnum.plotsatnum(sat_num, date, self.respath)

    def satiode(self):
        """Plot satellite iode."""
        read_iode = readdata.Read()
        plot_iode = plotdata.Plot()
        for date in self.getdaterange():
            for filepath in self.midoutput:
                for prn in self.prn:
                    sat_iode = read_iode.readsatiode(filepath, date, prn)
                    if sat_iode is not None:
                        plot_iode.plotsatiode(sat_iode, prn, date, self.respath)

    def satorbitc(self):
        """Plot satellite orbit and clock errors."""
        read_orbitc = readdata.Read()
        plot_orbitc = plotdata.Plot()
        for date in self.getdaterange():
            for filepath in self.midoutput:
                for prn in self.prn:
                    sat_orbitc = read_orbitc.readorbitc(filepath, date, prn)
                    if sat_orbitc is not None:
                        plot_orbitc.plotorbitc(sat_orbitc, prn, date, self.respath)

    def getdaterange(self):
        """Get date range."""
        for i in range((self.duration[1] - self.duration[0]).days + 1):
            yield self.duration[0] + datetime.timedelta(i)
