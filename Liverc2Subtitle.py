"""
NorcalScore2Subtitle
"""

'''
20171115 Added heat name
20171114 Fix heat with more than 10 drivers.
20171110 Fix problem with Driver names. Fix for final print out. Clean up
20171212 Added Race Title. Moved generated files to output folder. Added race _duration to subtitle.
'''

from HTMLParser import HTMLParser, HTMLParseError
from htmlentitydefs import name2codepoint
import re
import urllib
import urllib2
#import numpy as np
import sys
import os
import argparse
from parseRaceHtml import parseRaceHtml
import calendar



# drivers must be 'name', lapCnt, lapTime
def addSub(subTime, drivers = None, raceTime = None, _duration = 0, _class=None, _title=None, _date=None, _track=None):
    addSub.count += 1
    if raceTime == None:
        endTime = subTime + 90
    else:
        endTime = subTime + 1

    s = format('%d\n%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n' %
    (addSub.count,
    int(subTime/60/60),int(subTime/60),int(subTime%60),int((subTime*1000)%1000),
    int(endTime/60/60),int(endTime/60),int(endTime%60),int((endTime*1000)%1000)))

    if _track != None:
        s += format('%s\n' % _track)
    if _date != None:
        s += format('%s\n' % _date)
    if _title != None:
        s += format('%s\n' % _title)
    if _class != None:
        s += format('%s\n' % _class)

    if raceTime == None:    # after race has ended
        s += format('%s' % ('Race Over'))
    else:
        if raceTime < 0:
            s += format('-')
        s += format('%02d:%02d / %02d:%02d' % (int(abs(raceTime)/60),int(abs(raceTime)%60),int(_duration/60),int(_duration%60)))

    idx = 0
    if drivers != None:
        for driver in drivers:
            ## if raceTime is running but drivers lap == 0 filter him out
            if driver['name'] != '':        # only if list is not cleared
                if idx % 2 == 0:
                    s += format('\n')
                idx += 1
                if driver['lapCnt'] == 0:   # show qual order if no lap count
                    s += format('[%s] %-15s\t' %
                        (idx, driver['name']))
                else:
                    s += format('[%s] %2d/%5.8s %-15s\t' %
                        (idx, driver['lapCnt'],
                        driver['lapTime'], driver['name']))

    s += format('\n\n')
    return s


