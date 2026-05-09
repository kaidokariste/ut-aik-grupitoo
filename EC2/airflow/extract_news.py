import requests
import psycopg2
from bs4 import BeautifulSoup
import os
from datetime import datetime
import dateutil.parser
from dateutil.tz import gettz
from dotenv import load_dotenv
load_dotenv()

def get_connection():
    """
    Get database connection handle
    """
    return psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" %
                            (os.getenv('DB_DATABASE'),
                             os.getenv('DB_USERNAME'),
                             os.getenv('DB_HOSTNAME'),
                             os.getenv('DB_PASSWORD')))

def db_query():
    query = "SELECT version()"
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result
    except psycopg2.Error as err:
        print(err)

def get_err_news():
    dates = []

    currentbenchmark=''
    # List of excluded topics
    exclude_topics = ['Arhitektuur', 'Teater', 'ETV uudised', 'Kunst', 'Raadiouudised', 'Inimesed','Galerii',
                      'Kultuurisaated','Viipekeelsed','Purjetamine','Tele/raadio','Film','Tennis','Iluuisutamine',
                      'ETV spordi lühiuudised','Arvamus','Ühiskond','Elu','Loodus','kultuur','Galeriid','TV10 Olümpiastarti',
                      'Keskkond','Muusika','ETV spordisaade','Kultuur']

    err_benchmark = dateutil.parser.parse('2021-12-19 10:11:00+0200')
    print('Initial benchmark', currentbenchmark)

    r = requests.get("https://www.err.ee/rss")
    soup = BeautifulSoup(r.content, features='lxml-xml')
    articles = soup.find_all('item')

    for a in articles:
        pubDate = a.find('pubDate').text
        isodate = dateutil.parser.parse(pubDate)
        category = a.find('category').text
        # Get only news where date is newer than current saved benchmark and category is not excluded
        if err_benchmark < isodate and category not in exclude_topics:
            title = a.find('title').text
            description = a.find('description').text
            link = a.find('link').text
            #Preparing discord message
            #message = '[**{}**]({})   \n`{} | {}`   \n{}   \n   \n\n\n'.format(title,link,isodate.strftime("%H:%M %d.%m.%Y"),category, description)
            #requests.post(teamshook, json={"content": message})
            #ti.xcom_push(key='latest_news', value=message)
            print(isodate, title, category, description, link)
            dates.append(isodate)
    try:
        currentbenchmark = max(dates)
    except ValueError:
        pass

    ct = currentbenchmark.strftime("%Y-%m-%d %H:%M:%S%z")
    print(ct)


if __name__ == "__main__":
    get_err_news()
    #print(db_query())