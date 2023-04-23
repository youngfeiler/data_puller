from datetime import datetime, timedelta

import pandas as pd

import json

import requests

score_dict = {
    "game_id": [],
    "team_1": [],
    "team_1_score": [],
    "team_2": [],
    "team_2_score": [],
    "winning_team": []
}

score_df = pd.DataFrame(score_dict)

DAYS_TO_RUN = 4

HOURS_TO_CHECK = [21, 22, 23, 24, 1, 2, 3, 4, 5, 6, 7]


def getOdds(user_sport, d):
    # An api key is emailed to you when you sign up to a plan
    # Get a free API key at https://api.the-odds-api.com/
    API_KEY = 'c7a1d7f7bae5aac1b32ee0f4cf3a1a22'

    SPORT = user_sport  # use the sport_key from the /sports endpoint below, or use 'upcoming' to see the next 8 games across all sports

    REGIONS = 'us,eu'  # uk | us | eu | au. Multiple can be specified if comma delimited

    MARKETS = 'h2h'  # h2h | spreads | totals. Multiple can be specified if comma delimited

    ODDS_FORMAT = 'american'  # decimal | american

    DATE_FORMAT = 'iso'  # iso | unix

    DATE = d

    BOOKMAKERS = "pinnacle, fanduel, williamhill_us, sugarhouse, betonlineag, betrivers, draftkings, betfair, barstool, betmgm, unibet, twinspires, gtbets, wynnbet, pointsbetus"

    test_df = pd.DataFrame()

    odds_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds-history/',
        params={
            'api_key': API_KEY,
            'regions': REGIONS,
            'markets': MARKETS,
            'oddsFormat': ODDS_FORMAT,
            'dateFormat': DATE_FORMAT,
            'date': DATE,
            'bookmakers': BOOKMAKERS
        }
    )

    if odds_response.status_code != 200:
        print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')

    else:
        odds_json = odds_response.json()

        # Check the usage quota
        print('Remaining requests', odds_response.headers['x-requests-remaining'])
        print('Used requests', odds_response.headers['x-requests-used'])

        df = pd.DataFrame.from_dict(odds_json)

        return df


def getScores(user_sport):
    # An api key is emailed to you when you sign up to a plan
    # Get a free API key at https://api.the-odds-api.com/
    API_KEY = 'c7a1d7f7bae5aac1b32ee0f4cf3a1a22'

    SPORT = user_sport  # use the sport_key from the /sports endpoint below, or use 'upcoming' to see the next 8 games across all sports

    DATE_FORMAT = 'iso'  # iso | unix

    odds_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{SPORT}/scores/',
        params={
            'api_key': API_KEY,
            'daysFrom': 3,
            'dateFormat': DATE_FORMAT,
        }
    )

    if odds_response.status_code != 200:
        print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')

    else:
        odds_json = odds_response.json()

        # Check the usage quota
        print('Remaining requests', odds_response.headers['x-requests-remaining'])
        print('Used requests', odds_response.headers['x-requests-used'])

        df = pd.DataFrame.from_dict(odds_json)

        df.to_json('/Users/stefanfeiler/Desktop/scores.json')

        df.to_csv('/Users/stefanfeiler/Desktop/scores.csv')

        return df


def parseOddsData():
    print("Reading and cleaning data.....")
    f = open('/Users/stefanfeiler/Desktop/DATA.json', 'r')
    print("------------")

    print(type(f))

    # Dict of each game
    file = json.load(f)
    print("Loading it back into the program....")
    return file['data'].items()


def calc_profit(num):
    if num > 0:
        return num
    else:
        return (100 / abs(num)) * 100


def calc_fair_odds(num1, num2):
    if num1 > 0 and num2 < 0:
        dividend = 100 / (100 + num1)
        divisor = ((abs(num2) / (abs(num2) + 100)) + dividend)
        return dividend / divisor

    elif num1 < 0 and num2 > 0:
        dividend = abs(num1) / (abs(num1) + 100)
        divisor = ((100 / (100 + num2)) + dividend)
        return dividend / divisor

    elif num1 > 0 and num2 > 0:
        dividend = 100 / (100 + num1)
        divisor = (dividend + (100 / 100 + num2))
        return dividend / divisor

    elif num1 < 0 and num2 < 0:
        dividend = abs(num1) / (abs(num1) + 100)
        divisor = (dividend + (abs(num2) / (abs(num2) + 100)))
        return dividend / divisor


def calc_ev(fair_win_prob, prof, odds_taken):
    if odds_taken > 0:
        stake = 100
    elif odds_taken < 0:
        stake = abs(odds_taken)

    return (fair_win_prob * prof) - ((1 - fair_win_prob) * stake)


