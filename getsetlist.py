import requests
import json
import time

key = 'IgZc5xptAGjG7ZX9-xjxaJBTx_G-EiqzSjZd'

headers = {'Accept': 'application/json', 'x-api-key': key}

band = 'Bob Dylan'
band_id = '070d193a-845c-479f-980e-bef15710653e'
# Call Setlist.fm API
def get_band_id(band):
    response = requests.get('https://api.setlist.fm/rest/1.0/search/artists?artistName=' + band, headers=headers)
    r = json.loads(response.content)
    print(r)
    print(len(r['artist']))
    ids = []
    for artist in r['artist']:
        ids.append(artist['mbid'])
    print(r['artist'][0]['mbid'])
    print(ids)

#get_band_id(band)

def get_setlist_dict(band_id, pages):
    setlist_dict = {}
    for i in range(1,pages+1):
        time.sleep(2)
        response = requests.get('https://api.setlist.fm/rest/1.0/artist/'+ band_id +'/setlists?p=' + str(i), headers=headers)
        s = json.loads(response.content)
        print(s)
        for show in s['setlist']:
            print(show['eventDate'])
            print(i)
            setnum = 0
            showlist = []
            for set in show['sets']['set']:
                setnum += 1
                setlist = []

                for song in set['song']:
                    setlist.append(song['name'])
                showlist.append((setnum,setlist))
            setlist_dict[show['eventDate']] = showlist

    print(setlist_dict)
    json.dump(setlist_dict, open("data/prince.json", 'w'))

get_setlist_dict(band_id,96)








