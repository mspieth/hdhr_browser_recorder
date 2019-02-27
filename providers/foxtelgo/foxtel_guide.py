# import sys
# import os
# import pprint
import lxml.html
import aiohttp
# import asyncio

USER_AGENT = \
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3445.2 Safari/537.36'

'''
['TV H!TS',
 'UKTV',
 'Lifestyle Channel',
 'FOX8',
 '111 funny',
 'Arena',
 'Universal TV',
 'FOX SHOWCASE',
 'BBC First',
 '13th Street',
 'BoxSets',
 'Binge',
 'Comedy Channel',
 'A&E',
 'Syfy',
 'MTV',
 'E!',
 'The Style Network',
 'Lifestyle Food',
 'Lifestyle Home',
 'TLC',
 'TVSN',
 'Premiere',
 'Family',
 'Disney Movies',
 'Comedy',
 'Action',
 'Thriller',
 'Romance',
 'Masterpiece',
 'Movie Greats',
 'More Movies',
 'FOX SPORTS NEWS',
 'FOX CRICKET',
 'FOX League',
 'FOX SPORTS 503',
 'FOOTY PLAY',
 'FOOTY PLAY +',
 'FOX SPORTS 505',
 'FOX SPORTS 506',
 'Fox Sports More',
 'ESPN',
 'ESPN2',
 'Eurosport',
 'beIN SPORTS 1',
 'beIN SPORTS 2',
 'beIN SPORTS 3',
 'Chelsea TV',
 'LFCTV',
 'MUTV',
 'SKY NEWS',
 'Your Money',
 'SKY Weather',
 'SKY NEWS Extra',
 'SKY NEWS UK',
 'FOX News',
 'CNN International',
 'HISTORY',
 'Crime + Investigation Network',
 'Discovery Channel',
 'National Geographic',
 'BBC Knowledge',
 'Discovery Science',
 'Discovery Turbo',
 'Animal Planet',
 'Nat Geo WILD',
 'CNBC',
 'BBC World News',
 'Nickelodeon',
 'Nick Jr.',
 'CBeebies',
 'Disney Channel',
 'Disney Junior',
 'Cartoon Network',
 'Boomerang',
 'Discovery Kids',
 '[V]',
 'MTV Music',
 'MTV Dance',
 'MAX',
 'Smooth/Arts',
 'CMC']
{'10 BOLD Sydney': {'name': '10 BOLD Sydney', 'number': '140'},
 '10 HD Sydney': {'name': '10 HD Sydney', 'number': '210'},
 '10 Peach Sydney': {'name': '10 Peach Sydney', 'number': '141'},
 '10 Sydney': {'name': '10 Sydney', 'number': '110'},
 '111 funny': {'name': '111 funny', 'number': '111'},
 '111 funny +2': {'name': '111 funny +2', 'number': '154'},
 '13TH STREET': {'name': '13TH STREET', 'number': '117'},
 '13th STREET +2': {'name': '13th STREET +2', 'number': '160'},
 '13th Street HD': {'name': '13th Street HD', 'number': '218'},
 '7Flix NSW': {'name': '7Flix NSW', 'number': '187'},
 '7HD Sydney': {'name': '7HD Sydney', 'number': '207'},
 '7TWO Sydney': {'name': '7TWO Sydney', 'number': '137'},
 '7mate Sydney': {'name': '7mate Sydney', 'number': '138'},
 '9Gem Sydney': {'name': '9Gem Sydney', 'number': '192'},
 '9Go! Sydney': {'name': '9Go! Sydney', 'number': '139'},
 '9HD Sydney': {'name': '9HD Sydney', 'number': '209'},
 '9Life Sydney': {'name': '9Life Sydney', 'number': '194'},
 'A&E': {'hd_number': '222', 'name': 'A&E', 'number': '122'},
 'A&E +2': {'name': 'A&E +2', 'number': '611'},
 'A&E HD': {'name': 'A&E HD', 'number': '222', 'sd_number': '122'},
 'ABC HD': {'name': 'ABC HD', 'number': '202'},
 'ABC ME Sydney': {'name': 'ABC ME Sydney', 'number': '723'},
 'ABC NSW': {'name': 'ABC NSW', 'number': '102'},
 'ABC News': {'name': 'ABC News', 'number': '642'},
 'ABCComedy/Kids': {'name': 'ABCComedy/Kids', 'number': '134'},
 'ACC': {'name': 'ACC', 'number': '182'},
 'Action': {'hd_number': '245', 'name': 'Action', 'number': '405'},
 'Action +2': {'name': 'Action +2', 'number': '412'},
 'Action HD': {'name': 'Action HD', 'number': '245', 'sd_number': '405'},
 'Al Jazeera': {'name': 'Al Jazeera', 'number': '651'},
 'Animal Planet': {'name': 'Animal Planet', 'number': '621'},
 'Antenna Pacific': {'name': 'Antenna Pacific', 'number': '941'},
 'Arena': {'hd_number': '205', 'name': 'Arena', 'number': '112'},
 'Arena +2': {'name': 'Arena +2', 'number': '151'},
 'Arena HD': {'name': 'Arena HD', 'number': '205', 'sd_number': '112'},
 'Aurora': {'name': 'Aurora', 'number': '173'},
 'BBC First': {'hd_number': '217', 'name': 'BBC First', 'number': '116'},
 'BBC First HD': {'name': 'BBC First HD', 'number': '217', 'sd_number': '116'},
 'BBC Knowledge': {'hd_number': '272',
                   'name': 'BBC Knowledge',
                   'number': '614'},
 'BBC Knowledge HD': {'name': 'BBC Knowledge HD',
                      'number': '272',
                      'sd_number': '614'},
 'BBC World News': {'name': 'BBC World News', 'number': '649'},
 'Binge': {'hd_number': '216', 'name': 'Binge', 'number': '119'},
 'Binge HD': {'name': 'Binge HD', 'number': '216', 'sd_number': '119'},
 'Bloomberg Television': {'name': 'Bloomberg Television', 'number': '650'},
 'Boomerang': {'name': 'Boomerang', 'number': '715'},
 'BoxSet HD': {'name': 'BoxSet HD', 'number': '215'},
 'BoxSets': {'name': 'BoxSets', 'number': '118'},
 'CGTN': {'name': 'CGTN', 'number': '653'},
 'CGTN-Documentary': {'name': 'CGTN-Documentary', 'number': '654'},
 'CMC': {'name': 'CMC', 'number': '815'},
 'CNBC': {'name': 'CNBC', 'number': '644'},
 'CNN': {'name': 'CNN', 'number': '607'},
 'Cartoon Network': {'name': 'Cartoon Network', 'number': '713'},
 'Cbeebies': {'name': 'Cbeebies', 'number': '705'},
 'Channel 7 Sydney': {'name': 'Channel 7 Sydney', 'number': '107'},
 'Channel 9 Sydney': {'name': 'Channel 9 Sydney', 'number': '100'},
 'Chelsea TV': {'name': 'Chelsea TV', 'number': '516'},
 'Chelsea TV HD ': {'name': 'Chelsea TV HD ', 'number': '283'},
 'Comedy': {'hd_number': '244', 'name': 'Comedy', 'number': '404'},
 'Comedy Ch +2': {'name': 'Comedy Ch +2', 'number': '162'},
 'Comedy HD': {'name': 'Comedy HD', 'number': '244', 'sd_number': '404'},
 'Crime': {'name': 'Crime', 'number': '609'},
 'Daystar': {'name': 'Daystar', 'number': '185'},
 'Discovery +2': {'name': 'Discovery +2', 'number': '635'},
 'Discovery Channel': {'name': 'Discovery Channel', 'number': '612'},
 'Discovery HD': {'name': 'Discovery HD', 'number': '268'},
 'Discovery Kids': {'name': 'Discovery Kids', 'number': '718'},
 'Discovery Science': {'name': 'Discovery Science', 'number': '616'},
 'Discovery Turbo': {'name': 'Discovery Turbo', 'number': '620'},
 'Discovery Turbo +2': {'name': 'Discovery Turbo +2', 'number': '640'},
 'Disney Channel': {'name': 'Disney Channel', 'number': '707'},
 'Disney Junior': {'name': 'Disney Junior', 'number': '709'},
 'Disney Mov +2': {'name': 'Disney Mov +2', 'number': '415'},
 'Disney Movies': {'hd_number': '243',
                   'name': 'Disney Movies',
                   'number': '403'},
 'Disney Movies HD': {'name': 'Disney Movies HD',
                      'number': '243',
                      'sd_number': '403'},
 'E! Entertainment': {'name': 'E! Entertainment', 'number': '125'},
 'ESPN': {'hd_number': '261', 'name': 'ESPN', 'number': '508'},
 'ESPN HD': {'name': 'ESPN HD', 'number': '261', 'sd_number': '508'},
 'ESPN2': {'hd_number': '262', 'name': 'ESPN2', 'number': '509'},
 'ESPN2 HD': {'name': 'ESPN2 HD', 'number': '262', 'sd_number': '509'},
 'EXPO': {'name': 'EXPO', 'number': '177'},
 'Eurosport': {'hd_number': '263', 'name': 'Eurosport', 'number': '511'},
 'Eurosport HD': {'name': 'Eurosport HD', 'number': '263', 'sd_number': '511'},
 'FOX CRICKET': {'hd_number': '255', 'name': 'FOX CRICKET', 'number': '501'},
 'FOX CRICKET HD': {'name': 'FOX CRICKET HD',
                    'number': '255',
                    'sd_number': '501'},
 'FOX Classics': {'name': 'FOX Classics', 'number': '113'},
 'FOX Classics+2': {'name': 'FOX Classics+2', 'number': '156'},
 'FOX LEAGUE': {'hd_number': '256', 'name': 'FOX LEAGUE', 'number': '502'},
 'FOX LEAGUE HD': {'name': 'FOX LEAGUE HD',
                   'number': '256',
                   'sd_number': '502'},
 'FOX News': {'name': 'FOX News', 'number': '606'},
 'FOX SHOWCASE': {'hd_number': '214', 'name': 'FOX SHOWCASE', 'number': '115'},
 'FOX SHOWCASE +2': {'name': 'FOX SHOWCASE +2', 'number': '158'},
 'FOX SHOWCASE HD': {'name': 'FOX SHOWCASE HD',
                     'number': '214',
                     'sd_number': '115'},
 'FOX SPORTS 503': {'hd_number': '257',
                    'name': 'FOX SPORTS 503',
                    'number': '503'},
 'FOX SPORTS 503 HD': {'name': 'FOX SPORTS 503 HD',
                       'number': '257',
                       'sd_number': '503'},
 'FOX SPORTS 505': {'hd_number': '259',
                    'name': 'FOX SPORTS 505',
                    'number': '505'},
 'FOX SPORTS 505 HD': {'name': 'FOX SPORTS 505 HD',
                       'number': '259',
                       'sd_number': '505'},
 'FOX SPORTS 506': {'hd_number': '260',
                    'name': 'FOX SPORTS 506',
                    'number': '506'},
 'FOX SPORTS 506 HD': {'name': 'FOX SPORTS 506 HD',
                       'number': '260',
                       'sd_number': '506'},
 'FOX SPORTS MORE': {'hd_number': '264',
                     'name': 'FOX SPORTS MORE',
                     'number': '507'},
 'FOX SPORTS MORE HD': {'name': 'FOX SPORTS MORE HD',
                        'number': '264',
                        'sd_number': '507'},
 'FOX8': {'hd_number': '208', 'name': 'FOX8', 'number': '108'},
 'FOX8 HD': {'name': 'FOX8 HD', 'number': '208', 'sd_number': '108'},
 'FOX8+2': {'name': 'FOX8+2', 'number': '153'},
 'Family': {'hd_number': '242', 'name': 'Family', 'number': '402'},
 'Family +2': {'name': 'Family +2', 'number': '414'},
 'Family HD': {'name': 'Family HD', 'number': '242', 'sd_number': '402'},
 'Fox Footy': {'hd_number': '258', 'name': 'Fox Footy', 'number': '504'},
 'Fox Footy HD': {'name': 'Fox Footy HD', 'number': '258', 'sd_number': '504'},
 'Fox News HD': {'name': 'Fox News HD', 'number': '293'},
 'Fox Sports News': {'hd_number': '254',
                     'name': 'Fox Sports News',
                     'number': '500'},
 'Fox Sports News HD': {'name': 'Fox Sports News HD',
                        'number': '254',
                        'sd_number': '500'},
 'Hillsong Channel': {'name': 'Hillsong Channel', 'number': '183'},
 'History HD': {'name': 'History HD', 'number': '271'},
 'LFCTV': {'name': 'LFCTV', 'number': '517'},
 'LFCTV HD ': {'name': 'LFCTV HD ', 'number': '284'},
 'Lifestyle +2': {'name': 'Lifestyle +2', 'number': '152'},
 'Lifestyle FOOD': {'name': 'Lifestyle FOOD', 'number': '127'},
 'Lifestyle FOOD +2': {'name': 'Lifestyle FOOD +2', 'number': '164'},
 'Lifestyle HD': {'name': 'Lifestyle HD', 'number': '206'},
 'Lifestyle Home': {'name': 'Lifestyle Home', 'number': '128'},
 'MAX': {'name': 'MAX', 'number': '805'},
 'MTV': {'name': 'MTV', 'number': '124'},
 'MTV Dance': {'name': 'MTV Dance', 'number': '804'},
 'MTV Music': {'name': 'MTV Music', 'number': '803'},
 'MUTV': {'hd_number': '285', 'name': 'MUTV', 'number': '518'},
 'MUTV HD': {'name': 'MUTV HD', 'number': '285', 'sd_number': '518'},
 'Masterpiece': {'hd_number': '248', 'name': 'Masterpiece', 'number': '408'},
 'Masterpiece HD': {'name': 'Masterpiece HD',
                    'number': '248',
                    'sd_number': '408'},
 'More Movies': {'hd_number': '251', 'name': 'More Movies', 'number': '410'},
 'More Movies HD': {'name': 'More Movies HD',
                    'number': '251',
                    'sd_number': '410'},
 'Movie Greats': {'hd_number': '249', 'name': 'Movie Greats', 'number': '409'},
 'Movie Greats HD': {'name': 'Movie Greats HD',
                     'number': '249',
                     'sd_number': '409'},
 'NHK World-Japan': {'name': 'NHK World-Japan', 'number': '656'},
 'NITV': {'name': 'NITV', 'number': '144'},
 'Nat Geo +2': {'name': 'Nat Geo +2', 'number': '641'},
 'Nat Geo HD': {'name': 'Nat Geo HD', 'number': '270'},
 'Nat Geo Wild': {'hd_number': '276', 'name': 'Nat Geo Wild', 'number': '622'},
 'Nat Geo Wild HD': {'name': 'Nat Geo Wild HD',
                     'number': '276',
                     'sd_number': '622'},
 'National Geographic': {'name': 'National Geographic', 'number': '613'},
 'Nick Jr.': {'name': 'Nick Jr.', 'number': '703'},
 'Nickelodeon': {'name': 'Nickelodeon', 'number': '701'},
 'Premiere': {'hd_number': '241', 'name': 'Premiere', 'number': '401'},
 'Premiere +2': {'name': 'Premiere +2', 'number': '411'},
 'Premiere HD': {'name': 'Premiere HD', 'number': '241', 'sd_number': '401'},
 'RACING.COM': {'name': 'RACING.COM', 'number': '529'},
 'RAI ITALIA': {'name': 'RAI ITALIA', 'number': '942'},
 'Romance': {'hd_number': '247', 'name': 'Romance', 'number': '407'},
 'Romance HD': {'name': 'Romance HD', 'number': '247', 'sd_number': '407'},
 'Russia Today': {'name': 'Russia Today', 'number': '658'},
 'SBS Food NSW': {'name': 'SBS Food NSW', 'number': '143'},
 'SBS HD': {'name': 'SBS HD', 'number': '228'},
 'SBS Sydney': {'name': 'SBS Sydney', 'number': '104'},
 'SBS VICELAND': {'name': 'SBS VICELAND', 'number': '142'},
 'SKY News Live': {'name': 'SKY News Live', 'number': '600'},
 'SKY Racing': {'name': 'SKY Racing', 'number': '526'},
 'SKY Racing 2': {'name': 'SKY Racing 2', 'number': '527'},
 'SKY Tbred Cent': {'hd_number': '265',
                    'name': 'SKY Tbred Cent',
                    'number': '528'},
 'SKY Tbred Cent HD': {'name': 'SKY Tbred Cent HD',
                       'number': '265',
                       'sd_number': '528'},
 'SKY Weather': {'name': 'SKY Weather', 'number': '603'},
 'Sky News Extra': {'name': 'Sky News Extra', 'number': '604'},
 'Sky News Live HD': {'name': 'Sky News Live HD', 'number': '291'},
 'Sky News UK': {'hd_number': '292', 'name': 'Sky News UK', 'number': '605'},
 'Sky News UK HD': {'name': 'Sky News UK HD',
                    'number': '292',
                    'sd_number': '605'},
 'Smooth / Arts': {'hd_number': '233',
                   'name': 'Smooth / Arts',
                   'number': '133'},
 'Smooth / Arts HD': {'name': 'Smooth / Arts HD',
                      'number': '233',
                      'sd_number': '133'},
 'SonLife': {'name': 'SonLife', 'number': '186'},
 'Style': {'name': 'Style', 'number': '126'},
 'Syfy': {'hd_number': '223', 'name': 'Syfy', 'number': '123'},
 'Syfy +2': {'name': 'Syfy +2', 'number': '163'},
 'Syfy HD': {'name': 'Syfy HD', 'number': '223', 'sd_number': '123'},
 'TLC': {'name': 'TLC', 'number': '130'},
 'TLC +2': {'name': 'TLC +2', 'number': '166'},
 'TRT World': {'name': 'TRT World', 'number': '652'},
 'TVH!TS': {'name': 'TVH!TS', 'number': '101'},
 'TVH!TS +2': {'name': 'TVH!TS +2', 'number': '149'},
 'TVSN': {'name': 'TVSN', 'number': '176'},
 'The Comedy Channel': {'name': 'The Comedy Channel', 'number': '121'},
 'The History Channel': {'name': 'The History Channel', 'number': '608'},
 'The Lifestyle Channel': {'name': 'The Lifestyle Channel', 'number': '106'},
 'Thriller': {'hd_number': '246', 'name': 'Thriller', 'number': '406'},
 'Thriller HD': {'name': 'Thriller HD', 'number': '246', 'sd_number': '406'},
 'UKTV': {'name': 'UKTV', 'number': '105'},
 'UKTV+2': {'name': 'UKTV+2', 'number': '150'},
 'Universal +2': {'name': 'Universal +2', 'number': '155'},
 'Universal HD': {'name': 'Universal HD', 'number': '212'},
 'Universal TV': {'name': 'Universal TV', 'number': '114'},
 'Your Money': {'hd_number': '290', 'name': 'Your Money', 'number': '601'},
 'Your Money HD': {'name': 'Your Money HD',
                   'number': '290',
                   'sd_number': '601'},
 '[V]': {'name': '[V]', 'number': '801'},
 '[V] +2': {'name': '[V] +2', 'number': '802'},
 'beIN SPORTS 1': {'hd_number': '280',
                   'name': 'beIN SPORTS 1',
                   'number': '513'},
 'beIN SPORTS 1 HD': {'name': 'beIN SPORTS 1 HD',
                      'number': '280',
                      'sd_number': '513'},
 'beIN SPORTS 2': {'hd_number': '281',
                   'name': 'beIN SPORTS 2',
                   'number': '514'},
 'beIN SPORTS 2 HD': {'name': 'beIN SPORTS 2 HD',
                      'number': '281',
                      'sd_number': '514'},
 'beIN SPORTS 3': {'hd_number': '282',
                   'name': 'beIN SPORTS 3',
                   'number': '515'},
 'beIN SPORTS 3 HD': {'name': 'beIN SPORTS 3 HD',
                      'number': '282',
                      'sd_number': '515'},
 'foxtel 4K': {'name': 'foxtel 4K', 'number': '444'}}
# number for channel 'TV H!TS' not found
# number for channel 'Lifestyle Channel' not found
# number for channel '13th Street' not found
# number for channel 'Comedy Channel' not found
# number for channel 'E!' not found
# number for channel 'The Style Network' not found
# number for channel 'Lifestyle Food' not found
# number for channel 'FOX SPORTS NEWS' not found
# number for channel 'FOX League' not found
# number for channel 'FOOTY PLAY' not found
# number for channel 'FOOTY PLAY +' not found
# number for channel 'Fox Sports More' not found
# number for channel 'SKY NEWS' not found
# number for channel 'SKY NEWS Extra' not found
# number for channel 'SKY NEWS UK' not found
# number for channel 'CNN International' not found
# number for channel 'HISTORY' not found
# number for channel 'Crime + Investigation Network' not found
# number for channel 'Nat Geo WILD' not found
# number for channel 'CBeebies' not found
# number for channel 'Smooth/Arts' not found
'''