def eachGameOddsData(games_data):
    final_df = pd.DataFrame()
    i = 0
    j = 0
    my_dict = {
        "game_id": [],
        "team_1": [],
        "best_1_book": [],
        "best_1_ml": [],
        "best_1_profit_if_win": 0,
        "pinnacle_1_ml": [],
        "fair_odds_1": 0,
        "book_1_ev": 0,
        "book_1_time": [],

        "team_2": [],
        "best_2_book": [],
        "best_2_ml": [],
        "best_2_profit_if_win": 0,
        "pinnacle_2_ml": [],
        "fair_odds_2": 0,
        "book_2_ev": 0,
        "book_2_time": [],
        "width": 0,
        'commence_time': []
    }
    df2 = pd.DataFrame(my_dict)
    final_df = pd.concat([final_df, df2], ignore_index=True)
    final_df.to_csv('/Users/stefanfeiler/Desktop/final_df.csv')

    for game in games_data:
        print(i)
        print("-------------------" + str(j))
        i += 1
        j += 1

        pinnacle_first_team_odds = 0
        pinnacle_second_team_odds = 0
        game_id = game[1]['id']
        commence_time = game[1]['commence_time']
        best_first_team_odds = -10000
        best_first_team_bookie = ""

        best_second_team_odds = -10000
        best_second_team_bookie = ""

        for bookie in game[1]['bookmakers']:
            if bookie['title'] == "Pinnacle":
                pinnacle_first_team_odds = bookie['markets'][0]['outcomes'][0]['price']
                pinnacle_second_team_odds = bookie['markets'][0]['outcomes'][1]['price']
            elif bookie['title'] != "Matchbook":
                first_team = bookie['markets'][0]['outcomes'][0]['name']
                first_team_ml_odds = bookie['markets'][0]['outcomes'][0]['price']
                second_team = bookie['markets'][0]['outcomes'][1]['name']
                second_team_ml_odds = bookie['markets'][0]['outcomes'][1]['price']
                if first_team_ml_odds > best_first_team_odds:
                    best_first_team_odds = first_team_ml_odds
                    best_first_team_bookie = bookie['title']
                    best_first_team_odds_time = bookie['last_update']
                if second_team_ml_odds > best_second_team_odds:
                    best_second_team_odds = second_team_ml_odds
                    best_second_team_bookie = bookie['title']
                    best_second_team_odds_time = bookie['last_update']
        if pinnacle_first_team_odds != 0:
            best_1_prof = calc_profit(best_first_team_odds)
            fair_odds_1 = calc_fair_odds(pinnacle_first_team_odds, pinnacle_second_team_odds)
            book_1_ev = calc_ev(fair_odds_1, best_1_prof, best_first_team_odds)
            best_2_prof = calc_profit(best_second_team_odds)
            fair_odds_2 = calc_fair_odds(pinnacle_second_team_odds, pinnacle_first_team_odds)
            book_2_ev = calc_ev(fair_odds_2, best_2_prof, best_second_team_odds)
            width = abs(best_first_team_odds - best_second_team_odds)
            my_dict = {
                "game_id": [game_id],
                "team_1": [first_team],
                "best_1_book": [best_first_team_bookie],
                "best_1_ml": [best_first_team_odds],
                "best_1_profit_if_win": best_1_prof,
                "pinnacle_1_ml": [pinnacle_first_team_odds],
                "fair_odds_1": fair_odds_1,
                "book_1_ev": book_1_ev,
                "book_1_time": [best_first_team_odds_time],

                "team_2": [second_team],
                "best_2_book": [best_second_team_bookie],
                "best_2_ml": [best_second_team_odds],
                "best_2_profit_if_win": best_2_prof,
                "pinnacle_2_ml": [pinnacle_second_team_odds],
                "fair_odds_2": fair_odds_2,
                "book_2_ev": book_2_ev,
                "book_2_time": [best_second_team_odds_time],
                "width": width,
                'commence_time': [commence_time]
            }
            df2 = pd.DataFrame(my_dict)
            final_df = pd.concat([final_df, df2], ignore_index=True)
            print(i)

            if i >= 1000:
                final_df.to_csv('/Users/stefanfeiler/Desktop/final_df.csv', mode='a')
                i = 0
                final_df = pd.DataFrame()


def parseScoreData():
    score_df = pd.DataFrame()

    f = open('/Users/stefanfeiler/Desktop/scores.json', 'r')
    # Dict of each game
    file = json.loads(f.read())

    ids_list = []

    df = pd.DataFrame(file)
    rslt_df = df[df['completed'] == True]

    counter = 0

    for each in rslt_df['id'].items():
        ids_list.append(each[1])
    for each in rslt_df['scores'].items():
        game_id = ids_list[counter]
        team_1 = each[1][0]['name']
        team_1_score = each[1][0]['score']
        team_2 = each[1][1]['name']
        team_2_score = each[1][1]['score']
        counter += 1
        if (team_1_score > team_2_score):
            winning_team = team_1
        elif (team_2_score > team_1_score):
            winning_team = team_2

        score_dict = {
            "game_id": [game_id],
            "team_1": [team_1],
            "team_1_score": [team_1_score],
            "team_2": [team_2],
            "team_2_score": [team_2_score],
            "winning_team": [winning_team]
        }

        df2 = pd.DataFrame(score_dict)

        score_df = pd.concat([score_df, df2], ignore_index=True)

    rslt_df.to_csv('/Users/stefanfeiler/Desktop/completed_only.csv')

    score_df.to_csv('/Users/stefanfeiler/Desktop/score_df.csv')

    return 'hi'


