README for webscraperso.py

This program uses selenium to scrape stackoverflow questions to retrieve
questions and respective answers. The result is stored into a CSV file with
every row being a unique question to what was searched.

stackoverflow.com/robots.txt states that bots are not allowed to search.
However, selenium can read an already existing page that has passed the captcha
verification. The website also allows for selenium to go through pages as it is
not technically searching new things. This 'page flipping' is done until either
a captcha verification is needed again or the last page has been scraped.

Thus, downloading a chrome driver is needed.

Application of program:

Once downloaded and set up open chrome driver:
Google\ Chrome--remote-debugging-port=9222 --user-data-dir="~/ChromeProfile"
in terminal.

In the chrome window that appears search for desired tag on stack overflow.
Run the webscraperso.py program and it will prompt you to enter the current url.
After this, the program should parse through the search pages and retrieve all
question URLs and goto each URL to retrieve question and answers.
