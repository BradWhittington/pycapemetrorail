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
                values.append(value)
            timetable.append((title, values))

    train_nums = timetable[0]
    data = Dataset()
    data.headers = train_nums[1]
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
    Return a timetable for the specified zone, start_station, end_station and period

    :param zone: String representing a rail area/zone
    :param start_station: String representing a departure station
    :param finish_station: String represeting a arrival station
    :param browser: (optional) `Mechanize.browser` instance
    :param link: (optional) String representing a timetable HTML page
    """
    if browser and link:
        return fetch_timetable(browser, link)
    else:
        browser = mechanize.Browser()
        timetables = fetch_all_timetables(browser)
        return fetch_timetable(browser, timetables[zone][(start,finish)][period])


if __name__ == '__main__':
    if '--debug' in clint.args.grouped:
        debug=True
    zone = clint.args.grouped.get('--zone',['South'])[0]
    start = clint.args.grouped.get('--from',['ST'])[0]
    finish = clint.args.grouped.get('--to',['CT'])[0]
    period = clint.args.grouped.get('--period',['MonFri'])[0]
    station = clint.args.grouped.get('--station',['Fish Hoek'])[0]
    puts('Zone: '+zone)
    puts('Service line: %s to %s' % (area_nicename.get(start,start),area_nicename.get(finish,finish)))
    puts('Time: '+period_nicename[period])

    timetable_data = timetable(zone=zone, start=start, finish=finish, period=period)
    with indent(2):
        puts('Station: ' + station)
        with indent(2):
            for train, time in timetable_data.filter(station).dict[0].items():
                if train and time:
                    puts('%s: %s' % (train, time))
