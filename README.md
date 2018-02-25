# YouTubeCrawler
Crawler that creates a table of YouTube channels with its number of subscribers, list of tags and language. To run this crawler you'll need 2 additional libraries: *Selenium* and *BeautifulSoup*. To install them just type `pip install beautifulsoup4` and `pip install selenium` on your command line.
Type `python crawler.py` to run crawler. When it's ran for the very first time it gets a default set of channels from the youtube homepage. At each execution it finds channels similar to the channels in the initial list and gets the data about them. At each iteration the number of channels grows.

**TODO**
- Add functionality to the user interface.
- Enhance system of saving and storing information.
- Error handling.
