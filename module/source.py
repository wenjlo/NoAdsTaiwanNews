import time
from bs4 import BeautifulSoup
from selenium import webdriver
import re,emoji
from config import TOKEN,GROUP_ID
from fake_useragent import UserAgent
import requests
import pandas as pd
import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--disable-infobars")
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

SCROLL_PAUSE_TIME = 1.8

def user_agent():
    ua = UserAgent(os='windows', browsers='chrome')
    userAgent = ua.chrome
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    options.add_argument(f'user-agent={userAgent}')
    return options

def getNewsDetailContent(link_url):
    resp = requests.get(link_url)
    resp.encoding = 'utf-8'
    #print(resp.text)

    soup = BeautifulSoup(resp.text, 'lxml')
    news_content = soup.find("div", attrs={'class':'story'}).find_all("p")
    image_link = soup.find("div", attrs={'class':'story'}).find_all("img")[0]
    image_link = image_link['src']
    image_link = "https:" + image_link
    text = "\n"
    for p in news_content:
        """
        .string屬性說明：
        (1) 若當前tag節點底下沒有其他tag子節點，會直接抓取內容(返回"NavigableString")
        (2) 若當前tag節點底下只有唯一的一個tag子節點，也會直接抓取tag子節點的內容(返回"NavigableString")
        (3) 但若當前tag節點底下還有很多個tag子節點，.string就無法判斷，(返回"None")
        """
        if ((p.string) is not None):
            #print(p.string)
            text += p.string
            text += '\n'
    return image_link,text


def news_parser(browser):
    history = pd.read_csv("/app/data/log.csv")
    html = browser.page_source
    soup = BeautifulSoup(html,"lxml")
    all_news = soup.find("div", attrs={'class': 'block block_1 infinite_scroll'})
    news_block = all_news.find_all('div', attrs={'class': 'piece clearfix'})
    for n in news_block:
        news_body = n.find('h3')
        externalLink = news_body.a["href"]
        if externalLink not in history['news_url']:
            history = pd.concat([pd.DataFrame([[datetime.datetime.now(),externalLink]],columns=history.columns),history],ignore_index=True)
    history.to_csv('/app/data/log.csv',index=False)

class ettoday:
    def __init__(self):
        self.news_block = None
        self.date_block = None
        self.history_news = None
        self.url = "https://www.ettoday.net/news/focus/社會/"
        self.browser = browser = webdriver.Chrome(service=service, options=options)
        self.last_height = self.browser.execute_script("return document.body.scrollHeight;")
        self.browser.get(self.url)
        self.robot_emoji = emoji.emojize(":robot_face")
    def get_history_news(self):
        self.history_news = pd.read_csv('/app/data/log.csv')

    def insert_news_to_log(self,news_link):
        news_df = pd.read_csv('/app/data/log.csv')
        news_df = pd.concat([pd.DataFrame([[datetime.datetime.now(), news_link]], columns=news_df.columns), news_df],
                            ignore_index=True)
        news_df.to_csv('/app/data/log.csv', index=False)

    def news_cache(self):
        html = self.browser.page_source
        soup = BeautifulSoup(html, "lxml")
        all_news = soup.find("div", attrs={'class': 'block block_1 infinite_scroll'})
        news_block = all_news.find_all('div', attrs={'class': 'piece clearfix'})
        news_df = pd.DataFrame(columns=['time','news_url'])
        for n in news_block:
            news_body = n.find('h3')
            news_link = news_body.a["href"]
            news_df = pd.concat([pd.DataFrame([[datetime.datetime.now(), news_link]], columns=news_df.columns), news_df],
                            ignore_index=True)
        news_df.to_csv('/app/data/log.csv', index=False)

    def scroll(self):
        while True:
            '''
            Your code here

            提示：可參考以下的Stack Overflow: 
            https://stackoverflow.com/questions/48850974/selenium-scroll-to-end-of-page-indynamically-loading-webpage/48851166
            '''
            # Scroll down to the bottom.
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load the page.
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height.
            new_height = self.browser.execute_script("return document.body.scrollHeight")

            if new_height == self.last_height:
                print("E")
                break

            html = self.browser.page_source
            soup = BeautifulSoup(html, "lxml")
            all_news = soup.find("div", attrs={'class': 'block block_1 infinite_scroll'})
            date_block = all_news.find_all('span', attrs={'class': 'date'})
            regex = re.compile('(.+)小時前')
            time_ago = int(regex.search(date_block[-1].string).group(1))
            if time_ago > 6:
                break
            last_height = new_height
            print(".", end="")

    def html(self):
        html = self.browser.page_source
        soup = BeautifulSoup(html, "lxml")
        all_news = soup.find("div", attrs={'class': 'block block_1 infinite_scroll'})

        self.news_block = all_news.find_all('div', attrs={'class': 'piece clearfix'})
        self.date_block = all_news.find_all('span', attrs={'class': 'date'})

    def output(self,n_hours_ago,chain):
        self.get_history_news()
        regex = re.compile('(.+)小時前')
        for i, (date_item, news_item) in enumerate(zip(self.date_block, self.news_block)):
            try:
                time_ago = int(regex.search(date_item.string).group(1))
                # if date_item.string.split('/')[0] == date_item.string:
                if time_ago < n_hours_ago :


                    print("----------------------------------------------------------------------")
                    print(date_item.string)
                    news_body = news_item.find('h3')
                    print("\n[%d] %s\n" % (i, news_body.a.string))

                    #
                    # 連到外部連結，擷取詳細新聞內容
                    #
                    link = news_body.a["href"]
                    if link not in self.history_news['news_url']:
                        img_url, content = getNewsDetailContent(link)
                        question = (content)
                        answer = chain.invoke({"input_sentence":question})
                        message = f"""{img_url}
    
{self.robot_emoji}: {answer['text']}
來源: {link}"""
                        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={GROUP_ID}&text={message}"
                        print(requests.get(url).json())
                        self.insert_news_to_log(link)
            except:
                pass

