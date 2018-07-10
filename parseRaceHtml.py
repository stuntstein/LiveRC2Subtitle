
'''
# heat tag:
Start tag: span
     attr: ('class', 'class_header')
Data     : 13.5 Stadium Truck A-Main
End tag  : span

Start tag: span
     attr: ('class', 'race_length')
Data     : Length: 6:00 Minutes
End tag  : span


Start tag: span
     attr: ('class', 'race_status')
Data     : Status: Complete (
Start tag: a
     attr: ('href', '/results/?p=view_race_result&id=1311848')
Data     : View Results
End tag  : a
Data     : )
End tag  : span

Start tag: td
Start tag: span
     attr: ('class', 'car_num')
Data     : 1
End tag  : span
Data     : Erik Brewster
End tag  : td

create 
parse html page
when attr: ('class', 'class_header') found start new 'heats' dict to list 'race' with
str 'raceName'
int 'raceLength'
list 'qualOrder'
list 'lapData'
when attr: ('href', '/results/?p=view_race_result&id=1311848') call parseHeatHtml and add data to 'lapData'
when attr: ('class', 'race_length') found add data to 'raceLength'
when attr: ('class', 'car_num') found add second data to 'qualOrder' 

'''



import urllib
from HTMLParser import HTMLParser, HTMLParseError
#from htmlentitydefs import name2codepoint
from parseHeatHtml import parseHeatHtml

class _HTMLToRace(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
#        self.text = ''
#        self._buf = []
#        self.hide_output = True
        self.state = 'None'
        self.raceData = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            if self.state == 'getHeatResult':
                for attr in attrs:
                    if len(attr) == 2:
                        self.raceData['heats'][len(self.raceData['heats'])-1]['link'] = attr[1]

        if tag == 'span':
            for attr in attrs:
                if len(attr) == 2:
                    if attr[0] == 'class':
                        if attr[1] == 'class_header':
                            self.state = 'getClass'
                            return
                        if attr[1] == 'race_length':
                            self.state = 'getRaceLength'
                            return
                        if attr[1] == 'car_num':
                            self.state = 'getQualDriver'
                            return
                        if attr[1] == 'race_status':
                            self.state = 'getHeatResult'
                            return
                        if attr[1] == 'fa fa-list-ol':
                            self.state = 'getTitle'
                            return
                        if attr[1] == 'fa fa-calendar':
                            self.state = 'getDate'
                            return
                        if attr[1] == 'fa fa-road':
                            self.state = 'getTrackName'
                            return

    def handle_data(self, data):
        if self.state == 'None':
            return
        
        if self.state == 'getClass':
            self.raceData['heats'].append([])
            self.raceData['heats'][len(self.raceData['heats'])-1] = {}
            self.raceData['heats'][len(self.raceData['heats'])-1]['qualOrder'] = []
            self.raceData['heats'][len(self.raceData['heats'])-1]['class'] = data.lstrip().rstrip()
            self.state = 'None'
            return
        if self.state == 'getRaceLength':
            (a,b,c) = [t(s) for t,s in zip((str,str,str),data.split())]
            if a == 'Length:' and c == 'Minutes':
                duration = int(float(b.replace(':','.'))*60)
            else:
                duration = 300 # default 5 minutes
            self.raceData['heats'][len(self.raceData['heats'])-1]['length'] = duration
            self.state = 'None'
            return
        if self.state == 'getQualDriver':
            self.state = 'getQualDriverName'
            return
        if self.state == 'getQualDriverName':
            self.raceData['heats'][len(self.raceData['heats'])-1]['qualOrder'].append(data.lstrip().rstrip())
            self.state = 'None'
            return
        if self.state == 'getTitle':
            self.raceData['title'] = data.lstrip().rstrip()
            self.raceData['heats'] = []
            self.state = 'None'
            return
        if self.state == 'getDate':
            self.raceData['date'] = data.lstrip().rstrip()
            self.state = 'None'
            return
        if self.state == 'getTrackName':
            self.raceData['track'] = data.lstrip().rstrip()
            self.state = 'None'
            return

    def get_data(self):
        return self.raceData
     

def parseRaceHtml(url, proxies=None, debug=None):
    """
    Given a piece of HTML, return the plain text it contains.
    This handles entities and char refs, but not javascript and stylesheets.
    """

    if url != '':
        # For fetching from internet
        pageSource = urllib.urlopen(url,proxies).read()
        fo = open('race_from_web.html','w')
        fo.write(pageSource)
        fo.close()
    else:
        ## For offline testing
        file = open('race_from_web.html')    # instead of reading from web
        pageSource = file.read()
        file.close

    parser = _HTMLToRace()
    try:
        parser.feed(pageSource)
        parser.close()
    except HTMLParseError:
        pass

    data = parser.get_data()
    hostLink = url.split('//', 1)
    hostLink = hostLink[0]+'//'+hostLink[1].split('/', 1)[0]

    for heat in data['heats']:
        heatResult = parseHeatHtml(hostLink + heat['link'],proxies, debug)
        heat['lapData'] = heatResult
    return data
