#!/bin/python
#
# Copyright 2011 Grigale Ltd. All rigths reserved.
# Use is sujbect to license terms.
#
#import options
import subprocess as sp
import pprint as pp

KSTAT = '/bin/kstat'
PORT = 'stmf_tgt_'
PORTIO = 'stmf_tgt_io'
LU = 'stmf_lu_'
LUIO = 'stmf_lu_io'

def stmfkstat():
    cmd = [KSTAT, '-m', 'stmf', '-p']
    ks = sp.Popen(cmd, stdout=sp.PIPE)
    out, err = ks.communicate()
    if ks.returncode:
        raise IOError
    return out


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

    def portinventory(self, verbose=False):
        for port in self.curr['port']:
            if verbose:
                line = '{0}\t{1}\t\t{2}'.format(
                    self.curr['port'][port]['target-alias'],
                    self.curr['port'][port]['protocol'],
                    self.curr['port'][port]['target-name'])
            else:
                line = self.curr['port'][port]['target-alias']
            print line

def main():
    stats = STMFStats()
    #print stmfkstat()
    stats.portinventory(True)


if __name__ == '__main__':
    main()

