import urllib
from urllib import request
from bs4 import BeautifulSoup
import ssl, os, sys, re
import time
import multiprocessing as mp
from Nikita.web import getlang

from utils import *


def initialization():
    '''Read previously collected channels and set it as seeds for crawling processes.'''
    global processec_N        # number of processes
    global start_time         # start time
    global skips              # list of skipped channels
    global processes          # list of crawling processes
    global seeds              # list of lists channels to begin with
    global new_seeds          # list of lists new channels
    global curr_iter          # current iteration number
    global user_respond       # user respond from stin
    global keys               # list of column names in database table
    global logs               # list of each process logs
    global started_processes  # list of flags indicating which process is active

    keys = ['urls', 'subs', 'tags', 'lang']
    curr_iter = 0
    processec_N = 12
    start_time = time.time()
    processes = []
    init_seeds = [set() for i in range(processec_N)]
    logs = ['' for i in range(processec_N)]

    manager = mp.Manager()
    skips = manager.list()
    seeds = manager.list()
    started_processes = manager.list()
    new_seeds = manager.list()

    processec_N = int(input('Number of processes: '))
    [started_processes.append(1) for i in range(processec_N)]

    # user interface
    print('''Make a choice:
        1 - Update information about old channels
        2 - Get information about old and new channels
        3 - Exit''')
    while(True):
        user_respond = input()
        if user_respond == '1' or user_respond == '2':
            user_respond = int(user_respond)
            break
        elif user_respond == '3':
            sys.exit()
        else:
            print("Wrong input. Try again.")

    # create folders Backup and Results if they don't exist
    if not os.path.exists('Results'):
        os.makedirs('Results')
    if not os.path.exists('Backup'):
        os.makedirs('Backup')
    # create folder Temp to store intermediate information
    create_temp()
    # create empty file for database if doesn't exist
    open('Results/data.csv', 'a').close()
    # create file with default list of channels if it doesn't exist
    if not os.path.exists('Results/new.csv'):
        # get default channels
        channels = get_default_seeds()
        # write channe to file
        with open('Results/new.csv', 'w') as out:
            for channel in channels:
                out.write(channel + '\n')

    # backup current database
    with open('Backup/prev.csv', 'w') as prev:
        for line in open('Results/data.csv', 'r', encoding='utf-8'):
            prev.write(line)

    # with open('./Results/ChannelsWithData/' + str(curr_iter) + '.csv', 'r', encoding='utf-8') as inp:
    # read channels into list of lists (one list of channels for each process)
    with open('Results/data.csv', 'r', encoding='utf-8') as inp:
        counter = 0
        for line in inp:
            line = line.split(';')[0]
            if line.find('/user/') > -1:
                init_seeds[counter % processec_N].add(line.lower())
            elif line.find('/channel/') > -1:
                init_seeds[counter % processec_N].add(line)
            counter += 1

    if user_respond == 2:
        # with open('./Results/NewChannels/' + str(curr_iter) + '.csv', 'r') as inp:
        with open('./Results/new.csv', 'r') as inp:
            counter = 0
            for line in inp:
                if line.find('/user/') > -1:
                    init_seeds[counter % processec_N].add(line[:-1].lower())
                elif line.find('/channel/') > -1:
                    init_seeds[counter % processec_N].add(line[:-1])
                counter += 1

    # fill lists of new and skipped channels with empty sets
    for i in range(processec_N):
        seeds.append(init_seeds[i])
        new_seeds.append(set())
        skips.append(set())


