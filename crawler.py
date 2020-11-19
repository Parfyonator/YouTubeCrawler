import multiprocessing as mp
from time import time
import json
from typing import List, Dict, Any

from utils import YTChannel


def get_similar(channel_urls: List[str], data: Dict[str, Any], channel_list):
    for url in channel_urls:
        channel = YTChannel(url)
        data[url] = channel.as_dict()
        channel_list.extend(channel.featured_channels)


def split_even(l: List[str], n: int) -> List[List[str]]:
    ch_size = len(l) // n
    return [
        l[i * ch_size:min((i+1) * ch_size, len(l))]
        for i in range(n)
    ]


if __name__ == "__main__":
    n_proc = 8
    n_iterations = 4

    manager = mp.Manager()
    data = manager.dict()

    prev_channels = set()
    next_channels = set()
    seeds = YTChannel.get_default_seeds()
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
    print('Data:')
    print(json.dumps(data, indent=4))

    new_channels = list(prev_channels.union(next_channels))
    print('New channels:')
    print(json.dumps(new_channels, indent=4))
