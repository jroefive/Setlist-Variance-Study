from json import load, dumps
from itertools import chain
from collections import Counter
from datetime import datetime
import pandas as pd
from statistics import mean
import numpy as np
from scipy.stats import iqr
from bokeh.plotting import figure, ColumnDataSource
from bokeh.transform import jitter, linear_cmap
from bokeh.models import ColorBar, NumeralTickFormatter
from bokeh.palettes import RdYlBu11
from bokeh.layouts import row
import streamlit as st



st.beta_set_page_config(layout='wide')

#Hover text format for '

green = '#264653'
light_green = '#2a9d8f'
blue = '#1964aa'
light_blue = '#009fe3'
red = '#f03b20'
dark_red = '#cf270e'
yellow = '#e9c46a'
orange = '#f4a261'

def get_setlist_dict(band_json):
    #Open file for band name
    with open('data/' + band_json) as f:
      setlist_dict = load(f)

    #Get list of all dates
    dates = setlist_dict.keys()

    #Delete dates if they don't have any setlist
    for date in list(dates):
        if setlist_dict[date] == []:
            del setlist_dict[date]

    return setlist_dict

def get_top_songs(setlist_dict):
    #Create empty lists to add to
    all_songs = []
    #show_length = []
    #Run through all dates to get a list of all songs played
    for date, songs in setlist_dict.items():
        num_of_songs = 0
        for setx in songs:
            #Add all the set lengths together
            num_of_songs += len(setx[1])
            #Add all songs from a set to the overall songs list
            all_songs.append(setx[1])
        #Add total show length after running through all sets in a show
        #show_length.append((date,num_of_songs))

    #Flatten all songs list
    all_songs = list(chain.from_iterable(all_songs))
    #Get the top 10 songs and how many times each was played
    song_counts = Counter(all_songs).most_common(10)
    #Pull out just the song names
    top_songs = [x[0] for x in song_counts]
    return top_songs, song_counts

def get_song_position_list(setlist_dict):
    dates = setlist_dict.keys()
    date_list = list(dates)
    dates_asc = date_list[::-1]
    top_songs, song_counts = get_top_songs(setlist_dict)
    song_position_lists = [[], [], [], [], [], [], [], [], [], []]
    for date in dates_asc:
        #Refresh song list each time a new date loops
        show_song_list = []
        #Add the songs for each set in the show
        for setx in setlist_dict[date]:
            show_song_list.append(setx[1])
        #Flatten the list and turn it to a set to remove if a song was listed twice

        show_song_list = list(chain.from_iterable(show_song_list))


        if len(show_song_list) > 4:
            for song in show_song_list:
                # For the top 10 songs, get their placement in the show
                if song in top_songs:
                    # Get the song number in top songs to add to the right list
                    song_index = top_songs.index(song)
                    songlist = list(show_song_list)
                    # Add the placement and date to the right song position list
                    placement_tuple = (songlist.index(song) / len(show_song_list), date)
                    song_position_lists[song_index].append(placement_tuple)
    return song_position_lists

