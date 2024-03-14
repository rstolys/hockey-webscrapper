import requests
import time
from bs4 import BeautifulSoup

# Constants
BASE_URL = 'https://www.hockey-reference.com'

GAMES_TABLE_ID = 'games'
PLAYOFF_GAMES_TABLE_ID = 'games_playoffs'
SCORING_TABLE_ID = 'scoring'

GAME_FILE = "gamedata.csv"
SCORING_FILE = "scoringdata.csv"
PLAYOFF_GAME_FILE = "playoffgamedata.csv"
PLAYOFF_SCORING_FILE = "playoffscoringdata.csv"

# url: the relative url to extract the data from
# startingGameId: the game id to start at (can find the last game id in the gamedata.csv file, add 1 to this value)
# startDate: the date to start extracting data from (YYYY-MM-DD)
# endDate: the date to end extracting data from (YYYY-MM-DD)
# isPlayoffs: if the games are playoffs or not. This will extract data from different table and save it to a different file
# delayBtnRequestsInSecs: the number of seconds to wait between each request to the server (max is 20 requests per minute, if loading more than 20 games, set this to 3)
def extractGameData(url, startingGameId, startDate, endDate, isPlayoffs, delayBtnRequestsInSecs):
    _gameTableId = PLAYOFF_GAMES_TABLE_ID if isPlayoffs else GAMES_TABLE_ID
    _gameFile = PLAYOFF_GAME_FILE if isPlayoffs else GAME_FILE
    _scoringFile = PLAYOFF_SCORING_FILE if isPlayoffs else SCORING_FILE

    response = requests.get(BASE_URL + url)

    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find(lambda tag: tag.name=='table' and tag.has_attr('id') and tag['id']==_gameTableId) 
    rows = table.findAll(lambda tag: tag.name=='tr')
    
    gameFile = open(_gameFile, "a")
    scoringFile = open(_scoringFile, "a")

    # Table Format: Date, Visitor, G, Home, G, _, Att., LOG, Notes
    gameId = startingGameId
    for row in rows:
        cells = row.findChildren(['td', 'th'])

        # Print the header row if this is the top of the file
        if cells[0].get_text() == "Date" and startingGameId == 1:
            gameFile.write("GameId," + cells[0].get_text() + "," + cells[1].get_text() + "," + cells[2].get_text() + "," + cells[3].get_text() + "," + cells[4].get_text() + "," + cells[5].get_text() + "\n")
            scoringFile.write("GameId,Period,Min,Sec,Team,Situation\n")

        # If the game is a game we are reporting on then write it to the file
        if gameInDateRange(cells[0].get_text(), startDate, endDate) and cells[0].find('a') != None:
            gameFile.write(str(gameId) + "," + cells[0].get_text() + "," + cells[1].get_text() + "," + cells[2].get_text() + "," + cells[3].get_text() + "," + cells[4].get_text() + "," + cells[5].get_text() + "\n")
            extractSingleData(scoringFile, gameId, cells[0].find('a').get('href'))
            time.sleep(delayBtnRequestsInSecs)
            gameId += 1 # Increment the game is, only if we are reporting the game

    scoringFile.close()
    gameFile.close()


def extractSingleData(scoringFile, gameId, url):
    response = requests.get(BASE_URL + url)

    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find(lambda tag: tag.name=='table' and tag.has_attr('id') and tag['id']==SCORING_TABLE_ID) 
    rows = table.findAll(lambda tag: tag.name=='tr')

    firstPeriodTitle = "1st Period"
    secondPeriodTitle = "2nd Period"
    thirdPeriodTitle = "3rd Period"
    otPeriodTitle = "OT Period"
    shootoutPeriodTitle = "Shootout"

    # Data Format: TOG, Team, Situation, scorer, assists
    # Table Format: GameId, Period, TOG, Team, Situation
    currentPeriod = 0
    for row in rows:
        cells = row.findChildren(['td', 'th'])
        if firstPeriodTitle in str(row):
            currentPeriod = 1
            continue
        elif secondPeriodTitle in str(row):
            currentPeriod = 2
            continue
        elif thirdPeriodTitle in str(row):
            currentPeriod = 3
            continue
        elif otPeriodTitle in str(row):
            currentPeriod = 4
            continue
        elif shootoutPeriodTitle in str(row):
            currentPeriod = 5
            continue

        if currentPeriod == 5:
            continue
        scoringFile.write(str(gameId) + "," + str(currentPeriod) + "," + cells[0].get_text().split(":")[0] + "," + cells[0].get_text().split(":")[1] + "," + cells[1].get_text() + "," + cells[2].get_text().strip() + "\n")

# Determine if the game date is the specified date range we are fetching games for
def gameInDateRange(date, startDate, endDate):
    if date == "" or date == "Date":
        return False

    dateNumber = convertDateToNumber(date)
    startDateNumber = convertDateToNumber(startDate)
    endDateNumber = convertDateToNumber(endDate)

    if dateNumber >= startDateNumber and dateNumber <= endDateNumber:
        return True
    else:
        return False

# Will convert the date to a number which represents the number of days since 0 AD
# date is expected in the format of YYYY-MM-DD
# if date is empty then it will return -1
def convertDateToNumber(date):
    if date == "":
        return -1

    year = date.split("-")[0]
    month = date.split("-")[1]
    day = date.split("-")[2]

    return year * 365 + month * 30 + day
    

# TO RUN GAME DATE EXTRACTION
# Provide relative url for the league you want to extract data from
# Provide the starting game id (can be found in the gamedata.csv file, add 1 to this value). If this is the beginning, start at 1
# Provide the start date for games to extract in the format (YYYY-MM-DD) -- INCLUSIVE
# Provide the end date for games to extract in the format (YYYY-MM-DD) -- INCLUSIVE
# Provide a boolean if the games are playoffs or not (True means it is playoffs, False means it is not)
# Provide the delay between requests in seconds (max is 20 requests per minute, if loading more than 20 games, set this to 3)
extractGameData("/leagues/NHL_2023_games.html", 1, "2023-04-17", "2023-04-19", True, 0)


# EXAMPLE A
# -- Get all regular season games from in novmeber 2023 (part of 2023/2024 season)
#extractGameData("/leagues/NHL_2024_games.html", 1, "2023-10-01", "2023-10-30", False, 3)

# EXAMPLE B
# -- Get all playoff games from in april 2023
#extractGameData("/leagues/NHL_2023_games.html", 1, "2023-04-01", "2023-04-30", True, 0)