import ssl
from urllib import request
from time import sleep
import json
from typing import List, Dict, Any, Tuple
from logging import getLogger

from bs4 import BeautifulSoup
import langdetect


logger = getLogger(__name__)


class YTChannel:
    """Class for YouTube channel content processing.
    """
    def __init__(self, channel_url):
        yt_initial_data, soup = YTChannel.get_initial_data(channel_url)

        self.yt_initial_data = yt_initial_data
        self.soup = soup

        self.url = channel_url
        self.description = self.get_description()
        self.lang = self.detect_language()
        self.subscription_count = self.get_subscription_count()
        self.tags = self.get_tags()
        self.featured_channels = self.get_featured_channels()
    
    def as_dict(self):
        return {
            self.url: {
                "tags": ','.join(self.tags),
                "lang": self.lang,
                "sub_count": self.subscription_count,
            }
        }

    @staticmethod
    def full_url(relative_url: str) -> str:
        return f'https://www.youtube.com{relative_url}'

    @staticmethod
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

    @staticmethod
    def get_initial_data(url: str) -> Tuple[Dict[str, Any], BeautifulSoup]:
        for _ in range(3):
            response = request.urlopen(url, context=ssl._create_unverified_context())
            if response.code == 200:
                break
            sleep(1)
        # if the page cannot be loaded raise an exception
        if response.code != 200:
            raise Exception(f'Cannot get page {url}: {response.code}')
        content = response.read()

        soup = BeautifulSoup(content, 'html.parser')

        body = soup.find("body")
        scripts = body.find_all("script")
        # find script with required data
        idx = -1
        for i, script in enumerate(scripts):
            if script.contents and 'window["ytInitialData"]' in script.decode_contents():
                idx = i
                break
        # raise an exception if the initial data is not found
        if idx < 0:
            raise Exception(f'Cannot find initial data for page {url}')

        initial_data_script = scripts[idx].decode_contents().strip()
        first_line = initial_data_script.split('\n')[0]
        rhs = first_line[first_line.find('=')+1:].strip()
        rhs = rhs[:-1] # remove ';' at the end
        
        return json.loads(rhs, encoding='utf-8'), soup

    @staticmethod
    def parse_section_renderer(section_renderer: Dict[str, Any]) -> List[str]:
        urls = []

        if "richShelfRenderer" not in section_renderer["richSectionRenderer"]["content"]:
            return urls

        for item_renderer in section_renderer["richSectionRenderer"]\
                                             ["content"]\
                                             ["richShelfRenderer"]\
                                             ["contents"]\
        :
            urls.append(YTChannel.parse_item_renderer(item_renderer))
        
        return urls

    @staticmethod
    def get_default_seeds() -> List[str]:
        '''Get list of default channels from www.youtube.com and return it.'''
        urls = []

        yt_initial_data, _ = YTChannel.get_initial_data('https://www.youtube.com')

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
                    urls.append(YTChannel.full_url(YTChannel.parse_item_renderer(item)))
                elif "richSectionRenderer" in item:
                    urls.extend([
                        YTChannel.full_url(u)
                        for u in YTChannel.parse_section_renderer(item)
                    ])
        except Exception as e:
            logger.error(f'Unable to get channels due to exception: {e}')

        return list(set(urls))

    def get_featured_channels(self) -> List[str]:
        '''Get list of featured channels for given channel.
        '''
        featured_channels = []

        try:
            featured_channels = [
                f'https://www.youtube.com{item["miniChannelRenderer"]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]}'
                for item in self.yt_initial_data["contents"]["twoColumnBrowseResultsRenderer"]["secondaryContents"]["browseSecondaryContentsRenderer"]["contents"][0]["verticalChannelSectionRenderer"]["items"]
            ]
        except Exception as e:
            logger.error(f'Unable to get featured channels due to exception {e}')
        
        return list(set(featured_channels))

    def get_tags(self) -> List[str]:
        tags = []

        try:
            tags = self.yt_initial_data["microformat"]["microformatDataRenderer"]["tags"]
        except Exception as e:
            logger.error(f'Unable to get tags. Exception caught: {e}')

        return tags

    def get_subscription_count(self) -> str:
        sub_count = ''
        
        try:
            sub_count = self.yt_initial_data["header"]["c4TabbedHeaderRenderer"]["subscriberCountText"]["simpleText"]
        except Exception as e:
            logger.error(f'Unable to get subscription count. Exception caught: {e}')
        
        return sub_count

    def get_description(self) -> str:
        description = ''

        try:
            description = self.yt_initial_data["metadata"]["channelMetadataRenderer"]["description"]
        except Exception as e:
            logger.error(f'Unable to get description. Exception caught: {e}')

        return description

    def detect_language(self) -> str:
        lang = '--'
        
        try:
            lang = langdetect.detect(self.get_description())
        except Exception as e:
            logger.error(f'Unable to detect language. Exception caught: {e}')

        return lang


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


def split_even(l: List[Any], n: int) -> List[List[Any]]:
    '''Split given list into given number of even parts.

    Args:
        l: list
        n: number of parts
    
    Returns:
        Lists of lists (chunks).

    '''
    ch_size = len(l) // n
    return [
        l[i * ch_size:min((i+1) * ch_size, len(l))]
        for i in range(n)
    ]


if __name__ == "__main__":
    # get default seeds
    default_seeds = YTChannel.get_default_seeds()
    print(json.dumps(default_seeds, indent=4))

    # get data for given channel
    channel = YTChannel('https://www.youtube.com/c/javidx9')

    print('Featured channels:')
    print(json.dumps(channel.featured_channels, indent=4))

    print('Tags:')
    print(json.dumps(channel.tags, indent=4))

    print('Subscription count:')
    print(f'    {channel.subscription_count}')

    print('Language:')
    print(f'    {channel.lang}')
