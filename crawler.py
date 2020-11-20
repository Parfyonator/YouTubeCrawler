import multiprocessing as mp
from time import time
import json
from typing import List, Dict, Any
from logging import getLogger

import pandas as pd

from utils import YTChannel, split_even


logger = getLogger(__name__)


def get_similar(channel_urls: List[str], data: Dict[str, Any], channel_list):
    for url in channel_urls:
        try:
            channel = YTChannel(url)
        except Exception as e:
            logger.error(e)
            return
        data.update(channel.as_dict())
        channel_list.extend(channel.featured_channels)


def save_data(data: Dict[str, Any]) -> None:
    random_key = list(data.keys())[0]
    df = pd.DataFrame(columns=['url', *data[random_key].keys()])

    for k, v in data.items():
        df = df.append({'url': k, **v}, ignore_index=True)

    df.to_csv(f'results/channels.csv', index=False, sep=';')


if __name__ == "__main__":
    n_proc = 12
    n_iterations = 4

    manager = mp.Manager()
    data = manager.dict()

    prev_channels = set()
    next_channels = set()

    seeds = YTChannel.get_default_seeds()
    print('Number of default seeds:', len(seeds))
    
    next_channels.update(seeds)

    for _ in range(n_iterations):
        channel_list = manager.list()
        chunks = split_even(list(next_channels), n_proc)

        processes = []
        for chunk in chunks:
            p = mp.Process(target=get_similar, args=(chunk, data, channel_list))
            processes.append(p)
            p.start()
        
        for p in processes:
            p.join()

        prev_channels.update(next_channels)
        next_channels = set(channel_list) - prev_channels

    data = dict(data)
    # save data
    save_data(data)
    
    print(f'Data {len(data)}:')
    print(json.dumps(data, indent=4))

    new_channels = list(prev_channels.union(next_channels))
    print(f'New channels {len(new_channels)}:')
    print(json.dumps(new_channels, indent=4))