def calculateEV(first_team_pinnacle_odds, second_team_pinnacle_odds, first_team_b_odds, second_team_b_odds):
    if first_team_pinnacle_odds > second_team_pinnacle_odds:
        underdog = first_team_pinnacle_odds
        favorite = second_team_pinnacle_odds

        first_team_fair_percentage = (100 / (first_team_pinnacle_odds + 100)) * 100
        second_team_fair_percentage = (abs(second_team_pinnacle_odds) / (abs(second_team_pinnacle_odds) + 100)) * 100

        first_team_implied_prob = first_team_fair_percentage / (
                    first_team_fair_percentage + second_team_fair_percentage)
        second_team_implied_prob = second_team_fair_percentage / (
                    first_team_fair_percentage + second_team_fair_percentage)

        if first_team_b_odds < 0 and first_team_b_odds < second_team_b_odds:
            first_profit_if_win = abs(100 / first_team_b_odds) * 100
            second_profit_if_win = second_team_b_odds

        else:
            first_profit_if_win = first_team_b_odds
            second_profit_if_win = abs(100 / second_team_b_odds) * 100

        first_team_ev = (first_team_implied_prob * first_profit_if_win) - ((1 - first_team_implied_prob) * 100)
        second_team_ev = (second_team_implied_prob * second_profit_if_win) - ((1 - second_team_implied_prob) * 100)




    else:
        underdog = second_team_pinnacle_odds
        favorite = first_team_pinnacle_odds

        first_team_fair_percentage = (abs(first_team_pinnacle_odds) / (abs(first_team_pinnacle_odds) + 100)) * 100

        second_team_fair_percentage = (100 / (second_team_pinnacle_odds + 100)) * 100

        first_team_implied_prob = first_team_fair_percentage / (
                    first_team_fair_percentage + second_team_fair_percentage)
        second_team_implied_prob = second_team_fair_percentage / (
                    first_team_fair_percentage + second_team_fair_percentage)

        if first_team_b_odds < 0 and first_team_b_odds < second_team_b_odds:
            first_profit_if_win = (100 / abs(first_team_b_odds)) * 100
            second_profit_if_win = second_team_b_odds
        else:
            first_profit_if_win = first_team_b_odds
            second_profit_if_win = (100 / abs(second_team_b_odds)) * 100

        first_team_ev = (first_team_implied_prob * first_profit_if_win) - ((1 - first_team_implied_prob) * 100)
        second_team_ev = (second_team_implied_prob * second_profit_if_win) - ((1 - second_team_implied_prob) * 100)

    return [first_team_ev, first_profit_if_win, second_team_ev, second_profit_if_win]


def get_hour(fd):
    date_string = str(fd)
    time = date_string.split(" ")[1]
    hour = int(time.split(":")[0])

    return hour


def run():
    test_df = pd.DataFrame()
    scores_df = pd.DataFrame()
    #  sports_list = ['americanfootball_nfl', 'americanfootball_ncaaf', 'basketball_nba', 'icehockey_nhl']
    sports_list = ['basketball_nba']

    date_now = datetime.now().replace(microsecond=0)

    starting_date = date_now - timedelta(days=DAYS_TO_RUN)

    i = 0
    for sport in sports_list:
        date = starting_date
        while date < date_now:
            date = date + timedelta(minutes=2)
            i += 1
            hour = get_hour(date)
            if hour in HOURS_TO_CHECK:
                i += 1
                date_iso = date.isoformat() + "Z"
                df = getOdds(sport, date_iso)
                test_df = pd.concat([test_df, df], ignore_index=True)

            # if i >=5040:
            # date = date + timedelta(days=7)
            # print(date)
            # i=0

    test_df.to_json('/Users/stefanfeiler/Desktop/DATA.json')
    test_df = pd.DataFrame()
    print("here")

    var = parseOddsData()
    print("Working on compiling the best odds for each observation... this might take a while....")
    eachGameOddsData(var)
    print('Compiling scores... almost done!')

    for sport in sports_list:
        df = getScores(sport)
        scores_df = pd.concat([scores_df, df], ignore_index=True)
    scores_df.to_json('/Users/stefanfeiler/Desktop/scores.json')
    parseScoreData()
    print("Process complete")


if __name__ == '__main__':
    run()
