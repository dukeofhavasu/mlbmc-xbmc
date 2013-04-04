﻿import urllib
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import StorageServer
import json
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup
import time
from datetime import datetime, timedelta
from mlb_common import *


addon = xbmcaddon.Addon(id='plugin.video.mlbmc')
language = addon.getLocalizedString
addon = xbmcaddon.Addon('plugin.video.mlbmc')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
home = xbmc.translatePath(addon.getAddonInfo('path'))
icon = os.path.join(home, 'icon.png')
fanart = os.path.join(home, 'fanart.jpg')
next_icon = 'http://mlbmc-xbmc.googlecode.com/svn/icons/next.png'
fanart1 = 'http://mlbmc-xbmc.googlecode.com/svn/icons/fanart1.jpg'
fanart2 = 'http://mlbmc-xbmc.googlecode.com/svn/icons/fanart2.jpg'
debug = addon.getSetting('debug')
cache = StorageServer.StorageServer("mlbmc", 2)
show_scores = addon.getSetting('show_scores')
if debug == 'true':
    cache.dbg = True


def categories():
    thumb_path = 'http://mlbmc-xbmc.googlecode.com/svn/icons/'
    addDir(language(30000),'',3,thumb_path+'mlb.tv.png')
    addDir(language(30001),'',13,thumb_path+'condensed.png')
    addDir(language(30002),'',23,thumb_path+'fullcount.png')
    addDir(language(30003),'http://www.mlb.com/video/',18,thumb_path+'playlist.png')
    addPlaylist(language(30004),'http://mlb.mlb.com/video/play.jsp?tcid=mm_mlb_vid',12,thumb_path+'latestvid.png')
    addDir(language(30005),'add_playlist',4,thumb_path+'tvideo.png')
    addDir(language(30006),'',17,thumb_path+'highlights.png')
    addDir(language(30007),'',22,thumb_path+'podcast.png')
    addDir(language(30008),'http://gdx.mlb.com/components/game/mlb/'+dateStr.day[0]+'/media/highlights.xml',8,thumb_path+'realtime.png')
    addDir(language(30009),'',16,thumb_path+'search.png')


