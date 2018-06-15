"""
NorcalScore2Subtitle
"""

'''
20180518
'''

import urllib
#import json    # json to dict (with unicode)
import ast  # json to dict (no unicode)
from HTMLParser import HTMLParser, HTMLParseError

class _HTMLToHeat(HTMLParser):

    # return substring starting just after findChar
    # ex: stringFrom("asdfghjkl", "d") returns "fghjkl"
    def __stringFrom(self,myStr, findChar):
        startIndex = myStr.find(findChar)
        return myStr[startIndex+1:]

    # return substring ending just before findchar
    # ex: stringBefore("asdfghjkl", "df") returns "as"
    def __stringBefore(self,myStr, findChar):
        endIndex = myStr.find(findChar)
        return myStr[:endIndex]


    def __init__(self):
        HTMLParser.__init__(self)
#        self.text = ''
#        self._buf = []
#        self.hide_output = True
        self.tag = {}
        self.state = 'None'
        self.extraData = []
        self.heatData = []

    def handle_starttag(self, tag, attrs):
        self.tag['tag'] = tag
        self.tag['attr'] = attrs
        if tag == 'span':
            for attr in attrs:            
                if len(attr) == 2:
                    if attr[0] == 'class':
                        if attr[1] == 'car_num':
                            self.state = 'getDriver'
                            return
                        if attr[1] == 'driver_name':
                            self.state = 'getDriverName'
                            return
        if tag == 'script':
            for attr in attrs:
                if len(attr) == 2:
                    if attr[0] == 'type':
                        if attr[1] == 'text/javascript':
                            self.state = 'getLapData'
                            return

    def handle_data(self, data):
        self.tag['data'] = data

        if self.state == 'None':
            return

        if self.state == 'getDriver':
            self.extraData.append([])
            self.extraData[len(self.extraData)-1] = {}
            self.extraData[len(self.extraData)-1]['carNum']  = int(data.lstrip().rstrip())
            self.state = 'None'
            return
        if self.state == 'getDriverName':
            self.extraData[len(self.extraData)-1]['driverName']  = data.lstrip().rstrip()
            self.state = 'getDriverQualPos'
            self.tag['tag'] = ''
            return
        if self.state == 'getDriverQualPos':
            if self.tag['tag'] == 'td':  # first td after DriverName is qualifing position
                self.extraData[len(self.extraData)-1]['qualPos'] = int(data.lstrip().rstrip())
                self.state = 'getDriverTotalLapsTime'
                self.tag['tag'] = ''
                return
        if self.state == 'getDriverTotalLapsTime':
            if self.tag['tag'] == 'td':  # Second td after driverName is total Laps/time
                try:
                    (a,b) = [t(s) for t,s in zip((int,str) , data.split('/'))]
                except:
                    a = 0
                    b = 0
                self.extraData[len(self.extraData)-1]['totalLaps'] = a
                self.extraData[len(self.extraData)-1]['totalTime'] = b
                self.state = 'None'
                return
        if self.state == 'getLapData':
            if 'racerLaps' in data:
                driverDataStrings = data.split("positionDataDriver.label")[1:]

            #for string in driverDataStrings:
                for string in driverDataStrings:
                    #try:
                    trimmedStr = self.__stringFrom(string, ";")
                    trimmedStr = self.__stringFrom(trimmedStr, "= {")
                    trimmedStr = self.__stringBefore(trimmedStr, "positionDataDriver.data.push")
            # get rid of lots of whitespace
                    trimmedStr = trimmedStr.replace("\t","").replace("\n","")
            # strip leading and trailing spaces
                    trimmedStr = trimmedStr.strip()
            # js uses single quotes, json does not
                    trimmedStr = trimmedStr.replace("\'", "\"")
            # get rid of a trailing semicolon
                    if trimmedStr[-1] == ";":
                        trimmedStr = trimmedStr[:-1]
            # get rid of trailing comma
                    if trimmedStr[-3] == ",":
                        trimmedStr = trimmedStr[:-3] + trimmedStr[-2:]

                    self.heatData.append(ast.literal_eval(trimmedStr))   # convert JSON to dict (no unicode)

            self.state = 'None'
            return

    def getHeatData(self):
        # find each driver in heatData and add extraData
        for heatDriver in self.heatData:
            ## adjust driver names in json data
            heatDriver['driverName'] = heatDriver['driverName'].replace('\"','\'').rstrip().lstrip()
            for extra in self.extraData:
                if heatDriver['driverName'] == extra['driverName']:
                    heatDriver.update(extra)
                    self.extraData.remove(extra)
                    break
        return self.heatData

def parseHeatHtml(url, proxies=None, debug=None):

    if debug:
        print '## DEBUG ##'
        print 'Read from file'
        fo = open('heat_from_web.html','r')
        pageSource = fo.read()
        fo.close()
    else:
        pageSource = urllib.urlopen(url, proxies=proxies).read()

        fo = open('heat_from_web.html','w')
        fo.write(pageSource)
        fo.close()

    ## Get final result
    parser = _HTMLToHeat()
    try:
        parser.feed(pageSource)
        parser.close()
    except HTMLParseError:
        pass

    return parser.getHeatData()
