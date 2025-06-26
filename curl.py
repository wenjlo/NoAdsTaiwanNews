import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

ETtoday_url = "https://www.ettoday.net/news/focus/社會/"  #財經新聞
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


browser = webdriver.Chrome(service=service, options=options)
#browser = webdriver.Chrome()
browser.get(ETtoday_url)  # 打開瀏覽器並連到東森新聞雲網頁

SCROLL_PAUSE_TIME = 1.5
# Press the green button in the gutter to run the script.
last_height = browser.execute_script("return document.body.scrollHeight;")
def news_parser(browser):
    history = pd.read_csv("./data/log.csv")
    html = browser.page_source
    soup = BeautifulSoup(html,"lxml")
    all_news = soup.find("div", attrs={'class': 'block block_1 infinite_scroll'})
    news_block = all_news.find_all('div', attrs={'class': 'piece clearfix'})
    for n in news_block:
        news_body = n.find('h3')
        externalLink = news_body.a["href"]
        if externalLink not in history['news_url']:
            history = pd.concat([pd.DataFrame([[datetime.datetime.now(),externalLink]],columns=history.columns),history],ignore_index=True)
    history.to_csv('./data/log.csv',index=False)



while True:
    '''
    Your code here

    提示：可參考以下的Stack Overflow:
    https://stackoverflow.com/questions/48850974/selenium-scroll-to-end-of-page-indynamically-loading-webpage/48851166
    '''
    # Scroll down to the bottom.
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    news_parser(browser)

    # Wait to load the page.
    time.sleep(SCROLL_PAUSE_TIME)

    # Calculate new scroll height and compare with last scroll height.
    new_height = browser.execute_script("return document.body.scrollHeight")

    if new_height == last_height:
        print("E")
        break

    last_height = new_height
    print(".", end="")



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
# 爬取網頁內容，解析後萃取新聞摘要
html = browser.page_source
soup = BeautifulSoup(html, "lxml")
all_news = soup.find("div", attrs={'class': 'block block_1 infinite_scroll'})

news_block = all_news.find_all('div', attrs={'class': 'piece clearfix'})
date_block = all_news.find_all('span', attrs={'class': 'date'})
for i, (date_item,news_item) in enumerate(zip(date_block,news_block)):
    if date_item.string.split('/')[0] == date_item.string:
        try:
            print("----------------------------------------------------------------------")
            print(date_item.string)
            news_body = news_item.find('h3')
            print("\n[%d] %s\n" % (i, news_body.a.string))

            #
            # 連到外部連結，擷取詳細新聞內容
            #
            externalLink = news_body.a["href"]
            print(f"source {externalLink}")
            img_url,content = getNewsDetailContent(externalLink)
            print(img_url,content)
        except:
            pass

data = pd.read_csv("./data/log.csv")
print(data)
browser.execute_script("window.close();")