def find_similar(num, seeds, new_seeds, skips, keys, logs, started_processes):
    '''Search for similar channels to the ones given by seeds.

        num: number of the process (it's id)

        seeds: the set in this list at 'num' position gives channels from
            which to start the search.

        new_seeds: the set in this list at 'num' position gives a container to
            store new channels.

        skips: the set in this list at 'num' position stores skipped channels.

        keys: list of the column names in the channels database.

        logs: list of logs for each process.

        started_processes: list of flags that indicates whether the process at
            position 'num' is active.
    '''
    # depth of the tree created by similar channels (simlar to similar to ...)
    N = 1
    # youtube url
    yt = 'https://www.youtube.com'

    '''---Dictionary with data---'''
    data = dict()
    for key in keys:
        data[key] = []

    '''Already checked and skipped channels'''
    checked_seeds = set()
    final_skips = set()

    '''Search for similar channels and data till N-th depth'''
    for i in range(N):
        users = []
        count = 1
        # search through new channels except from previous ones
        for url in seeds[num] - checked_seeds:
            # logs[num] = "Process " + str(num) + ": " + url
            # number of time the channels was tried to be accessed
            try_count = 0
            exception = True
            # try to open each channel 3 times
            while try_count < 3 and exception:
                try:
                    website = urllib.request.urlopen(url + '/about', context=ssl._create_unverified_context())
                    exception = False
                except:
                    try_count += 1
            # if the channel wasn't opened add it to the list of skipped channels
            if exception:
                final_skips.add(url)
                continue

            '''---Add verified channel to data list---'''
            data['urls'].append(url)

            '''---Parse channel for data---'''
            soup = BeautifulSoup(website, "html.parser")

            '-Get similar channels-'
            channels = soup.find_all("span", class_="yt-lockup clearfix yt-lockup-channel yt-lockup-mini")
            for channel in channels:
                users.append(yt + str(channel.find("div", class_='yt-lockup-thumbnail').find('a')['href']))

            '-Get number of subscribers-'
            try:
                data['subs'].append(''.join(soup.find("span", class_=\
                    "yt-subscription-button-subscriber-count-branded-horizontal subscribed yt-uix-tooltip")['title'].split()))
            except:
                data['subs'].append('-1')

            '-Get tags-'
            try:
                data['tags'].append(', '.join([repl(elem['content']) for elem in soup.find_all('meta', property="og:video:tag")]))
            except:
                data['tags'].append('')

            '-Get language-'
            #by default for now
            try:
                data['lang'].append(getlang(soup))
            except:
                data['lang'].append('none')

            '''---Print current state---'''
            print('Process ' + str(num) + ': ' + str(count))
            count += 1

        '''---Update containers---'''
        checked_seeds.update(seeds[num])

        '''---Temporarily save new seeds---'''
        with open('./Temp/ChannelsWithData/' + str(num) + '.csv', 'w', encoding='utf-8') as temp_out:
            length = len(data['urls'])
            for j in range(length):
                l = []
                for key in keys:
                    l.append(data[key][j])
                temp_out.write(';'.join(l) + '\n')

        n_seeds = set(users) - seeds[num]
        with open('./Temp/NewChannels/' + str(num) + '.csv', 'w') as temp_out:
            for elem in n_seeds:
                temp_out.write(elem + '\n')

        with open('./Temp/Skipped/' + str(num) + '.csv', 'w') as temp_out:
            for elem in final_skips:
                temp_out.write(elem + '\n')

        started_processes[num] = 0
        # new_seeds[num] = (set(users) - seeds[num])
        # seeds[num] = data
        # skips[num] = final_skips

        '''---Print process results---'''
        print('=======================================')
        print('Process ' + str(num) + ' finished:\n    ' + str(len(users)) + ' channels found')
        print('=======================================')