def get_song_gap_graph(band_json, band, size):
    setlist_dict = get_setlist_dict(band_json)
    #Reset dates
    dates = setlist_dict.keys()

    #A bunch of empty lists and dicts for checking on placement and if songs had been played recently
    prev_show_list = []
    shows_two_ago = []
    three_shows_ago = []
    new_show_songs_dict = {}
    new_show_songs_dict2 = {}
    new_show_songs_dict3 = {}
    date_list = list(dates)
    dates_asc = date_list[::-1]

    #Run through all dates from first to late show
    shows = 0
    for date in dates_asc:
        #Refresh song list each time a new date loops
        show_song_list = []
        #Add the songs for each set in the show
        for setx in setlist_dict[date]:
            show_song_list.append(setx[1])
        #Flatten the list and turn it to a set to remove if a song was listed twice
        show_song_list = list(chain.from_iterable(show_song_list))
        show_song_list = set(show_song_list)
        #only do shows 5 songs or more to avoid noise from late night sets, etc.
        if len(show_song_list) > 4:
            shows += 1
            #New songs compared to the previous show

            #New songs that weren't in the previous 2 shows
            prev_2_show_list = list(prev_show_list) + list(shows_two_ago)

            #New songs that weren't in the previous 3 shows
            prev_3_show_list = list(prev_show_list) + list(shows_two_ago) + list(three_shows_ago)
            new_songs_3 = set(show_song_list) - set(prev_3_show_list)
            new_songs_2 = set(show_song_list) - set(prev_2_show_list) - set(new_songs_3)
            new_songs = set(show_song_list) - set(prev_show_list) - set(new_songs_2) - set(new_songs_3)

            #Shift all lists to be one show older before looping to next show
            new_show_songs_dict[date] = (len(new_songs), len(new_songs) / len(show_song_list), list(new_songs))
            new_show_songs_dict2[date] = (len(new_songs_2), len(new_songs_2) / len(show_song_list), list(new_songs_2))
            new_show_songs_dict3[date] = (len(new_songs_3), len(new_songs_3) / len(show_song_list), list(new_songs_3))

            three_shows_ago = shows_two_ago
            shows_two_ago = prev_show_list
            prev_show_list = show_song_list

    #Turn dicts into DFs for graphing
    new_show_songs_df = pd.DataFrame.from_dict(new_show_songs_dict).T
    new_show_songs_df.columns=['NumberNewSongs', 'PercentSongsNew','NewSongs']
    new_show_songs_df.index.names = ['Date']
    new_show_songs_df2 = pd.DataFrame.from_dict(new_show_songs_dict2).T
    new_show_songs_df2.columns=['NumberNewSongs', 'PercentSongsNew','NewSongs']
    new_show_songs_df2.index.names = ['Date']
    new_show_songs_df3 = pd.DataFrame.from_dict(new_show_songs_dict3).T
    new_show_songs_df3.columns=['NumberNewSongs', 'PercentSongsNew','NewSongs']
    new_show_songs_df3.index.names = ['Date']
    pd.set_option('max_columns', None)
    #Join dfs for graph stacking
    new_show_songs_23_df = new_show_songs_df2.join(new_show_songs_df3, lsuffix='_2', rsuffix='_3')
    new_show_songs_overall_df = new_show_songs_df.join(new_show_songs_23_df)
    new_show_songs_overall_df['TotPerc'] = new_show_songs_overall_df['PercentSongsNew'] + \
                                           new_show_songs_overall_df['PercentSongsNew_2'] + \
                                           new_show_songs_overall_df['PercentSongsNew_3']
    new_show_songs_overall_df['Total Percent'] = new_show_songs_overall_df['TotPerc'].astype(float)
    new_show_songs_overall_df.reindex(index=new_show_songs_overall_df.index[::-1])
    new_show_songs_overall_df['Rolling Average'] = new_show_songs_overall_df['Total Percent'].rolling(window=5).mean()
    new_show_songs_overall_df['Expanding Average'] = new_show_songs_overall_df['Total Percent'].expanding().mean()
    expanding_avs = new_show_songs_overall_df['Expanding Average'].values

    new_show_songs_overall_df.reindex(index=new_show_songs_overall_df.index[::-1])

    #Create graph for show gaps
    show_gaps_perc = ['PercentSongsNew','PercentSongsNew_2','PercentSongsNew_3']
    legend_perc = ['% Songs Not Played in Previous Show', '% Songs Not Played in Last Two Shows',
                   '% Songs Not Played  in Last Three Shows'
                   ]

    source_snsg = ColumnDataSource(new_show_songs_overall_df)

    show_new_songs_perc_graph = figure(y_range=list(dates), title=band, plot_height=int(700*size),
                                       plot_width=int(700*size), toolbar_location=None,
                                       tooltips = [('Date', '@Date'), ('Not Played Prev Show','@NewSongs'),
                                                   ('2 Show Gap', '@NewSongs_2'), ('3 Show Gap','@NewSongs_3')
                                                   ]
                                       )

    show_new_songs_perc_graph.hbar_stack(show_gaps_perc, y='Date', height = 0.9, source=source_snsg,
                                         legend_label=legend_perc, color=[yellow, orange, red]
                                         )
    show_new_songs_perc_graph.line(y='Date', x='Expanding Average', line_width=3, source=source_snsg,
                                   color=dark_red, legend_label='Average % Songs Not Played in Previous Show'
                                   )
    show_new_songs_perc_graph.xgrid.grid_line_color = None
    show_new_songs_perc_graph.ygrid.grid_line_color = None
    show_new_songs_perc_graph.yaxis.major_label_text_font_size = '0pt'
    show_new_songs_perc_graph.yaxis.major_tick_line_color = None  # turn off x-axis major ticks
    show_new_songs_perc_graph.yaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    show_new_songs_perc_graph.yaxis.axis_label = '(<-Most Recent)         All Shows Played         (Earliest Shows->)'
    show_new_songs_perc_graph.xaxis[0].formatter = NumeralTickFormatter(format='0%')
    #show_new_songs_perc_graph.add_layout(show_new_songs_perc_graph.legend[0], 'right')
    show_new_songs_perc_graph.legend.click_policy = 'hide'
    show_new_songs_perc_graph.legend.title = 'Click on Legend to Hide Individual Sections'
    show_new_songs_perc_graph.xaxis.axis_label = 'Percentage of Songs in a Show That Hadn''t Been Played Recently'
    return show_new_songs_perc_graph, expanding_avs[-1]