_channel_remap = {
    'TV H!TS': 'TVH!TS',
    'Lifestyle Channel': 'The Lifestyle Channel',
    '13th Street': '13TH STREET',
    'Comedy Channel': 'The Comedy Channel',
    'E!': 'E! Entertainment',
    'The Style Network': 'Style',
    'Lifestyle Food': 'Lifestyle FOOD',
    'FOX SPORTS NEWS': 'Fox Sports News',
    'FOX League': 'FOX LEAGUE',
    'FOOTY PLAY': 'Fox Footy',
    # 'FOOTY PLAY +': 'Fox Footy',
    'Fox Sports More': 'FOX SPORTS MORE',
    'SKY NEWS': 'SKY News Live',
    'SKY NEWS Extra': 'Sky News Extra',
    'SKY NEWS UK': 'Sky News UK',
    'CNN International': 'CNN',
    'HISTORY': 'The History Channel',
    'Crime + Investigation Network': 'Crime',
    'Nat Geo WILD': 'Nat Geo Wild',
    'CBeebies': 'Cbeebies',
    'Smooth/Arts': 'Smooth / Arts',
}


async def get_page(url):
    async with aiohttp.ClientSession(headers={'User-Agent': USER_AGENT}) as session:
        async with session.get(url) as resp:
            return await resp.text()


