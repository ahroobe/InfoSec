from bs4 import BeautifulSoup
import requests
import pandas
import urllib
import json
import sys


def str2level(levelform):
    #input -> LV.123 (string)
    #output -> 123 (int)
    check = 0
    if(levelform):
        wd = ""
        for ch in levelform:
            if check == 1:
                wd = wd+ch
            else:
                if ch =='.':
                    check = 1
        return int(wd)
    return 0

def str2int(numform):
    #input -> 1,357   or  2,345  form. (string)
    #output -> 1357 or 2345 form. (int)
    if(numform):
        return int(numform.replace(",","").replace("%",""))
    else:
        return 0

def str2wld(wldform):
    #input ->   ' 26W      31D    2L 'string
    #output -> (26,31,2) pair of int
    win=0
    draw=0
    lose=0
    wd=""
    wldform = wldform.replace(" ","").replace("\n","").replace("/","")
    if(wldform):
        for ch in wldform:
            if ch =='W':
                win = int(wd)
                wd = ""
            elif ch =='D':
                draw = int(wd)
                wd = ""
            elif ch =='L':
                lose = int(wd)
                wd = ""
                break
            else:
                wd = wd+ch
    else:
        return (0,0,0)
    return (win,lose,draw)

def str2kda(kdaform):
    #input '3.16:1' form
    #output 3.16 (float)
    kdaform = kdaform.replace(" ","")
    if(kdaform):
        wd =""
        for ch in kdaform:
            if(ch ==':'):
                return float(wd)
            else:
                wd = wd+ch
    return 0.0

def str2int2(hourform):
    #input: 9 hours or 9 Games form
    #output: 9 (int)
    hourform = hourform.replace(",","").split(' ')[0]
    if(hourform):
        return int(hourform)
    return 0

def str2sec(secform):
    #input : 29 secs or 2 mins 29 secs  -> 2mins29secs or 2secs or 2mins
    #output : 29 or 149 (int)
    check = 0
    sec = 0
    minute = 0
    secform = secform.replace(" ","").replace("\n","").replace(",","")
    
    if(secform):
        # There can be - (which means 0, never burned, or played.. else)
        if secform == '-':
            return 0
        wd = ""
        for ch in secform:
            if ch == 'm' or ch =='s':
                check = check+1
            if check == 0:
                wd = wd+ch
            elif ch == 'm':
                minute = int(wd)
                wd = ""
            elif check == 2 and ch != ' ' and ch != 's':
                wd = wd+ch
            elif ch == 'e':
                sec = int(wd)
                break

        return minute * 60 + sec
    return 0

def str2hour(hour):
    #2 Hour -> 2.0
    #2 Min -> 0.03
    if(hour):    
        hour = hour.split(' ')
        if len(hour) == 1:
            return int(hour[0][:-1])*1.0/60/60
        elif hour[1][0] == 'H':
            return int(hour[0])*1.0
        elif hour[1][0] == 'M':
            return int(hour[0])*1.0/60
        else:
            return 0
    else:
        0


def get_rank_page(page_num):

    """
    input: page number of ranking site. 1: 1~100 rankers , 2:101~200 rankers ...
    output: html source from ranking site.
    """
    
    url = 'http://overlog.gg/leaderboards/global/rank/' + `page_num`
    r = requests.get(url)
    html = r.text
   
    return html

def get_user_id(html):
    """
    from html source, get userid.
    
    """

    id_list = []
    soup = BeautifulSoup(html,"lxml")
    trs = soup.find_all("tr")
    
    # ex) <tr data-uid="225204161111254161080204">
    for tr in trs:
        if tr.get('data-uid'):
            id_list.append(tr.get('data-uid'))
    
    return id_list

def get_log_page(user_id):
    """
    personal log page
    """
  
    url = 'http://overlog.gg/detail/overview/' + user_id + '/'
    r = requests.get(url)
    html = r.text
    
    return html