def get_top_song_freq_graph(band_json, band, size):
    setlist_dict = get_setlist_dict(band_json)
    top_songs, song_counts = get_top_songs(setlist_dict)
    dates = setlist_dict.keys()
    #Get the date that each of the top songs was debuted
    debut_dict = {}
    for topsong in top_songs:
        #Iterate through all shows from most recent to oldest and update the date only if the song is in the show
        for date, songs in setlist_dict.items():
            for setx in songs:
                if topsong in setx[1]:
                    debut_dict[topsong] = date

    #Count the number of shows that happened since the debut date
    debuts_totals = []
    #Change dates to datetime objects for comparing
    dates_obj = [datetime.strptime(x, '%d-%m-%Y') for x in dates]
    for debut_date in debut_dict.values():
        debut_date_obj = datetime.strptime(debut_date, '%d-%m-%Y')
        shows_since_debut = [x for x in dates_obj if x > debut_date_obj]
        tup = (len(shows_since_debut), debut_date)
        debuts_totals.append(tup)

    #Turn total times played and total shows since debut into a percent
    percent_of_shows_info = []
    for i in range(0,10):
        perc = ((int(song_counts[i][1])/debuts_totals[i][0]), song_counts[i][1],
                debuts_totals[i][0], debuts_totals[i][1])
        percent_of_shows_info.append(perc)

    #Create graph of percentage of shows have top 10 songs
    #Update list to include average of top 10
    percent_of_shows = [x[0] for x in percent_of_shows_info]
    #Average out all the percents
    avg_of_top_ten = (sum(percent_of_shows)/len(percent_of_shows))

    percent_of_shows_df = pd.DataFrame(percent_of_shows_info)
    percent_of_shows_df['song'] = top_songs
    avg_row = [avg_of_top_ten,'','','','Average of Top 10']
    percent_of_shows_df.columns = ['Percent', 'TimesPlayed', 'ShowsSinceDebut', 'DebutDate', 'song']
    avg_series = pd.Series(avg_row, percent_of_shows_df.columns)
    percent_of_shows_df = percent_of_shows_df.append(avg_series, ignore_index=True)
    top_songs_w_avg = percent_of_shows_df['song'].values
    top_songs_w_avg = top_songs_w_avg[::-1]
    colors =  [light_green] * 10 + [green]
    percent_of_shows_df.insert(5, 'Color', colors, True)



    source_top = ColumnDataSource(percent_of_shows_df)
    top_songs_percent_graph = figure(y_range=top_songs_w_avg, title=band, frame_width=int(400*size),
                                     plot_width=int(700*size), toolbar_location=None,
                                     tooltips=[('Percent','@Percent'),('Times Played', ''@TimesPlayed''),
                                               ('Shows Since Debut','@ShowsSinceDebut'), ('Debut Date', '@DebutDate')
                                               ]
                                     )

    top_songs_percent_graph.hbar(y='song', right='Percent', height=0.9, color = 'Color', source=source_top)
    top_songs_percent_graph.xaxis[0].formatter = NumeralTickFormatter(format='0%')
    top_songs_percent_graph.circle(x=1,y=0)
    top_songs_percent_graph.xaxis.axis_label = '% of Shows Where Most Popular Songs Were Played'
    return top_songs_percent_graph, avg_of_top_ten


