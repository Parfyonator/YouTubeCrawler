import ssl
from urllib import request
import requests
import json
from typing import List, Dict, Any
from logging import getLogger

from bs4 import BeautifulSoup
import langdetect


logger = getLogger(__name__)


def full_url(relative_url: str) -> str:
    return f'https://www.youtube.com{relative_url}'


def parse_item_renderer(item_renderer: Dict[str, Any]) -> str:
    return item_renderer["richItemRenderer"]\
                        ["content"]\
                        ["videoRenderer"]\
                        ["longBylineText"]\
                        ["runs"][0]\
                        ["navigationEndpoint"]\
                        ["commandMetadata"]\
                        ["webCommandMetadata"]\
                        ["url"]


def get_initial_data(url: str) -> Dict[str, Any]:
    response = request.urlopen(url, context=ssl._create_unverified_context())
    content = response.read()

    soup = BeautifulSoup(content, 'html.parser')

    body = soup.find("body")
    scripts = body.find_all("script")
    initial_data_script = scripts[1].contents[0].strip()
    first_line = initial_data_script.split('\n')[0]
    rhs = first_line[first_line.find('=')+1:].strip()
    rhs = rhs[:-1] # remove ';' at the end
    
    return json.loads(rhs)


def parse_section_renderer(section_renderer: Dict[str, Any]) -> List[str]:
    urls = []

    if "richShelfRenderer" not in section_renderer["richSectionRenderer"]["content"]:
        return urls

    for item_renderer in section_renderer["richSectionRenderer"]\
                                         ["content"]\
                                         ["richShelfRenderer"]\
                                         ["contents"]\
    :
        urls.append(parse_item_renderer(item_renderer))
    
    return urls

def get_default_seeds(yt_initial_data: Dict[str, Any]) -> List[str]:
    '''Get list of default channels from www.youtube.com and return it.'''
    urls = []

    try:
        for item in yt_initial_data["contents"]\
                                   ["twoColumnBrowseResultsRenderer"]\
                                   ["tabs"][0]\
                                   ["tabRenderer"]\
                                   ["content"]\
                                   ["richGridRenderer"]\
                                   ["contents"]\
        :
            if "richItemRenderer" in item:
                urls.append(full_url(parse_item_renderer(item)))
            elif "richSectionRenderer" in item:
                urls.extend([
                    full_url(u)
                    for u in parse_section_renderer(item)
                ])
    except Exception as e:
        logger.error(f'Unable to get channels due to exception: {e}')

    return list(set(urls))


def get_featured_channels(yt_initial_data: Dict[str, Any]) -> List[str]:
    '''Get list of featured channels for given channel.

    Args:
        channel_url: channel url.
    
    Returs: 
        List of featured channel urls.

    '''
    featured_channels = []

    try:
        featured_channels = [
            f'https://www.youtube.com{item["miniChannelRenderer"]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]}'
            for item in yt_initial_data["contents"]["twoColumnBrowseResultsRenderer"]["secondaryContents"]["browseSecondaryContentsRenderer"]["contents"][0]["verticalChannelSectionRenderer"]["items"]
        ]
    except Exception as e:
        logger.error(f'Unable to get featured channels due to exception {e}')
    
    return list(set(featured_channels))


def get_tags(yt_initial_data: Dict[str, Any]) -> List[str]:
    tags = []

    try:
        tags = yt_initial_data["microformat"]["microformatDataRenderer"]["tags"]
    except Exception as e:
        logger.error(f'Unable to get tags. Exception caught: {e}')

    return tags


def get_subscription_count(yt_initial_data: Dict[str, Any]) -> str:
    return yt_initial_data["header"]["c4TabbedHeaderRenderer"]["subscriberCountText"]["simpleText"]


def get_description(yt_initial_data: Dict[str, Any]) -> str:
    return yt_initial_data["metadata"]["channelMetadataRenderer"]["description"]


def detect_language(text: str) -> str:
    return langdetect.detect(text)


def remove_duplicate(filename):
    '''Open file with data and remove duplicate records.

    Args:
        filename: file's path to remove duplicates from.
    
    '''
    # dictionary with keys given by urls and values given by the rest of the information
    data = dict()
    # read data from file and write to the dictionary
    with open(filename, 'r', encoding='utf-8') as inp:
        for line in inp:
            data[line.split(';')[0]] = line
    # rewrite file with new data
    with open(filename, 'w', encoding='utf-8') as out:
        for key, val in data.items():
            out.write(val)


def combine(filename1, filename2, output) -> None:
    '''Combine two lists of channel urls.

    Args:
        filename1, filename2: file's paths to combine lists from.
        output: path of the resulting file.
    
    '''
    # final set of urls
    curr = set()
    # read urls from first file
    with open(filename1, 'r') as inp_1:
        for line in inp_1:
            curr.add(line)
    # read urls from second file
    with open(filename2, 'r') as inp_2:
        for line in inp_2:
            curr.add(line)
    # write urls to output file
    with open(output, 'w') as out:
        for elem in curr:
            out.write(elem)


def repl(s: str, *chars) -> str:
    '''Auxiliary funtion to replace given characters with whitespaces.

    Args:
        s: string to modify.
        chars: characters to be replaced.
    
    '''
    # create copy of the string
    ss = s[:]
    if chars:
        # replace all characters from 'chars' with whitespaces
        for c in chars:
            ss = ss.replace(c, ' ')
        return ss

    # default replacement
    return s.replace(';', ' ').replace('\n', ' ').replace('\r', ' ').replace(',', ' ')


def create_temp() -> None:
    '''Create folder 'Temp' with subfolders to store information
    collected by each process before it'll be combined into one file.
    '''
    # create Temp if doesn't exist
    if not os.path.exists('Temp'):
        os.makedirs('Temp')
    # create subfolders
    for subdir in ['ChannelsWithData', 'NewChannels', 'Skipped']:
        if not os.path.exists('Temp/' + subdir):
            os.makedirs('Temp/' + subdir)

if __name__ == "__main__":
    yt_initial_data = get_initial_data('https://www.youtube.com/c/javidx9')

    print('Featured channels:')
    print(json.dumps(get_featured_channels(yt_initial_data), indent=4))

    print('Tags:')
    print(json.dumps(get_tags(yt_initial_data), indent=4))

    print('Subscription count:')
    print(f'    {get_subscription_count(yt_initial_data)}')

    print('Language:')
    print(f'    {detect_language(get_description(yt_initial_data))}')
