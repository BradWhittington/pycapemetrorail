from collections import defaultdict
#from ordereddict import OrderedDict
import mechanize
from tablib import Dataset
from BeautifulSoup import BeautifulSoup
from clint.textui import puts, indent, colored

debug = False
local_browser = mechanize.Browser()
base_url = "http://www.capemetrorail.co.za/"
area_nicename = {
    "ST":"Simonstown",
    "CT":"Cape Town",
    "STR":"Strand",
    "WOR":"Worchester",
    "KYL":"Khayelitsha",
    "MV":"Bellville",
    "CF":"Retreat",
}
period_nicename = {
    "MonFri":"Monday to Friday",
    "MonSun":"Monday to Sunday",
    "Sun":"Sunday & public holidays",
    "Sat":"Saturday",

}
def sub_dict():
    return defaultdict(dict)

def fetch_all_timetables(browser):
    # Fetch the homepage for capemetro, and click the Timetables link
    tables = defaultdict(sub_dict)
    browser.open(base_url)
    timetables = browser.follow_link(text="Timetables")

    # Iterate over all the links on the timetable page and get the URLs for timetables, using zone/start/end/period
    for link in browser.links():
        if 'html' in link.text and 'Business_Express' not in link.url:
            (date, zone, title) = link.url.split('/')
            (start, end, period) = title.split('_')[:3]
            tables[zone][(start,end)][period] = link

    if debug:
        #Print retrieved/organized data
        for zone, directions in tables.items():
            puts(zone)
            with indent(2):
                for direction, periods in directions.items():
                    puts("From:%s, to:%s" % (area_nicename[direction[0]], area_nicename[direction[1]]))
                    with indent(2):
                        for period, link in periods.items():
                            puts("%s - %s" % (period_nicename[period], link))
    return tables

def fetch_timetable(browser, link):
    # Utility method to return a nice Dataset from a timetable url
    response = browser.follow_link(link)
    soup = BeautifulSoup(response.read())
    table = soup.find('table')
    timetable = []
    for row in table.findAll('tr'):
        title=None
        title_test = row.find('td')
        if title_test.find('span'):
            title = title_test.getText()
            values = []
            for col in row.findAll('td')[1:]:
                value=col.getText()
                if value=='&nbsp;':
                    value = None
                values.append(value)
            timetable.append((title,values))
    
    train_nums = timetable[0]
    data = Dataset()
    data.headers=train_nums[1]
    for place, times in timetable[1:]:
        data.rpush(times,tags=[place.title().replace('`S',"'s")]) 

    #Strip out TRAIN NO. columns
    while 1:
        try:
            del data['TRAIN NO.']
        except:
            break

    return data

if __name__ == '__main__':
    timetables = fetch_all_timetables(local_browser)
    timetable = fetch_timetable(local_browser, timetables['South'][('ST','CT')]['MonFri'])
    puts('Timetable for Fish Hoek:')
    with indent(2):
        for train, time in timetable.filter('Fish Hoek').dict[0].items():
            puts('%s: %s' % (train,time))
        