def get_new_year_songs_graph(band_json, band, size):
    setlist_dict = get_setlist_dict(band_json)
    #Get a list of all years
    dates = setlist_dict.keys()
    years_all = list([x[-4:] for x in dates])
    years = sorted(set(years_all))

    #Create a dict that shows how many song were played in a year that weren't played the year before
    year_songs_dict = {}
    new_year_songs_dict = {}
    prev_year_songs = []
    for year in years:
        #Refresh the list of songs for the year each time through the loop
        year_song_list = []
        for date in dates:
            #Only add the songs if the year of the show matches the year of the loop
            if year == date[-4:]:
                for setx in setlist_dict[date]:
                    year_song_list.append(setx[1])
        #Flatten the list and subtract out all the songs that were played the year before
        year_song_list = list(chain.from_iterable(year_song_list))
        year_song_list = set(year_song_list)
        new_songs = set(year_song_list) - set(prev_year_songs)
        if len(year_song_list) > 10:
            #Add totals and lists to dicts
            year_songs_dict[year] = (len(year_song_list), year_song_list)
            new_year_songs_dict[year] = (len(new_songs), len(new_songs)/len(year_song_list), list(new_songs))
            #Shift the previous year song list to the current year before looping
            prev_year_songs = year_song_list

    #Turn new year songs dict into a df
    new_year_songs_df = pd.DataFrame.from_dict(new_year_songs_dict).T
    new_year_songs_df.columns=['NumberNewSongs', 'Percent of Songs New','NewSongs']
    new_year_songs_df.index.names = ['Date']
    years = new_year_songs_df.index.values
    percents_year_list = list(new_year_songs_df['Percent of Songs New'].values)
    percents_year_list.pop(0)
    year_percents_avg = sum(percents_year_list)/len(percents_year_list)
    avg_row = [0, year_percents_avg, ['']]
    avg_series = pd.Series(avg_row, new_year_songs_df.columns)
    new_year_songs_df = new_year_songs_df.append(avg_series, ignore_index=True)
    years_w_av = list(years) + list(['Average of Years'])
    new_year_songs_df.index = years_w_av
    new_year_songs_df.index.names = ['Date']

    colors =  [light_blue] * (len(years_w_av)-1) + [blue]
    new_year_songs_df.insert(3, 'Color', colors, True)


    years = new_year_songs_df.index.values
    years_asc = years_w_av[::-1]
    #Create graph for new songs per years
    source_ynsg = ColumnDataSource(new_year_songs_df)
    year_new_songs_graph = figure(y_range = years_asc, title=band, frame_width=int(400*size), plot_width=int(700*size),
                                  toolbar_location=None,
                                  tooltips=[('# of Songs Not Play Previous Year', '@NumberNewSongs'),
                                            ('New Songs', '@NewSongs')
                                            ]
                                  )
    year_new_songs_graph.hbar(y='Date', right='Percent of Songs New', height=0.9, color='Color', source=source_ynsg)
    year_new_songs_graph.xaxis[0].formatter = NumeralTickFormatter(format='0%')
    year_new_songs_graph.xaxis.axis_label = '% of Songs Played Each Year That Weren''t Played the Year Before'
    return year_new_songs_graph, year_percents_avg

