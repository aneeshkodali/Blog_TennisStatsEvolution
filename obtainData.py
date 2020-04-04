from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests
from bs4 import BeautifulSoup


import pandas as pd
import unidecode
import re



def countPointResults(points, playerList):
    '''Counts number of times point ended certain way for player
    Args
        - points: points dataframe
        - playerList: list of players
    Returns dataframe
    '''

    # List of point results
    resultList = ['ace', 'double fault', 'forced error', 'service winner', 'unforced error', 'winner']


    # Initialize list (we will append to this later)
    pointOutcomeList = []

    # Iterate through players
    for player in playerList:
        
        # Create dictionary where keys are point results and values are number of points for that result

        pointOutcomeDict={}
        pointOutcomeDict['Player'] = player
        
        for result in resultList:
            if result in ['double fault', 'forced error', 'unforced error']:
                wORl='loser'
            else:
                wORl='winner'
        
            pointOutcomeDict[result.title()] =  len(filterPointDF(points, player, result=result, wORlCol=wORl))
        
        # Add dictionary to list
        pointOutcomeList.append(pointOutcomeDict)
    
    # Return dataframe
    pointOutcomeDF = pd.DataFrame.from_records(pointOutcomeList)
    return pointOutcomeDF


def countPointsWon(points, playerList):
    '''Counts number of times player won point
    Args
        - points: points dataframe
        - playerList: list of players
    Returns dataframe
    '''

    # List of point results
    resultPlayerWin = ['ace', 'forced error', 'service winner', 'winner']
    resultPlayerLose = ['double fault', 'unforced error']


    # Initialize list (we will append to this later)
    pointsWonList = []

    # Iterate through players
    for player in playerList:
        
        # Create dictionary where keys are point results and values are number of points won for that result

        pointsWonDict={}
        pointsWonDict['Player'] = player


        pointsWonDict['Points Player Won'] = 0
        for result in resultPlayerWin:
            pointsWonDict['Points Player Won'] += len(filterPointDF(points, player, result=result, wORlCol='winner'))
        
        pointsWonDict['Points Opponent Lost'] = 0
        for result in resultPlayerLose:
            pointsWonDict['Points Opponent Lost'] += len(filterPointDF(points, player, result=result, wORlCol='winner'))
        
                
        # Add dictionary to list
        pointsWonList.append(pointsWonDict)
    
    # Return dataframe
    pointsWonDF = pd.DataFrame.from_records(pointsWonList)
    return pointsWonDF


def filterPointDF(points, player, rallyLength=None, sORrCol=None, result=None, wORlCol=None, resultCol='result', rallyLengthCol='rallyLength'):
    '''Calculates metric for given arguments
    Args
        - player: player name
        - points: points dataframe
        - rallyLength: rally length
        - sORrCol: 'server', 'receiver'
        - result: result of interest (ace, double fault, winner, ...)
        - wORlCol: 'winner', 'loser'
    Returns dataframe
    '''

    # Filter out any weird points
    points = points.loc[~(points['result'].isin(['None', 'challenge was incorrect']))]
    
    # Filter to rally length
    if rallyLength is not None:
        points = points.loc[points[rallyLengthCol]==rallyLength]
    # Filter server or receiver column to player
    if sORrCol is not None:
        points = points.loc[points[sORrCol]==player]
    # Filter results column
    if result is not None:
        points = points.loc[points[resultCol]==result]
    # Filter winner or loser column to player
    if wORlCol is not None:
        points = points.loc[points[wORlCol]==player]
    return points
    

def makeRallyTreeDF(points, player, sORrCol=None, serverCol='server', receiverCol='receiver', rallyLengthCol='rallyLength', winnerCol='winner', loserCol='loser'):
    '''
    Args
        - points: points dataframe
        - player: player name
        - sORrCol: 'server', 'receiver'
    Returns dataframe: number of points won/lost by rally length
    '''

    # Initialize list (append to this later)
    pointList = []

    # Make list of unique rally lengths
    rallyLengthList = list(points[rallyLengthCol].unique())
    rallyLengthList.sort()

    # Iterate through each rallyLength
    for rallyLength in rallyLengthList:

        # Iterate through results (winner, loser)
        resultList = [winnerCol, loserCol]
        for result in resultList:
            # Filter dataframe
            if sORrCol is not None:
                pointsFiltered = filterPointDF(points, player, rallyLength=rallyLength, sORrCol=sORrCol, wORlCol=result)
            else:
                pointsFiltered = filterPointDF(points, player, rallyLength=rallyLength, wORlCol=result)

            # Create dictionary
            pointDict = {}
            pointDict['RallyLength']=rallyLength
            pointDict['Result'] = result.title()
            pointDict['Points'] = len(pointsFiltered)

            # Append to list
            pointList.append(pointDict)

    # Create dataframe
    pointDF = pd.DataFrame.from_records(pointList)
    return pointDF



