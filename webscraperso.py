import requests
import sys
import pandas as pd
from time import sleep
from random import randint
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
import re
import csv

def popLinks(url):
    '''
    Parses through the HTML code of the given search results page (url parameter)
    Returns list of all stackoverflow question hyperlinks present within the HTML code
    '''
    # Get request from current URL
    linkRequest = requests.get(url)

    # Get HTML from URL
    htmlDoc = linkRequest.text

    # HTML parser
    soup = BeautifulSoup(htmlDoc, 'lxml')

    # Collection of links on the page
    links = []

    # Parse HTML to find all hyperlinks
    groupedLinks = soup.find(class_="flush-left js-search-results")
    quesHyperlinks = groupedLinks.find_all(class_="question-hyperlink")

    # Add full stackoverflow link to list of all links
    for link in quesHyperlinks:
        links.append("http://stackoverflow.com" + (link.get('href')))

    # Parsed links may be ads, social media links etc and not questions
    # Parse through and only add links that are questions
    questionLinks = [k for k in links if k and 'questions' in k]
    pattern = re.compile('questions/\d')
    questionLinks = filter(pattern.search, questionLinks)

    # Eliminate duplicate links
    questionLinks = list(set(questionLinks))
    return questionLinks


def getText(url, rmDigits = False, rmPunct = False, pause = False, sleepMax = 5):
    '''
    Parses through the HTML code of the given stackoverflow question link (url parameter)
    Returns the stackoverflow question being asked as well as each of the question's answers
    '''
    print("Retrieving question URL: ", url)

    # Pause to try to act more human
    if pause:
        sleep(randint(1, sleepMax))

    # Get request from current URL
    linkRequest = requests.get(url)

    # Retrieve HTML code from URL
    htmlDoc = linkRequest.text

    # HTML parser
    soup = BeautifulSoup(htmlDoc, 'lxml')

    # Link may not have answers
    try:
        # Parse HTML code to locate the question 
        questionSoup = soup.find(class_="question")
        # Parse question block to retrieve just the body text
        question = questionSoup.find(class_="s-prose js-post-body").get_text()
        # Parse HTML to locate the answers
        answerSoup = soup.find(id="answers")
        # Parse answer blocks to retrieve just the body text 
        answers = answerSoup.find_all(class_="s-prose js-post-body")
        return(question, answers)
    except:
        print(":(")
        return('', [])

def main():
    '''
    Scrapes through an opened stackoverflow search results page 
    Prints every question and answer from the search results page into dataset.csv
    '''
    # Initiate webdriver
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    # Path should be path to the chrome driver on computer
    driver = webdriver.Chrome(options=options, executable_path=r'/Users/neha/aaaaa/chromedriver')

    # User input of search result page
    searchPage = input('Enter Search Page URL: ')
    # Get every link on first search result page
    questionLinks = popLinks(url = searchPage)

    # List of all question links
    allQs = questionLinks

    print('Retrieving Links...')
    # While true because we don't know when the website will realize its a bot
    botCheck = True
    while botCheck:
        try:
            # Command to click to the next search result page
            js = 'document.querySelector("[rel=\'next\']").click();'
            # Click next page button
            driver.execute_script(js)
            sendurl = driver.current_url
            # Get every link on current page
            questionLinks = popLinks(url = sendurl)
            # Add links to list of all links
            allQs += questionLinks
            # Print retrieved question links from current page
            # print(questionLinks)
        except:
            break
    # Set to prevent repeated question links
    allQs = list(set(allQs))
    print('Retrieved', len(allQs) ,'links!')

    # Strings of numbers and punctuation marks to remove from questions and answers
    digitList = "1234567890"
    punct_list = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

    print('Retrieving Questions and Answers....')
    # Saves every stack overflow question to 'dataset.csv'
    with open('dataset.csv', mode='w') as myCSVFile:
        # CSV writer to write to CSV
        writer = csv.writer(myCSVFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Initiate columns
        writer.writerow(['questions', 'answers'])

        # Go to every link to retrieve the question and all answers to that question
        for link in allQs:
            # Retrieve text from question link
            question, answers = getText(link, pause = True)
            # First object in list is the question
            allAns = [question]
            if answers and question:
                # Check every answer and add it to the list following the
                # question
                for answer in answers:
                    # Customizable processing of text in answers
                    textAnswer = answer.get_text()
                    textAnswer = textAnswer.replace('\n',' ')
                    # Remove all numbers and punctuation from questions and answers
                    for char in punct_list:
                        textAnswer = textAnswer.replace(char, "")
                    for char in digitList:
                        textAnswer = textAnswer.replace(char, "")
                    allAns.append(textAnswer)
            # Write row to CSV file
            writer.writerow(allAns)

    # Save links scraped to a CSV file
    links_df = pd.DataFrame({'url':allQs})
    links_df.to_csv('links_scraped.csv', mode = 'a', header=True, encoding= 'utf8')

if __name__ == '__main__':
    main()