def get_song_placement_df(band_json, song_position_lists):
    setlist_dict = get_setlist_dict(band_json)
    top_songs, song_counts = get_top_songs(setlist_dict)
    #Create graph for placement of top 10 songs
    #Turn placement lists into df
    placement_df = pd.DataFrame(columns=['song','placement','date'])
    for index, placement_list in enumerate(song_position_lists):
        for placement in placement_list:
            x = (top_songs[index],placement[0],placement[1])
            x_series = pd.Series(x, index = ['song','placement','date'])
            placement_df = placement_df.append(x_series, ignore_index=True)

    placement_df['year'] = placement_df['date'].str[-4:].astype(int)
    placement_df['Percent Whole'] = round(placement_df['placement']*100,2)
    placement_df['hover'] = placement_df['Percent Whole'].astype(str) + '% into Show'
    #placement_df.to_csv('sample_placement_df.csv')
    return placement_df, top_songs

def get_iqr_df(song_position_lists, top_songs):
    q1_of_positions = []
    q3_of_positions = []
    iqr_of_positions = []
    for placement_list in song_position_lists:
        iqr_of_positions.append(iqr([x[0] for x in placement_list]))
        q1_of_positions.append(np.percentile([x[0] for x in placement_list],25))
        q3_of_positions.append(np.percentile([x[0] for x in placement_list],75))
    avg_iqr_placement = mean(iqr_of_positions)

    dat_tup = zip(top_songs,q1_of_positions,q3_of_positions)
    iqr_df = pd.DataFrame(dat_tup, columns=['Songs', 'Q1', 'Q3'])
    iqr_row = ['Average IQR',0,avg_iqr_placement]
    iqr_series = pd.Series(iqr_row, index=['Songs', 'Q1', 'Q3'])
    iqr_df = iqr_df.append(iqr_series, ignore_index=True)
    iqr_df.reindex(index=iqr_df.index[::-1])
    return iqr_df, avg_iqr_placement

def get_song_placement_graph(band_json, band, size):
    with open('data/song_position_dict.json') as f:
      song_position_dict = load(f)
    song_position_lists = song_position_dict[band]
    placement_df, top_songs = get_song_placement_df(band_json, song_position_lists)

    iqr_df, avg_iqr_placement = get_iqr_df(song_position_lists, top_songs)

    #Create color coding for placement
    years = placement_df['year'].values
    mapper = linear_cmap(field_name='year', palette=RdYlBu11, low=min(years), high=max(years))
    top_songs_w_av = ['Average IQR'] + top_songs[::-1]
    source_place = ColumnDataSource(placement_df)
    source_iqr = ColumnDataSource(iqr_df)
    top10_placement = figure(y_range=top_songs_w_av, title=band, frame_width=int(400*size),
                             plot_width=int(700*size), tooltips=[('Date','@date'), ('Show Placement','@hover')],
                             sizing_mode='stretch_both', toolbar_location=None
                             )
    top10_placement.circle(x='placement', y=jitter('song', width=0.4, range=top10_placement.y_range),
                           radius=0.01, fill_alpha=0.6, source=source_place, color=mapper
                           )
    top10_placement.hbar(y='Songs', left='Q1', right='Q3', source = source_iqr,
                         height = 0.4, color = yellow, fill_alpha=0.5
                         )
    color_bar = ColorBar(color_mapper=mapper['transform'], width=8, location=(0, 0))
    top10_placement.add_layout(color_bar, 'right')
    top10_placement.xaxis.ticker = [0, 0.5, 1]
    top10_placement.xaxis.major_label_overrides = {0: 'Start of Show', 0.5: 'Middle of Show', 1: 'End of Show', }
    top10_placement.circle(x=1,y=0)
    top10_placement.xaxis.axis_label = 'Placement of Top 10 Most Played Songs'
    return top10_placement, avg_iqr_placement