def parseResult(raceData):
    ## transverse though list of Heats
    for heat in raceData['heats']:
        print('Class: %s' % heat['class'])
        print('    Qualifying order')
        print('    Number of drivers: %d' % len(heat['qualOrder']))
        order=1
        for driver in heat['qualOrder']:
            print('        %d: %s' % (order,driver))
            order+=1

        ## generate one sorted list by race time
        oneList = []
        for laps in heat['lapData']:
            previousTime = 0.0
            for lap in laps['laps']:
                lap['time'] = float(lap['time']) # convert to float
                lap['pos'] = int(lap['pos'])    # convert to int
                lap['lapNum'] = int(lap['lapNum'])    # convert to int
                lap['raceTime'] = lap['time'] + previousTime
                previousTime = lap['raceTime']
                if lap['raceTime'] > 0.0:    # remove raceTime == 0
                    oneList.append({'lapData':lap, 'driver': laps['driverName']})
        oneList = sorted(oneList, key=lambda x:x['lapData']['raceTime'])

        ## generate subtitle
        fo = open(heat['class'] + '.srt','w')
        addSub.count = 0
        time = 0.0

        ## Init drivers for subtitle text
        drivers = []
        for driverName in heat['qualOrder']:
            drivers.append({'name':driverName,'lapCnt':0,'lapTime':0})

        ## loop through oneList and generate subtitle
        n = 0
        while n < len(oneList):
            raceTime = time - heat['timeOffset']

            if raceTime < 0.0:
                if raceTime >= -2.0 and heat['timeOffset'] > 4:
                    ## clear qual order 2 sec before start only if vid offset >4
                    s = addSub(time, None, raceTime, _duration=heat['length'])
                else:
                    ## show qualifying order
                    s = addSub(time, drivers, raceTime, _duration=heat['length'], _class=heat['class'],_title=raceData['title'],_date=raceData['date'],_track=raceData['track'])
            else:
                if n == 0:
                    # clear driver list
                    for d in drivers:
                        d['name'] = ''
                        d['lapCnt'] = 0
                        d['lapTime'] = 0

                while n < len(oneList) and oneList[n]['lapData']['raceTime'] < raceTime:

                    ## Swap 2 driver positions
                    nextEntry = oneList[n]
                    pos = nextEntry['lapData']['pos'] - 1   # Next entry. Get his position
                    if pos >= len(drivers):         # Sometimes I see a position higher that the number of drivers!
                        pos -= 1                    # If only 1 too high trim it down.
                    else:
                        if pos > len(drivers):      # Stop if pos is too high. Something is bad
                            print 'ERROR',pos,nextEntry
                            exit(1)
                    tmp = drivers[pos]                    # Find the driver on that position
                    if tmp['name'] != nextEntry['driver']:    # Check that it is not the same driver
                    # swap position. Tmp goes to nextEntry's old position
                        nextEntrysOldPos = next((index for (index, d) in enumerate(drivers) if d['name'] == nextEntry['driver']),pos)
                        drivers[pos], drivers[nextEntrysOldPos] = drivers[nextEntrysOldPos], drivers[pos]
                    drivers[pos]['name'] = nextEntry['driver']                # update entry
                    drivers[pos]['lapCnt'] = nextEntry['lapData']['lapNum']      # update entry
                    drivers[pos]['lapTime'] = nextEntry['lapData']['time'] # update entry
                    n += 1

                    ## Check if driver is on last lap then update with finish_order data
                    for driver in heat['lapData']:
                        if driver['driverName'] == drivers[pos]['name']:
                            if driver['totalLaps'] == drivers[pos]['lapCnt']:
                                drivers[pos]['lapTime'] = driver['totalTime']
                s = addSub(time, drivers, raceTime, _duration=heat['length'])

            fo.write(s)
            time += 1

        ## we have no more in the sorted list
        s = addSub(time, drivers, _class=heat['class'],_title=raceData['title'],_date=raceData['date'],_track=raceData['track'])
        fo.write(s)
        fo.close()

    return
## end parseScore(text)

## Create output folder#
def createFolder(raceData):
    ## find date and create folder
    _date = raceData['date']
    _date = _date.replace(',','')
    (month,day,year) = [t(s) for t,s in zip((str,int,int),_date.split())]
    mm = list(calendar.month_abbr).index(month)
    _date = '{:04d}{:02d}{:02d}'.format(year,mm,day)
    path = 'output/' + raceData['track'] + '/'+ _date
    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)
    print('Store files in %s.' % path)

# synchornize start time for each heat
def syncStartTime(raceData):
    print('Found %d heats.' % len(raceData['heats']))
    for heat in raceData['heats']:
        heat['timeOffset'] = 4
        if args.debug == False:
            print('Please type the time ofset from when the race starts.')
            offset = input('Time offset for %s : ' % heat['class'])
            heat['timeOffset'] = offset


### Main
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Fetch Race results from live.liverc.com and convert to a subtitle file to be loaded in youtube.')
    parser.add_argument('--url','-u', dest='url', metavar='<URL>',required=True,
                    help='Url to the page with the race result')

    parser.add_argument('--proxy','-p', dest='proxy')
    parser.add_argument('--verbose','-v', action='store_true')
    parser.add_argument('--debug','-d', action='store_true')

    args = parser.parse_args()
    url = args.url
    verbose = args.verbose
    if args.proxy != None:
        proxies = {}
        proxies['http'] = args.proxy
    else:
        proxies = None

    raceData = parseRaceHtml(url,proxies)
    createFolder(raceData)
    syncStartTime(raceData)
    parseResult(raceData)

    print "Done. Files generate in %s " % os.getcwd()