def extract_data_community(document):
    # Generate document tree
    tree = lxml.html.fromstring(document)
    # Select tr with a th and td descendant from table
    # elements = tree.xpath('//div[@id="lia-message-body-content"]/table/tbody/tr[th and td]')
    elements = tree.xpath('//div[@class="lia-message-body-content"]/table/tbody/tr')
    # Extract data
    result = {}
    # header = []
    count = 0
    for element in elements:
        count += 1
        if count == 1:
            continue
        if count == 2:
            # items = element.xpath('td')
            # for item in items:
            #     # print(f"header {item.text_content().strip()}")
            #     header.append(item.text_content().strip())
            continue

        items = element.xpath('td')
        text = items[0].text_content().strip()
        if not text:
            continue
        if '-' not in text:
            continue
        number, name = text.split('-')
        numbers = number.strip().split(' & ')
        name = name.strip()
        # print(f"item {item.text_content().strip()}")
        for number in numbers:
            entry = {
                'number': number,
                'name': name
            }
            result.update({name: entry})
    return result


def extract_data(document):
    # Generate document tree
    tree = lxml.html.fromstring(document)
    elements = tree.xpath('//div[@class="epg-channel-callout"]')
    # Extract data
    result = {}
    for element in elements:
        name, number = element.iterchildren()
        result.update({name.text_content(): {'number': number.text_content(), 'name': name.text_content()}})

    # special extra channel which is not in the standard guide, no guide
    result.update({'FOOTY PLAY +': {'number': 599, 'name': 'FOOTY PLAY +'}})

    return result


def filter_channels(data):
    names = data.keys()
    for channel_name in names:
        if channel_name + " HD" in names:
            name = channel_name
            data[name].update({'hd_number': data[name+' HD']['number']})
            data[name + ' HD'].update({'sd_number': data[name]['number']})
            # print(f"hd equiv {channel_name}")

    return data


def remap_channel_name(name):
    if name in _channel_remap:
        return _channel_remap[name]
    return name


async def get_channel_map(mode=True):
    """
    get dictionary of channels indexed on channel name
        elements have
            name        name of channel, same as key of element
            number      assigned channel number
            hd_number   equivalent hd channel number for an sd channel if exists
            sd_number   equivalent sd channel number for a hd channel if exists
    :return: dict of dicts
    """
    if mode:
        document = await get_page('http://www.foxtel.com.au/tv-guide/grid')
        data = extract_data(document)
        data = filter_channels(data)
    else:
        document = await get_page('https://community.foxtel.com.au/t5/Entertainment/Foxtel-Channel-List/td-p/170370')
        data = extract_data_community(document)

    return data