def mlb_playlist(url):
    soup = BeautifulSoup(getRequest(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
    try:
        thumb_string = soup.find('div', attrs={'id': "promoFeature"})['style']
        thumbnail = re.findall('background:url\((.+?)\)', thumb_string)[0]
    except:
        thumbnail = ''
    cats = soup.find('div', attrs={'id': "videoBrowseNav"})
    categories = cats('li', attrs={'class': 'category'})
    topics = cats('li', attrs={'class': 'topic'})
    topic_list = []
    for i in topics:
        name = i.a.string
        topic_id = i.a['rel']
        topic_list.append((name, topic_id))
    cates = {}
    for i in categories:
        title = i.a.string
        if title == 'Players':
            if 'c_id=' in url:
                team_id = url.split('c_id=')[1]
                topic_list.append((title, team_id))
        else:
            cates[title] = []
            items = i.ul('a')
            for item in items:
                if item['rel']:
                    cates[title].append((item.string, item['rel']))
    return {'thumbnail': thumbnail, 'playlist': topic_list, 'categories': cates}


def cache_playlist_categories():
    return mlb_playlist('http://www.mlb.com/video/')


def cache_current_playlist(url):
    p_dict = mlb_playlist(url)
    cache.set('current', repr(p_dict))
    return p_dict


def get_mlb_playlist(url, name=None):
    categories = None
    thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/playlist.png'
    if name is None:
        if url == 'http://www.mlb.com/video/':
            data = cache.cacheFunction(cache_playlist_categories)
            addDir('Teams', 'get_playlist', 4, thumb)
        else:
            data = cache_current_playlist(url)
        items = data['playlist']
        categories = data['categories']
        # thumb = data['thumbnail']
    else:
        if url == 'http://www.mlb.com/video/':
            data = cache.cacheFunction(cache_playlist_categories)
            items = data['categories'][name]
            # thumb = data['thumbnail']
        else:
            data = eval(cache.get('current'))
            items = data['categories'][name]
            # thumb = data['thumbnail']

    for title, item_id in items:
        mode = 1
        if title == 'Players':
            mode = 20
        addDir(title, item_id, mode, thumb)
    if categories:
        for i in categories.keys():
            addDir(i , url, 19, thumb)


def get_players(c_id):
    roster_url = ('http://www.mlb.com/lookup/json/named.roster_active_mlb.bam?'
                   'status=%27A%27&status=%27D15%27&file_code=%27'+c_id+'%27')
    data = json.loads(getRequest(roster_url))
    items = data['roster_active_mlb']['queryResults']['row']
    for i in items:
        url = ('http://www.mlb.com/ws/search/MediaSearchService?type=json&'
               'player_id=%s&start=0&src=vpp&sort=desc&sort_type=custom&'
               'hitsPerPage=60&hitsPerPage=60&src=vpp' %i['player_id'])
        addDir(i['name_first_last'], url, 1, 'http://mlbmc-xbmc.googlecode.com/svn/icons/playlist.png')


def gameCalender(game_type, start_date=None):
    base = 'http://mlb.mlb.com/gdcross/components/game/mlb/'
    if game_type == 'mlbtv':
        thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/mlb.tv.png'
        href = '/master_scoreboard.json'
        mode = 6
    else:
        thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/condensed.png'
        href = '/grid.json'
        mode = 14
    future = False
    if start_date is None:
        start_date = datetime.today()
        future = True
    older_dates = start_date - timedelta(days=10)
    future_dates = start_date + timedelta(days=10)
    for i in getDays(start_date):
        addGameDir(i[0],base+i[1]+href,mode,thumb)
    addDir(language(30015),older_dates.strftime("%B %d, %Y - %A"),15,thumb,game_type)
    if future:
        if game_type == 'mlbtv':
            addDir(language(30016),future_dates.strftime("%B %d, %Y - %A"),15,thumb,game_type)
        addDir(language(30017),'',11,thumb,game_type)


def getDays(start_date):
    pattern = "%B %d, %Y - %A"
    url_pattern = "year_%Y/month_%m/day_%d"
    one_day = timedelta(days=1)
    days = []
    for i in range(10):
        day = start_date-(one_day*i)
        days.append((day.strftime(pattern), day.strftime(url_pattern)))
    return days


def mlb_podcasts():
    thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/podcast.png'
    addDir(language(30020),'http://mlb.mlb.com/feed/podcast/c1261158.xml',10,thumb)
    addDir(language(30021),'http://mlb.mlb.com/feed/podcast/c1265860.xml',10,thumb)
    addDir(language(30022),'http://mlb.mlb.com/feed/podcast/c1508643.xml',10,thumb)
    addDir(language(30023),'http://mlb.mlb.com/feed/podcast/c1291376.xml',10,thumb)
    addDir(language(30024),'http://mlb.mlb.com/feed/podcast/c1266262.xml',10,thumb)
    addDir(language(30025),'http://mlb.mlb.com/feed/podcast/c17429946.xml',10,thumb)



def get_podcasts(url):
    soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
    items = soup('item')
    thumb = soup.find('itunes:image')['href']
    for i in items:
        title = i.title.string.replace('MLB.com','') #strange issue with the '.' in the xbmcgui.Listitem name??
        desc = i.description.string
        guid = i.guid.string
        # e_url = i.enclosure['url']  # same as guid
        pubdate = i.pubdate.string
        duration = i('itunes:duration')[0].string
        addLink(title,guid,duration,2,thumb,desc,True)


def getTeams(mode):
    for name, c_id in TeamCodes.values():
        if mode == 'get_playlist':
            addDir(name, 'http://www.mlb.com/video/index.jsp?c_id='+c_id, 18, icon)
        elif mode == 'add_playlist':
            addPlaylist(name, c_id, 5, 'http://mlbmc-xbmc.googlecode.com/svn/icons/tvideo.png')


def getRealtimeVideo(url):
    try:
        soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        videos = soup.findAll('media')
        for video in videos:
            name = video.headline.string
            vidId = video['id']
            url = vidId[-3]+'/'+vidId[-2]+'/'+vidId[-1]+'/'+vidId
            duration = video.duration.string
            thumb = video.thumb.string
            addLink(name,'http://mlb.mlb.com/gen/multimedia/detail/'+url+'.xml',duration,2,thumb)
    except:
        pass


def getTeamVideo(url):
    xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30036)+",5000,"+icon+")")
    url='http://mlb.mlb.com/gen/'+url+'/components/multimedia/topvideos.xml'
    soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
    videos = soup('item')
    playlist = xbmc.PlayList(1)
    playlist.clear()
    for video in videos:
        name = video('title')[0].string
        thumb = video('picture', attrs={'type' : "dam-raw-thumb"})[0]('url')[0].string
        if video('url', attrs={'speed' : "1200"}):
            url = video('url', attrs={'speed' : "1200"})[0].string
        elif video('url', attrs={'speed' : "1000"}):
            url = video('url', attrs={'speed' : "1000"})[0].string
        elif video('url', attrs={'speed' : "800"}):
            url = video('url', attrs={'speed' : "800"})[0].string
        duration = video('duration')[0].string
        desc = video('big_blurb')[0].string
        info = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
        playlist.add(url, info)
    play = xbmc.executebuiltin('playlist.playoffset(video,0)')


