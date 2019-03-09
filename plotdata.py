# coding:utf-8
"""Plot include ENU plot, HVError plot, Satellite plot, Orbit plot."""

import os
import sqlite3
import glob
import re
import pandas as pd
import numpy as np
import platform
if platform.system() == 'Linux':
    import matplotlib
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.axes_grid1 import ImageGrid
import itertools
from collections import defaultdict


class Plot(object):
    """Plot."""

    def plotENU(self, coorpath, date, gsystem, ctype, respath):
        """plotenu and report.

        Arg:
            coorpath:coor file store path.
            date:coor file date, type:datetime.
            gsystem:GNSS system.
            ctype:calculate type.
            respath:result path.
        """
        doy = date.timetuple().tm_yday
        filelist = glob.glob(
            os.path.join(coorpath, ''.join(
                ['*', '{:0>3d}.{:0>2d}'.format(doy, date.year % 100), 'coor'])))
        if not filelist:
            print("Can't find %s's coor file in %s" % (str(date), coorpath))
            return 0
        filesnum = len(filelist)
        # start plot
        fig, axes = plt.subplots(4, sharex=True)
        fig_number = 1
        colors = itertools.cycle(cm.rainbow(np.linspace(0, 1, 7)))
        refname = re.compile(r'(\w+)\d{3}\.\d{2}coor')
        # set yaxis range
        if ctype == 'DFPPP':
            yrange = np.arange(-1, 1.5, 0.5)
        elif ctype == 'SFPPP':
            yrange = np.arange(-2, 2.5, 1)
        elif ctype == 'SFSPP':
            yrange = np.arange(-10, 10.5, 5)

        report = defaultdict(list)
        counter = 0  # if counte is multiple of 7 create a new figure
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
                counter += 1
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
                counter += 1
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

            color = next(colors)
            label = '%s U:%.2fm N:%.2fm E:%.2fm' % (station, u_rms, n_rms,
                                                    e_rms)
            x_axis = (data.ws % 86400) / 3600.0
            axes[0].scatter(x_axis, data.U, s=1, color=color)
            axes[1].scatter(x_axis, data.N, s=1, color=color, label=label)
            axes[2].scatter(x_axis, data.E, s=1, color=color)
            axes[3].scatter(x_axis, data.trop, s=1, color=color)

            counter += 1
            if counter % 7 == 0 or counter == filesnum:
                # legend
                axes[1].legend(
                    bbox_to_anchor=(1.01, 1),
                    loc=2,
                    borderaxespad=0.,
                    scatterpoints=1,
                    markerscale=3,
                    prop={'size': 'medium',
                          'weight': 'bold'},
                    frameon=False)
                # set xaixs and yaixs
                for ax in axes:
                    ax.set_xlim([0, 24.5])
                    ax.set_ylim([yrange[0], yrange[1]])
                    ax.set_xticks(np.arange(0, 25))
                    ax.set_yticks(yrange)
                    ax.xaxis.tick_bottom()
                    ax.yaxis.tick_left()
                    ax.set_yticklabels(yrange, weight='bold')
                # change trop subplot ylim and yticks
                axes[3].set_ylim([1, 3])
                axes[3].set_yticks(np.arange(1, 3.5, 0.5))
                axes[3].set_xticklabels(range(0, 25), weight='bold')
                axes[3].set_yticklabels(np.arange(1, 3.5, 0.5), weight='bold')
                # set xaixs and yaixs label
                axes[3].set_xlabel('TIME[h]', weight='bold')
                axes[3].set_ylabel('Trop[m]', weight='bold')
                axes[0].set_ylabel('Up[m]', weight='bold')
                axes[1].set_ylabel('North[m]', weight='bold')
                axes[2].set_ylabel('East[m]', weight='bold')

                # save figure
                fig_name = '%s-%s-%s-ENU%d' % (ctype, gsystem, str(date),
                                               fig_number)
                fig_path = os.path.join(respath, '-'.join([ctype, gsystem]),
                                        str(date))
                if not os.path.exists(fig_path):
                    os.makedirs(fig_path)
                plt.savefig(
                    os.path.join(fig_path, fig_name), bbox_inches='tight')
                plt.clf()
                plt.close()
                # new figure
                fig, axes = plt.subplots(4, sharex=True)
                fig_number += 1
        plt.clf()
        plt.close()

        # save report
        cols = [
            'name', 'U_rms', 'N_rms', 'E_rms', 'H_rms', 'U_95', 'N_95', 'E_95',
            'H_95', 'effective_rate'
        ]
        report = pd.DataFrame(report, columns=cols).sort_values('name')
        report_name = '-'.join([ctype, gsystem, str(date), 'report.csv'])
        report.to_csv(
            os.path.join(fig_path, report_name),
            sep='\t',
            na_rep=' ',
            index=False,
            float_format='%.2f')

    def plotUH(self, report, date, gsystem, ctype, filepath):
        """Plot horenzital and vertical errors.

        Arg:
            report:report of coor file, type:pandas.dataframe.
            date:coor file date.
            gsystem:GNSS system.
            ctype:calculate type.
            filepath:result path.
        """
        # connect to station database, returieve station b, l
        connect = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), 'station.sqlite'))
        cur = connect.cursor()

        latitude = list()
        longtitude = list()
        for name in report.name:
            cur.execute('SELECT B, L FROM Station WHERE name=?',
                        (name.lower(), ))
            try:
                cur_fetch = cur.fetchone()
                latitude.append(cur_fetch[0])
                longtitude.append(cur_fetch[1])
            except:
                continue

        cur.close()
        connect.close()
        if not latitude:
            return
        # start plot
        # set colorbar range
        if ctype == 'DFPPP':
            colorbar_vmax = 1
        elif ctype == 'SFPPP':
            colorbar_vmax = 3
        elif ctype == 'SFSPP':
            colorbar_vmax = 10

        fig = plt.figure(figsize=(20, 10))
        grid = ImageGrid(
            fig,
            111,
            nrows_ncols=(1, 2),
            axes_pad=0.2,
            share_all=True,
            cbar_mode='single',
            cbar_size="5%",
            cbar_pad=0.1)
        for ax, i in zip(grid, [0, 1]):
            if i == 0:
                title = 'Horizontal Errors'
                color = report.H_95.values
            else:
                title = 'Vertical Errors'
                color = report.U_95.values
            ax.set_title(title, size=22, weight='bold')
            m = Basemap(
                projection='cyl',
                llcrnrlat=9,
                urcrnrlat=61,
                llcrnrlon=70,
                urcrnrlon=140,
                ax=ax)
            m.drawcountries(color='#778899')
            m.drawlsmask(
                land_color='#F0E68C', ocean_color='#87CEEB', lakes=False)
            if i == 0:
                m.drawparallels(
                    np.arange(10, 70, 10),
                    labels=[1, 0, 0, 0],
                    linewidth=0.01,
                    fontsize=18,
                    weight='bold')
            m.drawmeridians(
                np.arange(75, 140, 10),
                labels=[0, 0, 0, 1],
                linewidth=0.01,
                fontsize=18,
                weight='bold')
            mscatter = m.scatter(
                longtitude,
                latitude,
                latlon=True,
                c=color,
                s=200,
                marker='o',
                cmap=cm.get_cmap('jet'),
                vmin=0,
                vmax=colorbar_vmax,
                alpha=0.95)
        cbar = ax.cax.colorbar(mscatter)
        cbar.ax.set_title('m', size=18, weight='bold')
        plt.setp(cbar.ax.yaxis.get_ticklabels(), size=18, weight='bold')
        title = {'BDS': 'BDS', 'GPS': 'GPS', 'GBS': 'BDS/GPS', 'MIX': 'GPS+BDS+GLO+GAL'}
        fig.suptitle(
            '%s %s %s' % (title[gsystem], ctype, str(date)),
            y=0.84,
            size=24,
            weight='bold')
        fig_name = '-'.join([ctype, gsystem, str(date), 'HV'])
        fig_path = os.path.join(filepath, '-'.join([ctype, gsystem]),
                                str(date))
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)
        plt.savefig(
            os.path.join(fig_path, ''.join([fig_name, '.png'])),
            bbox_inches='tight')

        # add station name
        for ax in grid:
            for name, lon, lat in zip(report.name.tolist(), longtitude,
                                      latitude):
                x, y = m(lon, lat)
                ax.text(x, y, name, size=12, weight='bold')

        plt.savefig(
            os.path.join(fig_path, ''.join([fig_name, '_name.png'])),
            bbox_inches='tight')
        plt.clf()
        plt.close()

    def plotsatnum(self, satnum, date, filepath):
        """Plot statellite number.

        Args:
            satnum:satellite num, type:dict.
            date:satnum date, type:datetime.
            filepaht:result filepath.
        """
        for gsystem in satnum:
            hours = satnum[gsystem].keys()
            nums = satnum[gsystem].values()
            missnum = 86400 - len(nums)
            badnum = len([num for num in nums if num < 4])
            plt.figure(figsize=(20, 10))
            label = 'Sat.Num = 0: %s\nSat.Num < 4: %s' % (missnum, badnum)
            plt.scatter(hours, nums, s=1, color='#00FA9A', label=label)
            # set xaxis and yaixs
            ax = plt.gca()
            ax.set_xlim([0, 24.5])
            ax.set_ylim([4, 15]) if gsystem == 'BDS' else ax.set_ylim([7, 33])
            ax.set_xticks(range(0, 25))
            ax.set_xticklabels(range(0, 25), size=18, weight='bold')
            plt.setp(ax.yaxis.get_ticklabels(), size=18, weight='bold')
            ax.xaxis.tick_bottom()
            ax.yaxis.tick_left()
            ax.set_xlabel('Time[h]', size=20, weight='bold')
            ax.set_ylabel('Number', size=20, weight='bold')
            ax.set_title(
                ' '.join([gsystem, 'Satellite Number', 'At', str(date)]),
                size=25,
                weight='bold')
            plt.legend(markerscale=0, prop={'size': 12, 'weight': 'bold'})
            fig_name = '-'.join([gsystem, str(date), 'satnum.png'])
            fig_path = os.path.join(filepath, 'Correct', str(date))
            if not os.path.exists(fig_path):
                os.makedirs(fig_path)
            plt.savefig(os.path.join(fig_path, fig_name), bbox_inches='tight')
            plt.clf()
            plt.close()

    def plotsatiode(self, satiode, prn, date, filepath):
        """Plot satellite iode.

        Args:
            satiode:satellite iode, type:OrderedDict.
            prn:satellite prn.
            date:satellite date, type:datetime.
            filepath:result file path.
        """
        hours = satiode.keys()
        iodes = satiode.values()
        plt.figure(figsize=(20, 10))
        plt.scatter(hours, iodes, s=1, color='#B22222')
        # set xaxis and yaixs
        ax = plt.gca()
        ax.set_xlim([0, 24.5])
        ax.set_ylim([0, max(iodes) + 10])
        ax.set_xticks(range(0, 25))
        ax.set_xticklabels(range(0, 25), size=18, weight='bold')
        plt.setp(ax.yaxis.get_ticklabels(), size=18, weight='bold')
        ax.xaxis.tick_bottom()
        ax.yaxis.tick_left()
        ax.set_xlabel('Time[h]', size=20, weight='bold')
        ax.set_ylabel('IODE', size=20, weight='bold')
        ax.set_title(
            ' '.join([prn, 'Satellite IODE', 'At', str(date)]),
            size=25,
            weight='bold')
        fig_name = '-'.join([prn, str(date), 'satiode.png'])
        fig_path = os.path.join(filepath, 'Correct', str(date))
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)
        plt.savefig(os.path.join(fig_path, fig_name), bbox_inches='tight')
        plt.clf()
        plt.close()

    def plotorbitc(self, orbitc, prn, date, filepath):
        """Plot orbit errors and clock errors.

        Args:
            orbitc:orbit errors and clock errors, type:pd.DataFrame.
            prn:satellite prn.
            date:date, type:datetime.
            filepath:result file path.
        """
        hours = orbitc.hour.tolist()
        do_r = orbitc.do_r.tolist()
        do_c = orbitc.do_c.tolist()
        do_a = orbitc.do_a.tolist()
        clock = orbitc.clock.tolist()
        # start plot
        f, axes = plt.subplots(4, sharex=True, figsize=(20, 10))
        axes[0].scatter(hours, do_a, s=1, color='#1E90FF')
        axes[1].scatter(hours, do_c, s=1, color='#00FA9A')
        axes[2].scatter(hours, do_r, s=1, color='#CD5C5C')
        axes[3].scatter(hours, clock, s=1, color='#F4A460')
        # set xaxis and yaxis
        for ax in axes:
            ax.xaxis.tick_bottom()
            ax.yaxis.tick_left()
            ax.set_xlim([0, 24.5])
            plt.setp(ax.yaxis.get_ticklabels(), size=18, weight='bold')
        axes[0].set_ylabel('DO-A[m]', size=20, weight='bold')
        axes[1].set_ylabel('DO-C[m]', size=20, weight='bold')
        axes[2].set_ylabel('DO-R[m]', size=20, weight='bold')
        axes[3].set_xticks(range(0, 25))
        axes[3].set_xticklabels(range(0, 25), size=18, weight='bold')
        axes[3].set_xlabel('TIME[h]', size=20, weight='bold')
        axes[3].set_ylabel('Clock[m]', size=20, weight='bold')
        # set title
        title = ' '.join([prn, 'Oribit And Clock', 'At', str(date)])
        f.suptitle(title, size=25, weight='bold')
        # save figure
        fig_name = '-'.join([prn, str(date), 'orbit-clock.png'])
        fig_path = os.path.join(filepath, 'Correct', str(date))
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)
        plt.savefig(os.path.join(fig_path, fig_name), bbox_inches='tight')
        plt.clf()
        plt.close()
