import datetime
from collections import defaultdict
import clint
from clint.textui import puts, indent
from BeautifulSoup import BeautifulSoup
import mechanize
from tablib import Dataset

debug = False
local_browser = mechanize.Browser()
base_url = "http://www.capemetrorail.co.za/"
area_nicename = {
    "ST": "Simonstown",
    "CT": "Cape Town",
    "STR": "Strand",
    "WOR": "Worchester",
    "KYL": "Khayelitsha",
    "MV": "Bellville",
    "CF": "Retreat",
}
period_nicename = {
    "MonFri": "Monday to Friday",
    "MonSun": "Monday to Sunday",
    "Sun": "Sunday & public holidays",
    "Sat": "Saturday",

}


def sub_dict():
    return defaultdict(dict)


def fetch_all_timetables(browser):
    # Fetch the homepage for capemetro, and click the Timetables link
    if debug:
        puts("Fetching timetable links")
    tables = defaultdict(sub_dict)
    browser.open(base_url)
    browser.follow_link(text="Timetables")

    # Iterate over all the links on the timetable page and
    # get the URLs for timetables, using zone/start/end/period
    for link in browser.links():
        if 'html' in link.text and 'Business_Express' not in link.url:
            (date, zone, title) = link.url.split('/')
            (start, end, period) = title.split('_')[:3]
            tables[zone][(start, end)][period] = link

    if debug:
        #Print retrieved/organized data
        for zone, directions in tables.items():
            puts(zone)
            with indent(2):
                for direction, periods in directions.items():
                    puts("From:%s, to:%s" % (
                        area_nicename[direction[0]],
                        area_nicename[direction[1]]))
                    with indent(2):
                        for period, link in periods.items():
                            puts("%s - %s" % (period_nicename[period], link))
    return tables


def fetch_timetable(browser, link):
    # Utility method to return a nice Dataset from a timetable url
    if debug:
        puts("Fetching timetable from %s" % link)
    response = browser.follow_link(link)
    soup = BeautifulSoup(response.read())
    table = soup.find('table')
    timetable = []
    for row in table.findAll('tr'):
        title = None
        title_test = row.find('td')
        if title_test.find('span'):
            title = title_test.getText()
            values = []
            for col in row.findAll('td')[1:]:
                value = col.getText()
                if value == '&nbsp;':
                    value = None
                if isinstance(value, basestring) and ':' in value:
                    try:
                        time = value.strip().split(':')
                        time = datetime.time(*[int(s) for s in time])
                    except:
                        pass
                    else:
                        value = time
                values.append(value)
            timetable.append((title, values))

    while len(timetable):
        if 'TRAIN NO.' not in timetable[0][0]:
            del timetable[0]
        else:
            break

    train_nums = timetable[0]
    data = Dataset()
    data.headers = train_nums[1]
    if debug:
        puts(repr(data.headers))
    for place, times in timetable[1:]:
        if debug:
            puts(repr((place, times)))
        data.rpush(times, tags=[place.title().replace('`S', "'s")])

    #Strip out TRAIN NO. columns
    while 1:
        try:
            del data['TRAIN NO.']
        except:
            break

    return data


def timetable(zone, start, finish, period, browser=None, link=None):
    """
    Return a timetable for the specified zone, start_station, end_station and
    period

    :param zone: String representing a rail area/zone
    :param start_station: String representing a departure station
    :param finish_station: String represeting a arrival station
    :param browser: (optional) `Mechanize.browser` instance
    :param link: (optional) String representing a timetable HTML page
    """
    if browser is None:
        browser = mechanize.Browser()
    if link is None:
        timetables = fetch_all_timetables(browser)
        link = timetables[zone][(start, finish)][period]
    return fetch_timetable(browser, link)


if __name__ == '__main__':
    if '--debug' in clint.args.grouped:
        debug = True
    zone = clint.args.grouped.get('--zone', ['South'])[0]
    start = clint.args.grouped.get('--from', ['ST'])[0]
    finish = clint.args.grouped.get('--to', ['CT'])[0]
    period = clint.args.grouped.get('--period', ['MonFri'])[0]
    station = clint.args.grouped.get('--station', ['Fish Hoek'])[0]
    time_window = int(clint.args.grouped.get('--window', [60])[0])
    puts('Zone: ' + zone)
    puts('Service line: %s to %s' % (
        area_nicename.get(start, start),
        area_nicename.get(finish, finish)))
    puts('Time: ' + period_nicename[period])

    data = timetable(zone=zone, start=start, finish=finish, period=period)
    today = datetime.date.today().timetuple()[:3]
    now = datetime.datetime.now()
    with indent(2):
        puts('Station: ' + station)
        with indent(2):
            for train, time in data.filter(station).dict[0].items():
                if train and time:
                    notes = ''
                    time_tuple = today + (time.hour, time.minute)
                    local_time = datetime.datetime(*time_tuple)
                    if local_time > now:
                        minutes = (local_time - now).seconds / 60
                        if minutes < 60:
                            notes = "* leaving in %s minutes" % minutes
                    puts('%s: %s %s' % (train, time, notes))
