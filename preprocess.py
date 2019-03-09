# coding:utf-8
"""Preprocess include read configure file, read station list."""

import sys
import os
import re
import sqlite3
import datetime


class Preprocess(object):
    """Preprocess.

    Preprocess include read configure file, read station list.

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
        """Initialize Preprocess."""
        self.endoutput = list()
        self.midoutput = list()
        self.respath = None
        self.gsystem = list()
        self.ctype = list()
        self.duration = list()
        self.prn = list()

    def readconfig(self, fname):
        """Read configure file.

        Arg:
            fname: configure file name, manual.ini or auto.ini.
        """
        configure_path = os.path.join(os.path.dirname(__file__), fname)
        if not os.path.exists(configure_path):
            print('Not find configure file in %s' % configure_path)
            sys.exit()

        try:
            with open(configure_path) as f:
                for line in f:
                    if line.startswith('endoutput'):
                        self.endoutput.append(line.split('=')[1].strip())
                    if line.startswith('midoutput'):
                        self.midoutput.append(line.split('=')[1].strip())
                    if line.startswith('stationlist'):
                        station = (line.split('=')[1].strip())
                    if line.startswith('resultpath'):
                        self.respath = (line.split('=')[1].strip())
                    if line.startswith('system'):
                        self.gsystem.append(line.split('=')[1].strip().upper())
                    if line.startswith('type'):
                        self.ctype.append(line.split('=')[1].strip().upper())

                    if fname == 'manual.ini':
                        if line.startswith('starttime'):
                            self.duration.append(line.split('=')[1].strip())
                        if line.startswith('endtime'):
                            self.duration.append(line.split('=')[1].strip())
                        if line.startswith('prn'):
                            prn = line.split('=')[1].strip()
                            if prn:
                                self.prn.append(prn)

            # check filepath, system, type, duration
            self.__checkpath(self.endoutput)
            self.__checkpath(self.midoutput)
            self.__checksystem(self.gsystem)
            self.__checktype(self.ctype)
            if fname == 'manual.ini':
                self.__checkdatetime(self.duration)

            # read station list and store in database
            self.__readstation(station)

        except:
            print('Read configure file %s failed!' % configure_path)
            sys.exit()

    def __checkpath(self, pathls):
        """check file path."""
        for ipath in pathls:
            if not os.path.exists(ipath):
                print('Not find %s' % ipath)
                sys.exit()

    def __checksystem(self, systemls):
        """check system."""
        for isystem in systemls:
            if isystem not in ['BDS', 'GPS', 'GBS', 'MIX']:
                print('System %s is invalid!' % isystem)
                sys.exit()

    def __checktype(self, typels):
        """check type."""
        for itype in typels:
            if itype not in ['DFPPP', 'SFPPP', 'SFSPP']:
                print('Type %s is invalid!' % itype)
                sys.exit()

    def __checkdatetime(self, duration):
        """check datetime."""
        for itime in duration:
            if not re.match(r"^\d{4} \d{2} \d{2}$", itime):
                print('%s not match yyyy mm dd' % itime)
                sys.exit()
        try:
            starttime = datetime.date(*list(map(int, duration[0].split())))
            endtime = datetime.date(*list(map(int, duration[1].split())))
        except Exception as e:
            print('Datetime is invalid.')
            print(e)
            sys.exit()

        if endtime < starttime:
            print('endtime shold be less than or equal to starttime!')
            sys.exit()

        self.duration[0] = starttime
        self.duration[1] = endtime

    def __readstation(self, filepath):
        """Read station list and store in database.

        Arg:
            filepath:station list filepath.
        """
        connection = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), 'station.sqlite'))
        cur = connection.cursor()
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS Station(name TEXT NOT NULL UNIQUE
            , B DOUBLE NOT NULL, L DOUBLE NOT NULL, H DOUBLE NOT NULL)''')

        if not os.path.exists(filepath):
            print('Not find station list in %s' % filepath)
            sys.exit()

        try:
            with open(filepath) as f:
                for line in f:
                    chrgroup = line.split()
                    name = chrgroup[0]
                    b = chrgroup[1]
                    l = chrgroup[2]
                    h = chrgroup[3]
                    cur.execute(
                        'INSERT OR IGNORE INTO Station VALUES(?, ?, ?, ?)',
                        (name, b, l, h))
            connection.commit()
            cur.close()
            connection.close()
        except:
            print('Read station list %s failed!' % filepath)
            sys.exit()