def playLatest(url):
    xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30036)+",5000,"+icon+")")
    headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
               'Referer' : 'http://mlb.mlb.com/video/play.jsp?cid=mlb'}
    soup = BeautifulSoup(getRequest(url,None,headers), convertEntities=BeautifulSoup.HTML_ENTITIES)
    videos = soup.find('div', attrs={'id' : "playlistWrap"})('li')
    playlist = xbmc.PlayList(1)
    playlist.clear()
    for video in videos:
        name = video('p')[0].string
        try:
            thumb = video('img')[0]['data-src']
        except:
            thumb = video('img')[0]['src']
        content = video('a')[0]['rel']
        url = content[-3]+'/'+content[-2]+'/'+content[-1]+'/'+content
        url = getVideoURL('http://mlb.mlb.com/gen/multimedia/detail/'+url+'.xml')
        info = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
        playlist.add(url, info)
    play = xbmc.executebuiltin('playlist.playoffset(video,0)')


def getVideos(url, page=False):
    if not page:
        xml_url = None
        search_url = None
        if not url.startswith('http://'):
            topic_url = 'http://www.mlb.com/gen/multimedia/topic/'+url+'.xml'
            soup = BeautifulStoneSoup(getRequest(topic_url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
            try:
                search_query = soup.search_query.string
                search_url = 'http://www.mlb.com/ws/search/MediaSearchService?&'+search_query+'&hitsPerPage='+soup.topic['maxitems']+'&src=vpp'
            except:
                pass
            try:
                xml_url = soup.video_index['src']
            except:
                pass

        if 'MediaSearchService' in url:
            search_url = url

        if search_url:
            data = json.loads(getRequest(search_url))
            addon_log('Search Data: %s' %data)
            if data.has_key('mediaContent'):
                total = data['end']
                if total > 20:
                    cache.set('current_playlist', repr(data))
                    items = get_playlist_page(0)
                else:
                    items = (data['mediaContent'], False)
        elif xml_url:
            return getVideoListXml(xml_url)
    else:
        items = get_playlist_page(page)

    for i in items[0]:
        name = i['blurb']
        duration = i['duration']
        item_url = i['url']
        try:
            thumb = i['thumbnails'][2]['src']
        except:
            thumb = i['thumbnails'][1]['src']
        addLink(name,item_url,duration,2,thumb)
    if items[1]:
        addDir(language(30034), str(page+1), 21, next_icon)


def get_playlist_page(page):
    data = eval(cache.get('current_playlist'))
    if data['end'] > (page*20)+20:
        end = (page*20)+20
        more = True
    else:
        end = data['end']
        more = False
    items = data['mediaContent'][page*20:end]
    return (items, more)


def setVideoURL(link, podcasts=False):
    if podcasts:
        url = link
    else:
        url = getVideoURL(link)
    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def getVideoURL(url):
    soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
    if addon.getSetting('use_hls') == 'true':
        if soup.find('url', attrs={'playback_scenario' : "HTTP_CLOUD_TABLET"}):
            url = soup.find('url', attrs={'playback_scenario' : "HTTP_CLOUD_TABLET"}).string
    elif soup.find('url', attrs={'playback_scenario' : "FLASH_1200K_640X360"}):
        url = soup.find('url', attrs={'playback_scenario' : "FLASH_1200K_640X360"}).string
    elif soup.find('url', attrs={'playback_scenario' : "FLASH_1000K_640X360"}):
        url = soup.find('url', attrs={'playback_scenario' : "FLASH_1000K_640X360"}).string
    elif soup.find('url', attrs={'playback_scenario' : "FLASH_600K_400X224"}):
        url = soup.find('url', attrs={'playback_scenario' : "FLASH_600K_400X224"}).string
    elif soup.find('url', attrs={'playback_scenario' : "MLB_FLASH_1000K_PROGDNLD"}):
        url = soup.find('url', attrs={'playback_scenario' : "MLB_FLASH_1000K_PROGDNLD"}).string
    elif soup.find('url', attrs={'playback_scenario' : "MLB_FLASH_800K_PROGDNLD"}):
        url = soup.find('url', attrs={'playback_scenario' : "MLB_FLASH_800K_PROGDNLD"}).string
    return url


def getCondensedGames(url):
    data = json.loads(getRequest(url))
    addon_log('CondensedGames Data: %s' %data)
    items = data['data']['games']['game']
    addon_log('item count: %s' %len(items))
    for i in items:
        try:
            if i['game_media']['newsroom']['media']['type'] == 'condensed_video':
                content = i['game_media']['newsroom']['media']['id']
            else:
                raise KeyError
        except KeyError:
            continue
        content_id = content[-3]+'/'+content[-2]+'/'+content[-1]+'/'+content
        url = 'http://mlb.mlb.com/gen/multimedia/detail/'+content_id+'.xml'
        if show_scores == "true":
            name = TeamCodes[i['away_team_id']][0] + ' - ' + i['away_score'] + ' @ ' + TeamCodes[i['home_team_id']][0] + ' - ' + i['home_score']
        else:
            name = TeamCodes[i['away_team_id']][0] + ' @ ' + TeamCodes[i['home_team_id']][0]
        addLink(name, url, '', 2, 'http://mlbmc-xbmc.googlecode.com/svn/icons/condensed.png')


def gameHighlights():
    thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/highlights.png'
    days = getDays(datetime.today())
    for i in days:
        addGameDir(i[0],i[1],26,thumb)


def getGameHighlights(dstr):
    base = 'http://www.mlb.com/gdcross/components/game/mlb/'
    thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/highlights.png'
    try:
        data = json.loads(getRequest(base + dstr +'/grid.json'))
        items = data['data']['games']['game']
        for i in items:
            try:
                gameId = i['id']
                gid = gameId.replace('/','_')
                gid = gid.replace('-','_')
                glbl = TeamCodes[i['away_team_id']][0] + ' @ ' + TeamCodes[i['home_team_id']][0]
                gurl = 'http://gdx.mlb.com/components/game/mlb/' + dstr + '/gid_' + gid + '/media/highlights.xml'
                addon_log( "gsh item: " + str(gid) + ', lbl: ' + glbl + ', url:' + gurl )
                addDir(glbl, gurl, 27, thumb)
            except:
                continue
    except:
        pass


def getVideoListXml(url):
    url = 'http://mlb.mlb.com'+url
    soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
    items = soup('item')
    for item in items:
        name = item.blurb.string
        vidId = item['content_id']
        url = vidId[-3]+'/'+vidId[-2]+'/'+vidId[-1]+'/'+vidId
        try:
            thumb = item('image', attrs={'type' : "13"})[0].string
        except:
            thumb = item.image.string
        duration = item.duration.string
        addLink(name,'http://mlb.mlb.com/gen/multimedia/detail/'+url+'.xml',duration,2,thumb)


def Search(url):
    if url == '' or url is None:
        searchStr = ''
        keyboard = xbmc.Keyboard(searchStr, 'MLB.com Video Search')
        keyboard.doModal()
        if (keyboard.isConfirmed() == False):
            return
        newStr = keyboard.getText()
        if len(newStr) == 0:
            return
        searchStr = newStr.replace(' ','%20')
        referStr = newStr.replace(' ','+')
        url = ('http://mlb.mlb.com/ws/search/MediaSearchService?start=0&site=mlb&hitsPerPage=12&hitsPerSite=10&'+
               'type=json&c_id=&src=vpp&sort=desc&sort_type=custom&query='+searchStr)
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : 'http://mlb.mlb.com/search/media.jsp?query='+referStr+'&c_id=mlb'}
    else:
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : 'http://mlb.mlb.com/search/media.jsp?query='+url.split('=')[-1]+'&c_id=mlb'}
    data = json.loads(getRequest(url,None,headers))
    if data['total'] == 0:
        xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30037)+data['query']+"',5000,"+icon+")")
        return
    videos = data['mediaContent']
    for video in videos:
        name = video['blurb']
        desc = video['bigBlurb']
        link = video['url']
        duration = video['duration']
        try:
            thumb = video['thumbnails'][1]['src']
        except:
            thumb = video['thumbnails'][0]['src']
        addLink(name,link,duration,2,thumb)
    if data['total'] > data['end']:
        url = url.split('&',1)[0][:-1]+str(data['end']+1)+'&'+url.split('&',1)[1]
        addDir(language(30034),url,16,next_icon)