def summary():
    '''Save results and give brief summary of the work done: number new and skipped channels, time of execution.'''
    '''---Save logs---'''
    end_time = time.time()
    # with open('LogFile.txt', 'w') as logf:
    #     for lg in logs:
    #         logf.write(lg + '\n')
    #
    # global new_seeds
    # global skips
    #
    # final_seeds = set()
    # final_skips = set()
    #
    # for i in range(processec_N):
    #     final_seeds |= new_seeds[i]
    #     final_skips |= skips[i]
    #
    # for i in range(processec_N):
    #     final_seeds -= set(seeds[i]['urls'])

    '''---Save data---'''
    print('Saving channels with data')
    # with open('./Results/ChannelsWithData/' + str(curr_iter + 1) + '.csv', 'w', encoding='utf-8') as output:
    #     for i in range(processec_N):
    #         length = len(seeds[i]['urls'])
    #         for j in range(length):
    #             l = []
    #             for key in keys:
    #                 l.append(seeds[i][key][j])
    #             output.write(';'.join(l) + '\n')
    #
    #         print('Data of process ' + str(i) + ' is saved.')

    # with open('./Results/ChannelsWithData/' + str(curr_iter + 1) + '.csv', 'w', encoding='utf-8') as output:
    # collect temporary data in each Temp's subfolder into one file
    with open('./Results/data.csv', 'w', encoding='utf-8') as output:
        all_lines = []
        for i in range(processec_N):
            # path = './Temp/ChannelsWithData/' + str(i) + '.csv'
            with open('./Temp/ChannelsWithData/' + str(i) + '.csv', 'r', encoding='utf-8') as temp_in:
                for line in temp_in:
                    all_lines.append(line)
            # os.remove(path)

        for line in all_lines:
            output.write(line)

    '-Remove duplicates-'
    # remove_duplicate('./Results/ChannelsWithData/' + str(curr_iter + 1) + '.csv')
    remove_duplicate('./Results/data.csv')

    print('Saving new channels.')
    # with open('./Results/NewChannels/' + str(curr_iter + 1) + '.csv', 'w') as output:
    #     for elem in final_seeds:
    #         output.write(elem + '\n')

    # with open('./Results/NewChannels/' + str(curr_iter + 1) + '.csv', 'w') as output:
    with open('./Results/new.csv', 'w') as output:
        all_lines = set()
        for i in range(processec_N):
            path = './Temp/NewChannels/' + str(i) + '.csv'
            with open('./Temp/NewChannels/' + str(i) + '.csv', 'r') as temp_in:
                for line in temp_in:
                    all_lines.add(line)
            # os.remove(path)

        new_total = len(all_lines)
        for line in all_lines:
            output.write(line)

    print('Saving skipped channels.')
    # with open('./Results/Skipped/' + str(curr_iter) + '.csv', 'w') as skiped_urls:
    #     for elem in final_skips:
    #         skiped_urls.write(elem + '\n')

    # with open('./Results/Skipped/' + str(curr_iter) + '.csv', 'w') as output:
    with open('./Results/skipped.csv', 'w') as output:
        all_lines = set()
        for i in range(processec_N):
            path = './Temp/Skipped/' + str(i) + '.csv'
            with open(path, 'r') as temp_in:
                for line in temp_in:
                    all_lines.add(line)
            # os.remove(path)

        skip_total = len(all_lines)
        for line in all_lines:
            output.write(line)

    write_time = time.time()
    print("\n\nSummary:")
    print("    Time elapsed: " + str(end_time - start_time))
    print("    Data saving time: " + str(write_time - end_time))
    # skip_total = len(final_skips)
    print("    Total skiped: " + str(skip_total))
    # new_total = len(final_seeds)
    print("    New channels: " + str(new_total))

    '''---Change current iteration in code---'''
    # with open('crawler.py', 'r') as input:
    #     code = input.read()
    #
    # code = code.replace('\n    curr_iter = ' + str(curr_iter), '\n    curr_iter = ' + str(curr_iter + 1))
    #
    # with open('crawler.py', 'w') as output:
    #     output.write(code)


def start_processes():
    '''Start crawling processes.'''
    global processes
    global seeds
    global skips
    global started_processes

    while sum(started_processes) != 0:
        procs_to_start = [j for j in range(len(started_processes)) if started_processes[j] == 1]
        for i in procs_to_start:
            parser_proc = mp.Process(target=find_similar, args=(i, seeds, new_seeds, skips, keys, logs, started_processes))
            processes.append(parser_proc)
            parser_proc.start()
        for proc in processes:
            proc.join()


if __name__ == "__main__":
    initialization()

    start_processes()

    summary()