def get_metrics_df(band_dict):
    metrics_desc = ['Band', 'Song Gaps', 'New Songs Per Year', 'Top 10 Song Frequency', 'Top 10 Song Placement']

    metrics_df = pd.DataFrame()
    for band, key in band_dict.items():
        graph1, met1 = get_song_placement_graph(key + '.json', band)
        graph2, met2 = get_new_year_songs_graph(key + '.json', band)
        graph3, met3 = get_top_song_freq_graph(key + '.json', band)
        graph4, met4 = get_song_gap_graph(key + '.json', band)
        met_row = [band, met4, met2, 1-met3, met1]
        met_series = pd.Series(met_row, index=metrics_desc)
        metrics_df = metrics_df.append(met_series, ignore_index=True)


    #metrics_df.to_csv('metrics_df.csv')
    return metrics_df

def get_metrics_graph(sort_by, bands, size):

    #metrics_df = get_metrics_df(band_dict)
    metrics_df = pd.read_csv('data/metrics_df.csv')
    metrics_df['Total of all Metrics'] = metrics_df['Song Gaps'] + metrics_df['New Songs Per Year'] + \
                                         metrics_df['Top 10 Song Frequency'] + metrics_df['Top 10 Song Placement']
    if sort_by == 'Song Gaps':
        mets = ['Song Gaps', 'New Songs Per Year', 'Top 10 Song Frequency', 'Top 10 Song Placement']
        colors = [dark_red, blue, green, yellow]
    elif sort_by == 'New Songs Per Year':
        mets = ['New Songs Per Year', 'Song Gaps', 'Top 10 Song Frequency', 'Top 10 Song Placement']
        colors = [blue, dark_red, green, yellow]
    elif sort_by == 'Top 10 Song Frequency':
        mets = ['Top 10 Song Frequency', 'Song Gaps', 'New Songs Per Year', 'Top 10 Song Placement']
        colors = [green, dark_red, blue, yellow]
    elif sort_by == 'Top 10 Song Placement':
        mets = ['Top 10 Song Placement', 'Song Gaps', 'New Songs Per Year', 'Top 10 Song Frequency']
        colors = [yellow, dark_red, blue, green]
    else:
        mets = ['Song Gaps', 'New Songs Per Year', 'Top 10 Song Frequency', 'Top 10 Song Placement']
        colors = [dark_red, blue, green, yellow]

    metrics_df = metrics_df.sort_values(by=[sort_by])

    bands_order = metrics_df['Band'].values

    bands = [x for x in bands_order if x in bands]

    source_met = ColumnDataSource(metrics_df)
    metrics_graph = figure(y_range=bands, title='Comparison of All Metrics', plot_width=int(1200*size),
                           plot_height = int(700*size), toolbar_location=None
                           )

    metrics_graph.hbar_stack(mets, y='Band', source=source_met, legend_label=mets, height=0.9, color=colors)
    metrics_graph.xaxis.axis_label = 'Total of All Setlist Variance Metrics'
    return metrics_graph