def getMatchData(link, driver):
    '''
    Args:
        - link = match url

    Returns:
        - dictionary of match data
        - 
    '''

    # Initialize a dictionary (we will append to this later)
    variableDict = {}

    # Parse link to get match data from link
    # Links are of form: http://www.tennisabstract.com/charting/date-gender-tournament-round-player1-player2.html
    matchParsed = link.split('charting/')[1].split('-')

    variableDict['date'] = int(matchParsed[0])
    variableDict['gender'] = matchParsed[1]
    variableDict['tournament'] = matchParsed[2].replace('_',' ')
    variableDict['round'] = matchParsed[3]
    variableDict['player1'] = matchParsed[4].replace('_',' ')
    variableDict['player2'] = matchParsed[5].replace('.html','').replace('_',' ')
    variableDict['matchLink'] = link

    variableDict['surface'] = 'None'
    variableDict['result'] = 'None'
    variableDict['winner'] = 'None'
    variableDict['loser'] = 'None'
    variableDict['score'] = 'None'
    variableDict['numSets'] = 0


    # Go to link
    driver.get(link)

    # Get table
    try:
        soup = BeautifulSoup(driver.page_source, 'lxml')
    except:
        pass

    # Get surface
    try:
        variableDict['surface'] = soup.findAll('table')[3].text
        variableDict['surface'] = variableDict['surface'].split('matches on ')[1].split(',')[0]

    except:
        pass

    # Find result, winner, loser, score
    # If result found, result is of form: winner d. loser score
    try:
        result = soup.find('h2').nextSibling.nextSibling.text
        variableDict['result'] = result
        variableDict['winner'] = result.split(' d.')[0]
        variableDict['loser'] = variableDict['player2'] if variableDict['winner'] == variableDict['player1'] else variableDict['player1']
        variableDict['score'] = variableDict['result'].split(variableDict['loser']+' ')[-1]
        variableDict['numSets'] = len(variableDict['score'].split())

    except:
        pass
    
    # Return dataframe
    dataframe = pd.DataFrame.from_records([variableDict])
    return dataframe


def getPointData(matchLink, driver):
    '''
    Args:
        - match_link = link to match
    Returns:
        - list of dictionaries; each dictionary is a point
    '''

    # Go to link
    driver.get(matchLink)

    pointlogLink = driver.find_element_by_id('pointlog')
    pointlogLink.click()

    # Get table
    soup = BeautifulSoup(driver.page_source, 'lxml')
    table = soup.select('span#forecast table tbody')[0]

    # Each point is a 'tr' (after the 1st tr which was the header)
    pointTrList = table.findAll('tr')[1:]

    # Initialize a list. We will append to this list
    pointList = []

    # Iterate through the list of trs
    for i, pointTr in enumerate(pointTrList):

        # Initialize dictionary
        columnDict = {}
        columnDict['matchLink'] = matchLink
        columnDict['point'] = i+1
        columnDict['matchPoint'] = matchLink+'-'+str(i+1)
        columnDict['server']='None'
        columnDict['setScore'] = 'None'
        columnDict['gameScore'] = 'None'
        columnDict['pointScore'] = 'None'
        columnDict['description'] = 'None'
        columnDict['result'] = 'None'
        columnDict['rally'] = 'None'

        # Each column value is in a 'td' tag
        tdList = pointTr.findAll('td')

        
        # For each column, we will try to override the preexisting value of '' with the proper value if we can fnd a value
        if tdList[0].text.replace('\xa0',' ').strip():
            columnDict['server'] = tdList[0].text.replace('\xa0',' ').strip()
        if tdList[1].text:
            columnDict['setScore'] = unidecode.unidecode(tdList[1].text)
        if tdList[2].text:
            columnDict['gameScore'] = unidecode.unidecode(tdList[2].text)
        if tdList[3].text:
            columnDict['pointScore'] = unidecode.unidecode(tdList[3].text)
        if tdList[4].text:
            columnDict['description'] = tdList[4].text
        if tdList[4].find('b'):
            columnDict['result'] = tdList[4].find('b').text
        if tdList[4].text and tdList[4].find('b'):
            columnDict['rally'] = re.split(r',\s{1,2}'+columnDict['result'], columnDict['description'])[0]
        # side
        columnDict['side'] = getSide(columnDict['pointScore'])

        # rallyLength
        columnDict['rallyLength'] = columnDict['description'].count(';')

        # receiver
        player1 = matchLink.split('charting/')[1].split('-')[4].replace('_',' ')
        player2 = matchLink.split('charting/')[1].split('-')[5].replace('.html','').replace('_',' ')
        columnDict['receiver'] = 'None'
        if columnDict['server'] != 'None':
            if columnDict['server']==player1:
                columnDict['receiver'] = player2
            else:
                columnDict['receiver'] = player1

        # winner and loser
        loseList = ['unforced error', 'forced error', 'double fault']
        winList = ['winner', 'ace', 'service winner']
        columnDict['winner'] = 'None'
        columnDict['loser'] = 'None'
        if columnDict['result'] in winList:
            if columnDict['rallyLength']%2==0:
                columnDict['winner'] = columnDict['server']
            else:
                columnDict['winner'] = columnDict['receiver']
        elif columnDict['result'] in loseList:
            if columnDict['rallyLength']%2==0:
                columnDict['winner'] = columnDict['receiver']
            else:
                columnDict['winner'] = columnDict['server']
        if columnDict['winner'] != 'None':
            columnDict['loser'] = columnDict['receiver'] if columnDict['server']==columnDict['winner'] else columnDict['server']

        # Append
        pointList.append(columnDict)

    # Filter out 'end of game' rows (where there is no data)
    pointList = [x for x in pointList if (x['server']!='None')&(x['setScore']!='None')&(x['gameScore']!='None')&(x['pointScore']!='None')&(x['description']!='None')]

    # Return dataframe
    dataframe = pd.DataFrame.from_records(pointList)
    return dataframe


