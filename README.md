# csgo-price-tracker
A simple script to track the value of your steam inventory from an appropriate csv file.

usage: Fetch.py [-h] [--textfile TEXTFILE] [-v] [-b] [-l] [-i]
                [--maxrows MAXROWS] [--wait WAIT]

Scrapes steam for sticker prices and pregenerated assets

optional arguments:
  -h, --help           show this help message and exit
  --textfile TEXTFILE  Textfile from which assets are accumulated
  -v                   Verbose
  -b                   Build Library of IDs from list of paths
  -l                   Use Links to scrape for ID
  -i                   Use ID Library to get prices
  --maxrows MAXROWS    Maximum amount of rows in csv
  --wait WAIT          Waiting time between requests