band_dict = {'Vampire Weekend':'vampireweekend', 'Arcade Fire':'arcadefire', 'Beck':'beck', 'Pearl Jam':'pearljam',
             'Phish':'phish', 'Grateful Dead':'gratefuldead', 'Metallica':'metallica', 'Radiohead':'radiohead',
             'Foo Fighters':'foofighters', 'Muse':'muse', 'Iron Maiden':'ironmaiden', 'U2':'u2',
             'Red Hot Chili Peppers':'rhcp', 'The Rolling Stones':'rollingstones', 'Dave Matthews Band':'dmb',
             'Tame Impala':'tameimpala', 'LCD Soundsystem':'lcd', 'The Avett Brothers':'avett', 'Ween':'ween',
             'Neil Young':'neilyoung', 'Bruce Springteen':'springsteen', 'King Gizzard':'kinggizzard',
             'Billy Strings':'billy', 'Bob Dylan':'dylan', 'Jimmy Buffett':'buffett', 'Dream Theater':'dream',
             'Animal Collective':'animal', 'Wilco':'wilco', 'String Cheese Incident':'sci', 'Medeski Martin Wood':'mmw',
             'My Morning Jacket':'mmj', 'Portugal. the Man':'portugal', 'moe.':'moe', 'Santana':'santana',
             'Frank Zappa':'zappa', 'Billy Joel':'joel', 'Goose':'goose', 'Greensky Bluegrass':'greensky',
             'Widespread Panic':'wsp', 'Umphrey''s McGee':'umphreys', 'STS9':'sts9', 'Disco Biscuits':'disco',
             'Jason Isbell':'isbell', 'Drive-By Truckers':'dbt', 'Railroad Earth':'rre', 'The National':'national',
             'Talking Heads':'heads', 'Van Morrison':'van', 'Bon Iver':'bon', 'Tom Petty':'petty', 'Steely Dan':'steely',
             'Clutch':'clutch', 'Kendrick Lamar':'kendrick', 'Kanye West':'kanye', 'Beyonce':'bey', 'Jay-Z':'jayz',
             'Stevie Wonder':'stevie', 'Prince':'prince'
             }
band_jam = ['Phish', 'Grateful Dead', 'Dave Matthews Band', 'Ween', 'Billy Strings', 'String Cheese Incident',
            'Medeski Martin Wood', 'moe.', 'Goose', 'Greensky Bluegrass', 'Widespread Panic', 'Umphrey''s McGee',
            'STS9', 'Disco Biscuits', 'Railroad Earth'
            ]
band_classic = ['Grateful Dead', 'Metallica', 'Iron Maiden', 'U2', 'The Rolling Stones', 'Neil Young',
                'Bruce Springsteen', 'Bob Dylan', 'Jimmy Buffett', 'Santana', 'Frank Zappa', 'Billy Joel',
                'Talking Heads', 'Van Morrison', 'Tom Petty', 'Steely Dan', 'Stevie Wonder', 'Prince', 'Dream Theater',
                'Red Hot Chili Peppers'
                ]
band_other = ['Vampire Weekend', 'Arcade Fire', 'Beck', 'Radiohead', 'Foo Fighters', 'Muse', 'Tame Impala',
              'LCD Soundsystem', 'The Avett Brothers', 'King Gizzard', 'Animal Collective', 'Wilco',
              'My Morning Jacket', 'Portugal. the Man', 'Jason Isbell', 'Drive-By Truckers', 'The National',
              'Bon Iver', 'Clutch', 'Kendrick Lamar', 'Kanye West', 'Beyonce', 'Jay-Z', 'Pearl Jam'
              ]
bands_less250 = ['Billy Strings', 'Disco Biscuits', 'Goose',
                 'Greensky Bluegrass', 'Jay-Z', 'Kanye West', 'Medeski Martin Wood'
                 ]


st.sidebar.write('A Dashboard to Explore How Much Bands Change Their Setlists')
resize = st.sidebar.checkbox('Shrink Graphs for Mobile')
include250 = st.sidebar.checkbox('Include Bands With Less Than 250 Show')

if resize:
    size = .6
else:
    size = 1

def create_song_position_dict():
    song_position_dict = {}
    for band, band_id in band_dict.items():
        setlist_dict = get_setlist_dict(band_id + '.json')
        band_pos_list = get_song_position_list(setlist_dict)
        song_position_dict[band] = band_pos_list

    json = dumps(song_position_dict)
    f = open('data/song_position_dict.json', 'w')
    f.write(json)
    f.close()

