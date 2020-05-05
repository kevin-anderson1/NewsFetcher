#----------------------------------------------------------------------------------------------
# Imports

import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from datetime import datetime
import sys
from PyQt5.QtWidgets import QApplication, QTableView, QWidget, QInputDialog, QLabel, QDialog, QPushButton
from PyQt5.QtCore import QAbstractTableModel, Qt


def popup():
    global query
    query = ''
    message = '                    Enter Search Below\nPlease allow up to 30 seconds for results\n        to be returned in a new window'
    window = QApplication(sys.argv)
    text, ok = QInputDialog.getText(None, 'NewsFetcher', message)
    query = text.lower()
    if ok:
        main()

def main():

    #----------------------------------------------------------------------------------------------
    # Functions

    def date_extract(x):

        if x == None:
            pass
        else:
            return x[0]

    def query_func(x):
       
        global final_query
        final_query = query.split()
        final_query = '%20'.join(final_query)


    #----------------------------------------------------------------------------------------------
    # New York Times Articles (w/ explaination of steps)

    query_func(query)

    #NYT URL
    url = 'https://www.nytimes.com/search?dropmab=false&query='+ final_query + '&sort=newest'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Creation of NYT dataframe
    nyt_df = pd.DataFrame()

    # Finding all NYT article titles
    nyt_link = soup.find_all('a')

    # Grabbing only the 3 most recent articles
    nyt_link = nyt_link[6:9]

    # Converting article titles to strings for parsing    
    nyt_link_str = [str(link) for link in nyt_link]

    # Showing what news site the article comes from
    nyt_name = ['New York Times' for line in range(len(nyt_link_str))]


    nyt_df['News Site'] = nyt_name

    # Creating df column from article title, non-parsed
    nyt_df['Article Title'] = nyt_link_str

    # Using Regex to only extract the article title from the <h4> string
    nyt_df['Article Title'] = nyt_df['Article Title'].apply(lambda x: re.search(r'(?<=\>).+?(?=\<)', x)[0])
    nyt_df['Article Title'] = nyt_df['Article Title'].apply(lambda x: re.search(r'(?<=\>).+', x)[0])

    # using Regex to extract the links
    nyt_df['Article Link'] = nyt_link_str
    nyt_df['Article Link'] = nyt_df['Article Link'].apply(lambda x: re.search(r'(?<=\").+?(?=\")', x)[0])
    nyt_df['Article Link'] = 'nytimes.com' + nyt_df['Article Link']

    #using regex to extract the data and convert to Pandas datetime obejct
    nyt_df['Article Date'] = nyt_df['Article Link'].apply(lambda x: re.search(r'\d+/\d+/\d+', x))
    nyt_df['Article Date'] = nyt_df['Article Date'].apply(date_extract)
    nyt_df['Article Date'] = pd.to_datetime(nyt_df['Article Date'], errors='coerce', utc=True)


    #----------------------------------------------------------------------------------------------
    # YAHOO w/ CUSTOM QUERY


    url = 'https://news.search.yahoo.com/search?p=' + final_query + '&fr=uh3_news_vert_gs&fr2=p%3Anews%2Cm%3Asb'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    y_links = soup.find_all('a')

    y_links_str = []
    for link in y_links:
        if '16px' in str(link):
            y_links_str.append(str(link))

    y_links_str = y_links_str[0:10]

    y_titles = []
    for link in y_links_str:
        url = re.search(r'(?<=\").+?(?=\")', link)[0]
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        y_titles.append(soup.find_all('h1'))
        
    y_titles_str = [str(title) for title in y_titles]

    y_df = pd.DataFrame()
        
    y_name = ['Yahoo News' for item in range(len(y_titles_str))]

    y_df['News Site'] = y_name

    y_df['Article Title'] = y_titles_str
    y_df['Article Title'] = y_df['Article Title'].apply(lambda x: re.findall(r'(?<=\>).+?(?=\<)', x)[0])

    y_df['Article Link'] = y_links_str
    y_df['Article Link'] = y_df['Article Link'].apply(lambda x: re.search(r'(?<=\").+?(?=\")', x)[0])

    y_dates = []
    for link in y_links_str:
        url = re.search(r'(?<=\").+?(?=\")', link)[0]
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        y_dates.append(soup.find_all('time'))

    y_dates_str = []
    for item in y_dates:
        if item == None:
            y_dates_str.append(None)
        else:
            y_dates_str.append(str(item))

    y_df['Article Date'] = y_dates_str
    y_df['Article Date'] = y_df['Article Date'].apply(lambda x: re.search(r'(?<=>).+(?=<)',x))
    y_df['Article Date'] = y_df['Article Date'].apply(date_extract)
    y_df['Article Date'] = pd.to_datetime(y_df['Article Date'], errors='coerce', utc=True)
    y_df = y_df.sort_values('Article Date', ascending=False)[0:3].reset_index(drop=True)


    #----------------------------------------------------------------------------------------------
    # GOOGLE NEWS w/ Query option


    url = 'https://news.google.com/search?q=' + final_query + '%20when%3A7d&hl=en-US&gl=US&ceid=US%3Aen'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    g_titles = soup.find_all(['h3','h4'], class_='ipQwMb ekueJc gEATFF RD0gLb')[0:10]
    
    g_titles_str = [str(title) for title in g_titles]
        
    g_name = ['Google News' for title in g_titles_str]

    g_df = pd.DataFrame()
    g_df['News Site'] = g_name

    g_df['Article Title'] = g_titles_str
    g_df['Article Title'] = g_df['Article Title'].apply(lambda x: re.findall(r'(?<=\>).+?(?=\<)', x)[0])
    g_df['Article Title'] = g_df['Article Title'].apply(lambda x: re.search(r'(?<=\>).+', x)[0])

    g_links = []
    for h3 in g_titles:
        for a in h3:
            g_links.append(a['href'])

    g_df['Article Link'] = g_links
    g_df['Article Link'] = 'https://www.news.google.com' + g_df['Article Link']

    g_dates = soup.find_all('time', class_='WW6dff uQIVzc Sksgp')[0:10]
    
    #g_dates_final = []
    #for time in g_dates:
        #g_dates_final.append(time['datetime'])
    
    g_dates_final = [time['datetime'] for time in g_dates]

    g_df['Article Date'] = g_dates_final
    g_df['Article Date'] = g_df['Article Date'].apply(lambda x: x[0:10])
    g_df['Article Date'] = pd.to_datetime(g_df['Article Date'], errors='coerce', utc=True)

    #----------------------------------------------------------------------------------------------
    # Final DF Concatenation

    final_df = pd.concat([nyt_df, y_df, g_df]).reset_index(drop=True)
    final_df = final_df.sort_values('Article Date', ascending=False).reset_index(drop=True)
    final_df['Article Date'] = final_df['Article Date'].apply(lambda x: x.strftime('%m-%d-%Y'))


    #----------------------------------------------------------------------------------------------
    # Pop-up Window Output

    class PandasModel(QAbstractTableModel):

        def __init__(self, data):
            QAbstractTableModel.__init__(self)
            self._data = data
            
        def rowCount(self, parent=None):
            return self._data.shape[0]

        def columnCount(self, parent=None):
            return self._data.shape[1]

        def data(self, index, role=Qt.DisplayRole):
            if index.isValid():
                if role == Qt.DisplayRole:
                    return str(self._data.iloc[index.row(), index.column()])
            else:
                return None

        def headerData(self, col, orientation, role):
            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return self._data.columns[col]
            else:
                return None

    app = QApplication(sys.argv)
    model = PandasModel(final_df)
    view = QTableView()
    view.setModel(model)
    view.resizeColumnToContents(0)
    view.resizeColumnToContents(1)
    view.resizeColumnToContents(3)
    view.resize(1200, 1600)
    view.show()
    app.exec_()

if __name__ == '__main__':
    popup()