def parsing_detail_data(html):
    """
    from personal log page, parse detail data
    id, level, score, rank, winning rate, KD, play time, most hero1, most hero2, most hero3
    
    most-hero1,2,3 -> each has other dict
    """

    soup = BeautifulSoup(html,"lxml")
    
    #PlayerInfo has id, level
    div = soup.find("div", "PlayerInfo")
    divs = div.find_all("div")
    level = divs[0].contents[0]
    name = divs[1].find("span").contents[0]
    
    #PlayerSummaryInfo has score, rank, win, lose, winning_rate, K,D, play time
    bigdiv = soup.find("div", "PlayerSummaryInfo")
    
    #in PlayerSummaryInfo, SkillRating has score ex 5,000 form
    div = bigdiv.find("div", "SkillRating")
    score = div.find("b").contents[0]
    
    #in PlayerSummaryInfo, PlayerSummaryStats has win, lose, winning rate (90%)
    # winning rate 90%form    win-> 51W  3D   2L  form
    div = bigdiv.find("div", "PlayerSummaryStats")
    winning_rate = div.find("span").contents[0]
    win = div.find("em").contents[0]

    #in PlayerSummaryInfo, first PlayerSummaryStat-LeftLine has K/D, second has play time
    divs = bigdiv.find_all("div", "PlayerSummaryStat-LeftLine")
    kda = divs[0].find("span").contents[0]
    play_time = divs[1].find("span").contents[0]
    game_num = divs[1].find("em").contents[0]

    #in ChampionStatsTable, Hero information list.
    table = soup.find("div", "ChampionStatsTable")
    trs = table.find_all("tr")

    h_hero = []
    h_win = []
    h_lose = []
    h_winning_rate = []
    h_kd = []
    h_avg_work_sec = []
    h_avg_burn_sec = []
    h_play_hour = []
    
    #most 1~3
    for i in range(1,4):
        if trs[i].get('class')[0] == 'NotPlayed':
            h_hero.append("Not_Played")
            h_win.append(0)
            h_lose.append(0)
            h_winning_rate.append(0)
            h_kd.append(0)
            h_avg_work_sec.append(0)
            h_avg_burn_sec.append(0)
            h_play_hour.append(0)
        else:
            tds = trs[i].find_all("td")
            h_hero.append(tds[0].contents[2].replace(" ","").replace("\n",""))
            h_win.append(int(tds[1].find("b").contents[0]))
            h_lose.append(int(tds[2].find("b").contents[0]))
            h_winning_rate.append(str2int(tds[3].contents[0]))
            h_kd.append(str2kda(tds[4].find("b").contents[0]))
            h_avg_work_sec.append(str2sec(tds[5].contents[0]))
            h_avg_burn_sec.append(str2sec(tds[6].find("b").contents[0]))
            h_play_hour.append(tds[7].contents[0])
            
            
    win, lose, draw = str2wld(win)
    inform = {
        
        'id' : name.replace(" ","").replace("\n",""),
        'level' : str2level(level),
        'score' : str2int(score),
        'win' : win,
        'lose' : lose,
        'draw' : draw,
        'winning_rate': str2int(winning_rate),
        'kd' : str2kda(kda),
        'play_time' : str2int2(play_time),
        'num_of_games' : str2int2(game_num),
        'most1champ' : {
            'name' : h_hero[0],
            'win' : h_win[0],
            'lose' : h_lose[0],
            'winning_rate' : h_winning_rate[0],
            'kd' : h_kd[0],
            'avg_burn_sec' : h_avg_burn_sec[0],
            'avg_work_sec' : h_avg_work_sec[0],
            'play_hour' : str2hour(h_play_hour[0])
        } ,      
        'most2champ' : {
            'name' : h_hero[1],
            'win' : h_win[1],
            'lose' : h_lose[1],
            'winning_rate' : h_winning_rate[1],
            'kd' : h_kd[1],
            'avg_burn_sec' : h_avg_burn_sec[1],
            'avg_work_sec' : h_avg_work_sec[1],
            'play_hour' : str2hour(h_play_hour[1])
        },
        'most3champ' : {
            'name' : h_hero[2],
            'win' : h_win[2],
            'lose' : h_lose[2],
            'winning_rate' : h_winning_rate[2],
            'kd' : h_kd[2],
            'avg_burn_sec' : h_avg_burn_sec[2],
            'avg_work_sec' : h_avg_work_sec[2],
            'play_hour' : str2hour(h_play_hour[2])
        }
    }
    return inform

def main():
    """
    args.spage -> start page
    args.epage -> finish page
    args.output -> output file name
    """
    try:
        spage = int(sys.argv[1])
        epage = int(sys.argv[2])
        filename = sys.argv[3]
    except ValueError:
        sys.exit("Wrong form. ex)python crawling.py 1 2 output.json")
    
    if spage < 1:
        sys.exit("Wrong start page number")
    elif epage+1 < spage:
        sys.exit("Wrong end page number")
    user_ids = []
    for i in range(spage,epage+1):
        user_ids = user_ids + get_user_id(get_rank_page(i))

    data = { user_id : parsing_detail_data(get_log_page(user_id))
        for user_id in user_ids}
    
    with open(filename, "w") as jsonFile:
        jsonFile.write(json.dumps(data))
    
main()
