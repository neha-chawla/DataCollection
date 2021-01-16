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
import json
import nltk
from nltk.tokenize import word_tokenize
import spacy
import spacy.lang.en
from spacy.lang.en import English

def popLinks(url):
    ''' Returns all links to questions from a search result page. '''

    #Get request from current URL
    linkRequest = requests.get(url)

    #Get HTML from URL
    htmlDoc = linkRequest.text

    #HTML parser
    soup = BeautifulSoup(htmlDoc, 'lxml')

    #Collection of links on the page
    links = []

    #Parse HTML to find all hyperlinks
    groupedLinks = soup.find(class_="flush-left js-search-results")
    quesHyperlinks = groupedLinks.find_all(class_="question-hyperlink")

    #Add full stackoverflow link to list of all links
    n=0
    for link in quesHyperlinks:
        links.append("http://stackoverflow.com" + (link.get('href')))
        n+=1
    print(n)
    #Parsed links may be ads, social media links etc and not questions!!
    #Parse through and only add links that are questions!!
    questionLinks = [k for k in links if k and 'questions' in k]
    return questionLinks

def getText(url, rmDigits = False, rmPunct = False, pause = False, sleepMax = 5):
    ''' Parses HTML code and returns the text contained in the question box and
    the text contained in each answer box.
    '''
    print("Retrieving question URL: ", url)
    #Pause to try and act more human
    if pause:
        sleep(randint(1, sleepMax))


    #Get request from current URL
    linkRequest = requests.get(url)

    #Retrieve HTML from URL
    htmlDoc = linkRequest.text
    #Add Spaces between certain tags
    htmlDoc = htmlDoc.replace('<p>', '<p> ')
    htmlDoc = htmlDoc.replace('</p>', ' </p>')
    htmlDoc = htmlDoc.replace('</strong>', ' </strong>')
    htmlDoc = htmlDoc.replace('</h1>', ' </h1>')
    htmlDoc = htmlDoc.replace('</h2>', ' </h2>')
    htmlDoc = htmlDoc.replace('</h3>', ' </h3>')
    htmlDoc = htmlDoc.replace('</h4>', ' </h4>')
    htmlDoc = htmlDoc.replace('</h5>', ' </h5>')
    htmlDoc = htmlDoc.replace('</h6>', ' </h6>')

    #HTML parser to find text simpler
    soup = BeautifulSoup(htmlDoc, 'lxml')
    headerSoup = soup.find(id="question-header")
    header = headerSoup.find(class_='question-hyperlink').get_text()

    #Remove certain tags from HTML that we dont want in our data
    removals = soup.find_all('pre')
    for match in removals:
        match.decompose()

    rem = soup.find_all('a')
    for match in rem:
        match.decompose()

    rem = soup.find_all('aside')
    for match in rem:
        match.decompose()

    #Link may not have answers
    try:
        #Parse HTML to find block for the question
        questionSoup = soup.find(class_="question")
        #Parse block to retrieve just the body.
        question = questionSoup.find(class_="s-prose js-post-body").get_text()
        return(header, question)
    except:
        print(":(")
        return('', '', '')

def tokenizeString(string):
    ''' Returns a list of words tokenized from given string. '''

    #We just want text from the question links. So we have number and
    #punctuations to remove after we retrive text from html code
    digitList = "1234567890"
    punct_list = '!"$%\'()*+,;<>?@[\\]^`{}~'
    slashDash = '-/+_&|:.#='

    #Initialize
    tokener = string

    #Special case of <br> tag
    tokener = tokener.replace('&gt', 'greaterthan')
    tokener = tokener.replace('&lt', 'lessthan')

    #Remove punctuation
    #for punc in punct_list:
    #    tokener = tokener.replace(punc, '')

    for num in digitList:
        tokener = tokener.replace(num, '')

    for space in slashDash:
        tokener = tokener.replace(space, ' ')

    #Tokenize
    nlp = spacy.load("en", disable=["parser","ner"])
    tokener = tokener.replace('\n', ' ')

    words = [token.lemma_ for token in nlp(tokener) if not token.is_punct]
    #remove digits and other symbols except "@"--used to remove email
    words = [re.sub(r"[^A-Za-z@]", "", word) for word in words]
    #remove websites and email address
    words = [re.sub(r"\S+com", "", word) for word in words]
    words = [re.sub(r"\S+@\S+", "", word) for word in words]

    #remove empty spaces
    words = [word for word in words if word!=' ']

    #Removing stop words!
    with open('StopWords_GenericLong.txt', 'r') as f:
        x_gl = f.readlines()
    with open('StopWords_Names.txt', 'r') as f:
        x_n = f.readlines()
    with open('StopWords_DatesandNumbers.txt', 'r') as f:
        x_d = f.readlines()
    #import nltk stopwords
    stopwords = nltk.corpus.stopwords.words('english')
    #combine all stopwords
    [stopwords.append(x.rstrip()) for x in x_gl]
    [stopwords.append(x.rstrip()) for x in x_n]
    [stopwords.append(x.rstrip()) for x in x_d]
    #change all stopwords into lowercase
    stopwords_lower = [s.lower() for s in stopwords]
    words = [word.lower() for word in words if word.lower() not in stopwords_lower]
    #Remove any empty words
    words = list(filter(("").__ne__,words))
    return words