def getFullCount():
    url = 'http://mlb.mlb.com/gen/multimedia/fullcount.xml'
    thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/fullcount.png'
    soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
    for i in soup('stream'):
        event_date = i.event_date.string
        event_id = i['calendar_event_id']
        if i.media_state.string == 'MEDIA_ON':
            name = language(30002)+language(30038)
            mode = '25'
            is_playable = True
        else:
            mode = '24'
            is_playable = False
            try:
                dt = time.strptime(event_date[:-5], "%Y-%m-%dT%H:%M:%S")
                name = time.strftime( "%A, %B %d @ %I:%M%p ET", dt)
            except:
                name = event_date
        u=sys.argv[0]+"?mode="+mode+"&name="+urllib.quote_plus(name)+"&event="+urllib.quote_plus(event_id)
        if is_playable:
            liz=xbmcgui.ListItem(coloring( name,"cyan",name ), iconImage="DefaultVideo.png", thumbnailImage=thumb)
            liz.setProperty('IsPlayable', 'true')
            liz.setInfo( type="Video", infoLabels={ "Title": name } )
        else:
            liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
        liz.setProperty( "Fanart_Image", fanart1 )
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)


def getGames(url):
    if addon.getSetting('email') == "":
        xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30039)+",30000,"+icon+")")
        addon.openSettings()
    data = json.loads(getRequest(url))
    try:
        games = data['data']['games']['game']
        if not isinstance(games, list):
            games = [data['data']['games']['game']]
    except:
        xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30040)+",10000,"+icon+")")
        return
    for game in games:
        mode = '7'
        home_team = game['home_team_city']
        away_team = game['away_team_city']
        status = game['status']['status']
        if show_scores == 'true':
            try:
                home_score = 0
                away_score = 0
                for i in game['linescore']['inning']:
                    try:
                        home_score += int(i['home'])
                    except: pass
                    try:
                        away_score += int(i['away'])
                    except: pass
                home_team += ' '+str(home_score)
                away_team += ' '+str(away_score)
            except KeyError: pass
        name = away_team+' @ '+home_team+'  '

        try:
            event_id = game['game_media']['media'][0]['calendar_event_id']
        except:
            try:
                event_id = game['game_media']['media']['calendar_event_id']
            except:
                addon_log( name+'event_id exception' )
                mode = '24'
                event_id = ''

        try:
            thumb = game['video_thumbnail']
        except:
            try:
                thumb = game['game_media']['media']['thumbnail']
            except:
                try:
                    thumb = game['game_media']['media'][0]['thumbnail']
                except:
                    thumb = ''

        try:
            media_state = game['game_media']['media']['media_state']
        except:
            try:
                media_state = game['game_media']['media'][0]['media_state']
            except:
                addon_log( name+'media_state exception' )
                media_state = ''

        if status == 'In Progress':
            try:
                name += str(game['status']['inning_state'])+' '+str(game['status']['inning'])
            except:
                name += status
        elif not status == 'Final':
            try:
                name += str(game['time']) + ' ' + str(game['time_zone']) + ' '
                if not status == 'Preview':
                    name += status
            except:
                pass

        archive = False
        if status == 'Final':
            if media_state == 'media_archive':
                try:
                    mlbtv = game['game_media']['media']['has_mlbtv']
                except:
                    try:
                        mlbtv = game['game_media']['media'][0]['has_mlbtv']
                    except:
                        mlbtv = ''
                if mlbtv == 'true':
                    name += language(30029)
                    archive = True
                else:
                    name += status

        try:
            free = game['game_media']['media']['free']
        except:
            try:
                free = game['game_media']['media'][0]['free']
            except:
                free = ''
        if free == 'ALL':
            name += language(30030)

        name = name.replace('.','').rstrip(' ')

        u=sys.argv[0]+"?url=&mode="+mode+"&name="+urllib.quote_plus(name)+"&event="+urllib.quote_plus(event_id)
        if media_state == 'media_on':
            liz=xbmcgui.ListItem(coloring( name,"cyan",name ), iconImage="DefaultVideo.png", thumbnailImage=thumb)
        elif archive:
            liz=xbmcgui.ListItem(coloring( name,"orange",name ), iconImage="DefaultVideo.png", thumbnailImage=thumb)
        else:
            liz=xbmcgui.ListItem(coloring( name,"lightgrey",name ), iconImage="DefaultVideo.png", thumbnailImage=thumb)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart1 )
        liz.setProperty('IsPlayable', 'true')
        # xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)


def getDate(game_type):
    if game_type == 'mlbtv':
        href = '/master_scoreboard.json'
    else:
        href = '/grid.json'
    date = ''
    keyboard = xbmc.Keyboard(date, 'Format: yyyy/mm/dd' )
    keyboard.doModal()
    if (keyboard.isConfirmed() == False):
        return
    date = keyboard.getText()
    if len(date) != 10:
        xbmc.executebuiltin("XBMC.Notification("+language(30035)+","+language(30041)+",5000,"+icon+")")
        return
    date = 'year_'+date.split('/')[0]+'/month_'+date.split('/')[1]+'/day_'+date.split('/')[2]
    url = 'http://mlb.mlb.com/gdcross/components/game/mlb/'+date+href
    return url


class dateStr:
    format = "year_%Y/month_%m/day_%d"
    t = datetime.today()
    t_delay = t - timedelta(hours=3)
    today = t_delay.strftime(format)
    one_day = timedelta(days=1)
    y = t - one_day
    yesterday = y.strftime(format)
    to = t + one_day
    tomorrow = to.strftime(format)
    by = t - (one_day*2)
    byesterday = by.strftime(format)
    day = (today,yesterday,tomorrow,byesterday)