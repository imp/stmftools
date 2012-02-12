#!/bin/python
#
# Copyright 2012 Grigale Ltd. All rigths reserved.
# Use is subject to license terms.
#
import optparse
import subprocess as sp
import pprint as pp
import time

KSTAT = '/bin/kstat'
PORT = 'stmf_tgt_'
PORTIO = 'stmf_tgt_io'
LU = 'stmf_lu_'
LUIO = 'stmf_lu_io'

PORT_HEADER_FMT = '{0: >59}'
PORT_HEADER_VERBOSE_FMT = '{0: >59}  {1: <13}  {2: <}'

LU_HEADER_FMT = '{0: >32}'
LU_HEADER_VERBOSE_FMT = '{0: >32}  {1: <}'

EMPTY_IO_STAT = {'class': 'io',
                 'crtime': '0.0',
                 'nread': '0',
                 'nwritten': '0',
                 'rcnt': '0',
                 'reads': '0',
                 'rlastupdate': '0',
                 'rlentime': '0',
                 'rtime': '0',
                 'snaptime': '0.0',
                 'wcnt': '0',
                 'wlastupdate': '0',
                 'wlentime': '0',
                 'writes': '0',
                 'wtime': '0'}

def stmfkstat():
    cmd = [KSTAT, '-m', 'stmf', '-p']
    ks = sp.Popen(cmd, stdout=sp.PIPE)
    out, err = ks.communicate()
    if ks.returncode:
        raise IOError
    return out


def iokstat(kstat):
    stat = dict()
    for item in kstat:
        if item == 'class':
            continue
        elif item in ['crtime', 'snaptime']:
            stat[item] = kstat[item] # FIXME
        else:
            stat[item] = int(kstat[item])
    return stat

def kstatrate(stat1, stat2):
    '''Calculates standard IO rates based on IO kstat stat1 and stat2
    '''
    s1 = iokstat(stat1)
    s2 = iokstat(stat2)

    rbytes = s2['nread'] - s1['nread']
    wbytes = s2['nwritten'] - s1['nwritten']
    reads = s2['reads'] - s1['reads']
    writes = s2['writes'] - s1['writes']

    return reads, writes, rbytes, wbytes

class STMFStats():
    def __init__(self):
        self.curr = dict(port=dict(), lu=dict())
        self.last = dict(port=dict(), lu=dict())
        self.luchanged = False
        self.portchanged = False
        self.update()

    def update(self):
        port = dict()
        lu = dict()
        for line in stmfkstat().splitlines():
            stat, value = line.split(None, 1)
            module, inst, name, stat = stat.split(':')
            #print name, stat, value
            if name.startswith(PORTIO):
                portidx = name.split('_')[3]
                if portidx not in port:
                    port[portidx] = dict(io=dict())
                else:
                    port[portidx]['io'][stat] = value
            elif name.startswith(PORT):
                portidx = name.split('_')[2]
                if portidx not in port:
                    port[portidx] = dict(io=dict())
                else:
                    port[portidx][stat] = value
            elif name.startswith(LUIO):
                luidx = name.split('_')[3]
                if luidx not in lu:
                    lu[luidx] = dict(io=dict())
                else:
                    lu[luidx]['io'][stat] = value
            elif name.startswith(LU):
                luidx = name.split('_')[2]
                if luidx not in lu:
                    lu[luidx] = dict(io=dict())
                else:
                    lu[luidx][stat] = value
        #pp.pprint(port)
        #pp.pprint(lu)
        self.last = self.curr.copy()
        self.curr['lu'] = lu
        self.curr['port'] = port
        if len(self.last['lu']) != len(self.curr['lu']):
            self.luchanged = True
        else:
            self.luchanged = False
        if len(self.last['port']) != len(self.curr['port']):
            self.portchanged = True
        else:
            self.portchanged = False

    def luinventory(self, header=True, verbose=False):
        fmt = LU_HEADER_VERBOSE_FMT if verbose else LU_HEADER_FMT
	if header:
            hdr = fmt.format('LU GUID', 'LU ALIAS')
            print '\n', hdr

        for lu in self.curr['lu']:
            line = fmt.format(
                self.curr['lu'][lu]['lun-guid'],
                self.curr['lu'][lu]['lun-alias'])
            print line

    def portinventory(self, header=True, verbose=False):
        fmt = PORT_HEADER_VERBOSE_FMT if verbose else PORT_HEADER_FMT
	if header:
            hdr = fmt.format('TARGET NAME', 'PROTOCOL', 'TARGET ALIAS')
            print '\n', hdr

        for port in self.curr['port']:
            line = fmt.format(
                self.curr['port'][port]['target-name'],
                self.curr['port'][port]['protocol'],
                self.curr['port'][port]['target-alias'])
            print line

    def lustat(self, header=True, verbose=False):
        for lu in self.curr['lu']:
	    if lu in self.last['lu']: 
                stat1 = self.last['lu'][lu]['io']
            else:
                stat1 = EMPTY_IO_STAT
            stat2 = self.curr['lu'][lu]['io']
	print self.curr['lu'][lu]['lun-guid'], kstatrate(stat1, stat2)

    def portstat(self, header=True, verbose=False):
        for port in self.curr['port']:
	    print self.curr['port'][port]['target-alias'], self.curr['port'][port]['io']
        #pp.pprint(self.curr['port'])


def main():
    interval = 0
    count = delta = 1
    usage = '%prog [options] interval count'
    parser = optparse.OptionParser(usage=usage, version='%prog r1',
        description='report STMF IO statistics')
    parser.set_defaults(verbose=False, headers=True, luns=False, ports=False)
    parser.add_option('-i', '--inventory', action='store_true',
        dest='inventory', help='show list of ports and logical units')
    parser.add_option('-l', '--lun', action='store_true', dest='luns', help='show LU stats')
    parser.add_option('-p', '--port', action='store_true', dest='ports', help='show ports stats')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose', help='be verbose')
    options, args = parser.parse_args()
    if len(args) > 1:
        interval = int(args[0])
        count = int(args[1])
        delta = 1
    elif len(args) == 1:
        interval = int(args[0])
        count = 1
        delta = 0

    #print type(options), options, args

    stats = STMFStats()

    if options.inventory:
        stats.portinventory(options.headers, options.verbose)
        stats.luinventory(options.headers, options.verbose)
        return

    while True:
	if options.ports:
            stats.portstat()
	if options.luns:
            stats.lustat()
        count -= delta
        if count:
            time.sleep(interval)
            stats.update()
        else:
            break

    #print stmfkstat()
    #stats.portinventory(True)


if __name__ == '__main__':
    main()