def getSide(pointScore):
	'''
	Args:
		- pointScore = score as a string 'score1-score2'
	Returns:
		- 'deuce' or 'ad'
	'''
	# Create dictionary to 'convert' scores
	pointDict = {'0':0, '15':1, '30':2, '40':3, '50': 4}
	# Replace 'AD' with number
	# Split score by '-'
	pointScoreSplit = pointScore.replace('AD', '50')
	# Get the 'int' version of the score if exists
	# Exception is if score is a tiebreak score
	# In this case, just return the integer of the score itself
	try:
		pointScoreSplit = [pointDict.get(x, int(x)) for x in pointScoreSplit.split('-')]
		# Add the scores and get side
		pointSum = sum(pointScoreSplit)
		side = 'deuce' if pointSum%2==0 else 'ad'
	except:
		side = 'None'

	return side



def getShotData(points):
    '''
    Args:
        - points: dataframe
    Returns:
        - dataframe
    '''
    shotList = []
    for p, point in points.iterrows():
        locationList = ['down the T', 'to body', 'wide', 'down the middle', 'crosscourt', 'inside-out', 'down the line', 'inside-in']
        splitPattern = '|'.join(locationList)

        # Create variables from point columns
        rallyLength = point['rallyLength']
        rally = point['rally']
        server = point['server']
        receiver = point['receiver']
        result = point['result']
        matchPoint = point['matchPoint']

        # Create lists of elements
        # These elements will be added to dictionaries, which will be added to a final list

        # Split out shots
        rallyList = [x.strip() for x in rally.split(';')]
        # Create list of alternating server and receiver
        shotByList = [server if i%2==0 else receiver for i in range(rallyLength+1)]

        rangeList = list(range(rallyLength+1))
        # Create list of 'None' + result
        resultList = [result if i==rallyLength else 'None' for i in range(rallyLength+1)]

        serveElement = rallyList[0]

        # Check if there is a 2nd serve
        if '.' in serveElement:
            firstServe = serveElement.split('. ')[0]
            secondServe = [serveElement.split('. ')[1]]
            rangeList = [0]*2 + list(range(1,rallyLength+1))
        else:
            firstServe = serveElement
            secondServe = []

        # Check if 1st serve is fault
        if ',' in firstServe:
            firstServeElement = firstServe.split(', ')[0]
            firstServeResult = [firstServe.split(', ')[1].strip()]
        else:
            firstServeElement = firstServe
            firstServeResult = []

        if rallyLength>0:
            restOfRally = rallyList[1:]
        else:
            restOfRally = []

        rallyList2 = [firstServeElement] + secondServe + restOfRally
        shotByList2 = [shotByList[i] for i in rangeList]
        resultList2 = firstServeResult + resultList


        for i, element in enumerate(rangeList):
            shotDict = {}
            shotDict['matchPoint'] = matchPoint
            shotDict['matchPointShotNumWithServe'] = matchPoint+'-'+str(i)
            shotDict['shotNumWithServe'] = i
            shotDict['shotNum'] = element
            shotDict['shotBy'] = shotByList2[i]
            try:
                shotDict['shot'] = re.split(splitPattern, rallyList2[i])[0].strip()
            except:
                shotDict['shot'] = 'None'
            try:
                shotDict['location'] = rallyList2[i][re.search(splitPattern, rallyList2[i]).start():]
            except:
                shotDict['location'] = 'None'
            shotDict['result'] = resultList2[i]
            
            shotList.append(shotDict)

    # Return dataframe
    dataframe = pd.DataFrame.from_records(shotList)
    return dataframe

