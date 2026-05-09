import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import dateutil.parser
from dateutil.tz import gettz

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import Variable

default_args = {
    'start_date': datetime(2022, 1, 1)
}

# ---------------------------------------------------------
# Python operators

def get_aripaev_articles(ti):
    teamshook = Variable.get("TeamsNewsHook")
    dates = []
    currentbenchmark = ''
    # List of excluded topics
    exclude_topics = ['Sisuturundus','Lisa','Saated','TOP','Leht']
    aripaev_benchmark = dateutil.parser.parse(Variable.get("aripaevBenchmark"))
    r = requests.get("http://feeds.feedburner.com/aripaev-rss")
    soup = BeautifulSoup(r.content, features='lxml-xml')
    articles = soup.findAll('item')

    for a in articles:
        pubDate = a.find('pubDate').text.strip()
        isodate = dateutil.parser.parse(pubDate)
        # Konverdime UTC aja Tallinna aega
        isodate_tallinn = isodate.astimezone(gettz("Europe/Tallinn"))
        category = a.find('category').text.strip()
        # Get only news where date is newer than current saved benchmark and category is not excluded
        if aripaev_benchmark < isodate and category not in exclude_topics:
            title = a.find('title').text.strip()
            description = a.find('description').text.strip()
            link = a.find('link').text.strip()
            #Preparing Discord message
            message = '[**{}**]({})   \n`{} | {} | Äripäev`   \n{}   \n\n'.format(title,link,isodate_tallinn.strftime("%H:%M %d.%m.%Y"),category, description)
            requests.post(teamshook, json={"content": message})
            #Forward to Discord sending task
            #ti.xcom_push(key='latest_news', value=discord_message)
            dates.append(isodate)
    try:
        currentbenchmark = max(dates)
    except ValueError:
        pass

    ct = currentbenchmark.strftime("%Y-%m-%d %H:%M:%S%z")
    Variable.set(key="aripaevBenchmark", value=ct)

def get_err_news(ti):
    teamshook = Variable.get("TeamsNewsHook")
    dates = []

    currentbenchmark=''
    # List of excluded topics
    exclude_topics = ['Arhitektuur', 'Teater', 'ETV uudised', 'Kunst', 'Raadiouudised', 'Inimesed','Galerii',
                      'Kultuurisaated','Viipekeelsed','Purjetamine','Tele/raadio','Film','Tennis','Iluuisutamine',
                      'ETV spordi lühiuudised','Arvamus','Ühiskond','Elu','Loodus','kultuur','Galeriid','TV10 Olümpiastarti',
                      'Keskkond','Muusika','ETV spordisaade','Kultuur']

    err_benchmark = dateutil.parser.parse(Variable.get("errBenchmark"))
    # print('Initial benchmark', currentbenchmark)

    r = requests.get("https://www.err.ee/rss")
    soup = BeautifulSoup(r.content, features='lxml-xml')
    articles = soup.findAll('item')

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
            message = '[**{}**]({})   \n`{} | {}`   \n{}   \n   \n\n\n'.format(title,link,isodate.strftime("%H:%M %d.%m.%Y"),category, description)
            requests.post(teamshook, json={"content": message})
            #ti.xcom_push(key='latest_news', value=message)
            dates.append(isodate)
    try:
        currentbenchmark = max(dates)
    except ValueError:
        pass

    ct = currentbenchmark.strftime("%Y-%m-%d %H:%M:%S%z")
    Variable.set(key="errBenchmark", value=ct)

def get_tartu_articles(ti):
    dates = []
    discord_message = ''
    currentbenchmark = ''
    # List of excluded topics
    tartu_benchmark = dateutil.parser.parse(Variable.get("tartunewsBenchmark"))
    r = requests.get("https://tartu.ee/et/rss")
    soup = BeautifulSoup(r.content, features='lxml-xml')
    articles = soup.findAll('item')

    for a in articles:
        pubDate = a.find('pubDate').text.strip()
        isodate = dateutil.parser.parse(pubDate)
        # Konverdime UTC aja Tallinna aega
        isodate_tallinn = isodate.astimezone(gettz("Europe/Tallinn"))
        # Get only news where date is newer than current saved benchmark and category is not excluded
        if tartu_benchmark < isodate:
            title = a.find('title').text.strip()
            description = a.find('description').text.strip()
            description = description.replace('<span class="field field--name-uid field--type-entity-reference field--label-hidden"><span>','').replace('</span></span>','')
            link = a.find('link').text.strip()
            #Preparing discord message
            discord_message = discord_message + '[**{}**]({})   \n`{} | Tartu`   \n{}   \n\n'.format(title,link,isodate_tallinn.strftime("%H:%M %d.%m.%Y"),description)
            #Forward to discord sending task
            ti.xcom_push(key='latest_news', value=discord_message)
            dates.append(isodate)
    try:
        currentbenchmark = max(dates)
    except ValueError:
        pass

    ct = currentbenchmark.strftime("%Y-%m-%d %H:%M:%S%z")
    Variable.set(key="tartunewsBenchmark", value=ct)

# Get the message from processing_forecast task.
def discord_post(ti):
    all_news = ''
    teamshook = Variable.get("TeamsNewsHook")
    message = ti.xcom_pull(key='latest_news', task_ids=['processing_aripaev_news','processing_tartu_news'])
    # Loop over the <list> of messages to compose concatenated discord message from both sources
    for news in message:
        all_news = all_news + (news or '') # in case news is None, add empty string
        requests.post(teamshook, json={"content": all_news})

# ----------------------------------------------------------------------------------------------------------------------

# Collect the news from 7AM to 23PM, every full hour'
with (DAG(dag_id='dwh_news_agency',
         schedule='0 7-23 * * *',
         default_args=default_args,
         catchup=False,
         tags=["dwhexample"])
      as dag):
    # 1st task: Process the response and get info
    processing_aripaev_news = PythonOperator(
        task_id='processing_aripaev_news',
        python_callable=get_aripaev_articles,
        do_xcom_push=True
    )
    # 2nd task: Process the response and get info
    processing_err_news = PythonOperator(
        task_id='processing_err_news',
        python_callable=get_err_news,
        do_xcom_push=True
    )
    # 3rd task: Process the response and get info
    processing_tartu_news = PythonOperator(
        task_id='processing_tartu_news',
        python_callable=get_tartu_articles,
        do_xcom_push=True
    )

    # 4th task: Post processed quote to discord
    discord_post_op = PythonOperator(
        task_id='discord_post_op',
        python_callable=discord_post,
        trigger_rule = 'one_success'
    )

    processing_tartu_news >> discord_post_op

    [processing_err_news,processing_aripaev_news]

