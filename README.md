# YouTubeCrawler

Crawler that creates a table of YouTube channels with its number of subscribers, list of tags and language. 

To run the crawler run the command
`python crawler.py`.

When it's ran for the very first time it gets a default set of channels from the youtube homepage. At each execution it finds channels similar to the channels in the initial list (*results/channels.txt*) and gets the data about them.
