from selenium import webdriver 
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import csv
import pymongo as pm
import time

#establishing client-db link

myclient = pm.MongoClient("mongodb://localhost:27017/")
mydb = myclient["LinkedIn_repo"] #LinkedIn_repo is the database
mycol = mydb["profiles"] #profiles is the collection

#Setting up login details to linkedIn and a chromedriver to launch chrome

email = ''
pwd = ''
chrome_driver = ''
link = '' #This is the link we want to scrape
with open('Config.txt','r') as file:
    lines = file.readlines()
    email = lines[0].split()[1].strip()
    pwd = lines[1].split()[1].strip()
    chrome_driver = lines[2].split()[1].strip()
    link = lines[3].split()[1].strip()
file.close()

browser=webdriver.Chrome(chrome_driver)
browser.get('https://www.linkedin.com')
time.sleep(1)
browser.find_element_by_xpath('/html/body/nav/section[2]/form/div[1]/div[1]/input').send_keys(email)
time.sleep(1)
browser.find_element_by_xpath('/html/body/nav/section[2]/form/div[1]/div[2]/input').send_keys(pwd)
time.sleep(1)
browser.find_element_by_xpath('/html/body/nav/section[2]/form/div[2]/button').click()
time.sleep(1)
browser.get(link)
time.sleep(1)

#Function to get the comments from a LinkedIn post
def get_comments():
    try:
        browser.find_element_by_xpath("//button[contains(@class,'button comments-comments-list__show-previous-button t-12 t-black t-normal hoverable-link-text')]")
    except NoSuchElementException:
        return False
    return True

#Function to examine an element in source code
def check_element(element):
    try:
        browser.find_element_by_xpath(element)
    except NoSuchElementException:
        return False
    return True

#Web-Scrapping logic
link_list = set()

while get_comments():
    comments = browser.find_elements_by_xpath("//a[contains(@class,'comments-post-meta__profile-link t-16 t-black t-bold tap-target ember-view')]")
    for comment in comments:
        link = comment.get_attribute('href')
        if not (link in link_list):
            link_list.add(link)
            current_tab = browser.current_window_handle
            script = 'window.open("{}");'.format(link)
            browser.execute_script(script)
            new_tab = [tab for tab in browser.window_handles if tab != current_tab][0]
            browser.switch_to.window(new_tab)
            time.sleep(3)
            name = browser.find_element_by_xpath("//li[contains(@class,'inline t-24 t-black t-normal break-words')]").text
            location = browser.find_element_by_xpath("//li[contains(@class,'t-16 t-black t-normal inline-block')]").text
            exp = browser.find_elements_by_xpath("//span[contains(@class,'text-align-left ml2 t-14 t-black t-bold full-width lt-line-clamp lt-line-clamp--multi-line ember-view')]")
            if len(exp) == 1:
                if(exp[0].text.find('University') >= 0 or exp[0].text.find('Institute') or exp[0].text.find('College') >= 0):
                    university = exp[0].text
                    company = 'N/A'
                else:
                    university = 'N/A'
                    company = exp[0].text
            else:
                company = exp[0].text
                university = exp[1].text
            if company == university:
                company = 'N/A'
            exp_element = '//*[@id="experience-section"]/ul'
            SCROLL_PAUSE_TIME = 1
            last_height = browser.execute_script("return document.body.scrollHeight")
            flag = 0
            while not check_element(exp_element):
                html = browser.find_element_by_tag_name('html')
                html.send_keys(Keys.PAGE_DOWN)
                time.sleep(SCROLL_PAUSE_TIME)
                new_height = browser.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    flag = 1
                    break
                last_height = new_height
            if flag == 0:
                exp_elements = browser.find_element_by_xpath('//*[@id="experience-section"]/ul')
                exp_elements = exp_elements.find_elements_by_tag_name('li')
                experiences = []
                flag = 0
                for exp in exp_elements:
                    for i in range(4):
                        exp = exp.find_elements_by_xpath(".//*")[0]
                        if i == 3 and exp.get_attribute('class') == 'pv-entity__company-details':
                            flag = 1
                            break
                    if flag == 1:
                        break
                    exp = exp.find_elements_by_xpath(".//*")[3]
                    experiences.append(exp.text)
                if flag == 1:
                    exp_elements = browser.find_element_by_xpath("//ul[contains(@class,'pv-entity__position-group mt2')]")
                    exp_elements = exp_elements.find_elements_by_tag_name('li')
                    for exp in exp_elements:
                        experiences.append(exp.find_elements_by_xpath(".//*")[9].text)
                profile = {}
                profile['Name'] = name
                profile['Location'] = location
                profile['Profile Link'] = link
                profile['Company'] = company
                profile['University'] = university
                profile['Experiences'] = experiences
                x = mycol.insert_one(profile)
            browser.close()
            browser.implicitly_wait(10)
            browser.switch_to_window(current_tab)

    browser.find_element_by_xpath("//button[contains(@class,'button comments-comments-list__show-previous-button t-12 t-black t-normal hoverable-link-text')]").click()
    time.sleep(2)

    university_name = input("Enter the University you want profiles from: ")
    find_uni = mycol.find({'University': {'$eq': university_name}})
    for entries in find_uni:
        print(entries)