def csvLinkCheck(allQs):
    try:
        with open('links_scraped.csv') as csvFile:
            reader = csv.reader(csvFile, delimiter=',')
            pastLinks = []
            for row in reader:
                if row[1] == 'url':
                    continue
                else:
                    pastLinks.append(row[1])
        currentLinks = allQs
        for link in pastLinks:
            if link in currentLinks:
                currentLinks.remove(link)
        return currentLinks
    except:
        with open('links_scraped.csv', "w") as emp:
            pass
        return allQs

def main():
    '''
    Scrapes search results pages of stackoverflow.com and creates CSV containing
    question and answer pairs.
    '''
    tags = [
            '<div>', '<br> &nbsp; &lt; &gt; &amp;', '<a>',
            '<h1> <h2> <h3> <h4> <h5> <h6>', '<p>', '<ul>', '<ol>', '<li>',
            '<img>', '<svg>', 'Figma SVG Export', 'width height',
            'background-color', 'class', '.class.name', '.one.two', '*',
            '@import a font', 'color', 'font-style', 'font-size', 'font-weight',
            'font-family', 'text-align', 'list-style-type'
            ]
    group = [
            'Elements'#, 'Layout', 'Data', 'Events'
            ]
    #Initiate webdriver
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    #Path should be path to the chrome driver on computer
    driver = webdriver.Chrome(options=options, executable_path=r'/Users/dshirami/aaaaa/chromedriver')

    #User input of search result page
    tag = str(input('Enter searched tag: '))
    while tag not in tags:
        tag = str(input('Enter searched tag again: '))
    searchPage = input('Enter Search Page URL: ')

    while 'title' not in searchPage:
        searchPage = input('YOU DID NOT SEARCH WITH TITLE:[TAG] REENTER CORRECT URL: ')
    #Get every link on first search result page
    questionLinks = popLinks(url = searchPage)

    #List of all question links
    allQs = questionLinks

    print('Retrieving Links...')
    #While true because we don't know when the website will realize its a bot
    botCheck = True

    while botCheck:
        try:
            #Command to click to the next search result page
            js = 'document.querySelector("[rel=\'next\']").click();'
            #Click next page button
            sleep(2)
            driver.execute_script(js)
            sendurl = driver.current_url
            #Get every link on current page
            questionLinks = popLinks(url = sendurl)
            #Add links to list of all links
            allQs += questionLinks
            #Print retrieved quesiton links from current page
        except:
            break
    #Set to prevent repeated question links
    print('Retrieved', len(allQs) ,'total links!')
    allQs = list(set(allQs))

    allQs = csvLinkCheck(allQs)
    print('Retrieved', len(allQs) ,'unique links!')
    #Save links scraped to CSV a file
    links_df = pd.DataFrame({'url':allQs})
    links_df.to_csv('links_scraped.csv', mode = 'a', header=True, encoding= 'utf8')


    print('Retrieving Questions and Answers....')
    nltk.download('punkt')
    nltk.download('stopwords')

    data = []
    #Goto every link and retrieve question and all answers to that question
    for link in allQs:
        #Retrieve text from question link
        header, question = getText(link, pause = True)
        if header== '' or question=='':
            continue

        if 'Not duplicate disclaimer' in question:
            question = question[0:question.index('Not duplicate disclaimer')]
        new = {}
        new['title'] = tokenizeString(header)
        new['query'] = tokenizeString(question)
        new['label'] = tag
        data.append(new)

    try:
        with open('Full_Data_Set.txt') as myJSONFile:
            past = json.load(myJSONFile)
        past+=data
        #Saves every stack overflow question to 'Full_Data_Set.csv'
        with open('Full_Data_Set.txt', mode='w') as myJSONFile:
            #Write row to JSON file
            json.dump(past, myJSONFile)
        print('Successfully added to JSON')
    except:
        with open('Full_Data_Set.txt', mode='w') as myJSONFile:
            #Write row to JSON file
            json.dump(data, myJSONFile)
        print('Created new JSON')


if __name__ == '__main__':
    main()