genre_select = st.sidebar.selectbox( 'Band Groups',
                                     ('All Bands', 'Bands Starting Before 1990',
                                      'Bands Starting After 1990','Jam Bands'
                                      )
                                     )
if include250:
    if genre_select == 'All Bands':
        bands = sorted(list(band_dict.keys()))
    elif genre_select == 'Jam Bands':
        bands = sorted(band_jam)
    elif genre_select == 'Bands Starting Before 1990':
        bands = sorted(band_classic)
    elif genre_select == 'Bands Starting After 1990':
        bands = sorted(band_other)
else:
    if genre_select == 'All Bands':
        bands = [x for x in sorted(list(band_dict.keys())) if x not in bands_less250]
    elif genre_select == 'Jam Bands':
        bands = [x for x in sorted(band_jam) if x not in bands_less250]
    elif genre_select == 'Bands Starting Before 1990':
        bands = [x for x in sorted(band_classic) if x not in bands_less250]
    elif genre_select == 'Bands Starting After 1990':
        bands = [x for x in sorted(band_other) if x not in bands_less250]

band_selectbox_a = st.sidebar.selectbox(
    'Choose First Band',
    (bands), index=0
)


band_selectbox_b = st.sidebar.selectbox(
    'Choose Second Band',
    (bands), index=1
)

graph_selectbox = st.sidebar.selectbox(
    'Choose a Comparison',
    ('Song Gaps', 'New Songs Per Year', 'Top 10 Song Frequency',
     'Top 10 Song Placement', 'Compare Bands Across All Measures')
)

if graph_selectbox == 'Compare Bands Across All Measures':
    sort_by = st.sidebar.selectbox('Sort By:',
                                   ('Total of all Metrics', 'Song Gaps', 'New Songs Per Year',
                                    'Top 10 Song Frequency', 'Top 10 Song Placement'
                                    )
                                   )

link = '[Link to Explanations](https://jroefive.github.io/2020/09/30/Visualizing-and-Comparing-Setlist-Variance.html)'
st.sidebar.markdown(link, unsafe_allow_html=True)
st.sidebar.write('Feedback and Feature Requests can be sent to: @JesseRoe55 on Twitter or PhishStatSpatula on Reddit')

if graph_selectbox == 'Song Gaps':
    graph1_a, meta = get_song_gap_graph(band_dict[band_selectbox_a] + '.json', band_selectbox_a, size)
    graph1_b, metb = get_song_gap_graph(band_dict[band_selectbox_b] + '.json', band_selectbox_b, size)
    graph1_a.legend.visible = False
    if size == 0.6:
        graph1_b.legend.visible = False
    two_graphs = row(graph1_a, graph1_b)
elif graph_selectbox == 'New Songs Per Year':
    graph1_a, meta = get_new_year_songs_graph(band_dict[band_selectbox_a] + '.json', band_selectbox_a, size)
    graph1_b, metb = get_new_year_songs_graph(band_dict[band_selectbox_b] + '.json', band_selectbox_b, size)
    two_graphs = row(graph1_a, graph1_b)
elif graph_selectbox == 'Top 10 Song Frequency':
    graph1_a, meta = get_top_song_freq_graph(band_dict[band_selectbox_a] + '.json', band_selectbox_a, size)
    graph1_b, metb = get_top_song_freq_graph(band_dict[band_selectbox_b] + '.json', band_selectbox_b, size)
    two_graphs = row(graph1_a, graph1_b)
elif graph_selectbox == 'Top 10 Song Placement':
    graph1_a, meta = get_song_placement_graph(band_dict[band_selectbox_a] + '.json', band_selectbox_a, size)
    graph1_b, metb = get_song_placement_graph(band_dict[band_selectbox_b] + '.json', band_selectbox_b, size)
    two_graphs = row(graph1_a, graph1_b)
elif graph_selectbox == 'Compare Bands Across All Measures':
    two_graphs = get_metrics_graph(sort_by, bands, size)

st.bokeh_chart(two_graphs)
