import json
from itertools import chain
from collections import Counter, OrderedDict
from datetime import datetime
import pandas as pd
from bokeh.plotting import figure, output_file, show, ColumnDataSource
from bokeh.transform import jitter, linear_cmap
from bokeh.models import ColorBar, Panel, Tabs, NumeralTickFormatter, FixedTicker, HoverTool, Legend
from bokeh.palettes import RdYlBu11
import statistics
import streamlit as st

#Important Notes - Shows dropped with fewer than 5 songs to remove the late show appearance type shows


#Hover text format for '
#Change Colors I think it's good
# Update axes labels
#Come up with metrics for all pages
#Figure out what's wrong with placement
#fix running average to go forward
#Redo phish

def get_graphs(band_json):
    #Open file for band name
    with open(band_json) as f:
      setlist_dict = json.load(f)

    #Get list of all dates
    dates = setlist_dict.keys()

    #Delete dates if they don't have any setlist
    for date in list(dates):
        if setlist_dict[date] == []:
            del setlist_dict[date]

    #Reset dates
    dates = setlist_dict.keys()

    #Create empty lists to add to
    all_songs = []
    show_length = []
    #Run through all dates to get a list of all songs played
    for date, songs in setlist_dict.items():
        num_of_songs = 0
        for setx in songs:
            #Add all the set lengths together
            num_of_songs += len(setx[1])
            #Add all songs from a set to the overall songs list
            all_songs.append(setx[1])
        #Add total show length after running through all sets in a show
        show_length.append((date,num_of_songs))

    #Flatten all songs list
    all_songs = list(chain.from_iterable(all_songs))
    #Get the top 10 songs and how many times each was played
    song_counts = Counter(all_songs).most_common(10)
    #Pull out just the song names
    top_songs = [x[0] for x in song_counts]

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
    dates_obj = [datetime.strptime(x, "%d-%m-%Y") for x in dates]
    for debut_date in debut_dict.values():
        debut_date_obj = datetime.strptime(debut_date, "%d-%m-%Y")
        shows_since_debut = [x for x in dates_obj if x > debut_date_obj]
        tup = (len(shows_since_debut), debut_date)
        debuts_totals.append(tup)

    #Turn total times played and total shows since debut into a percent
    percent_of_shows_info = []
    for i in range(0,10):
        perc = ((int(song_counts[i][1])/debuts_totals[i][0]), song_counts[i][1], debuts_totals[i][0], debuts_totals[i][1])
        percent_of_shows_info.append(perc)



    #Get a list of all years
    years_all = list([x[-4:] for x in dates])
    year_counts = Counter(years_all)
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
        #Add totals and lists to dicts
        year_songs_dict[year] = (len(year_song_list), year_song_list)
        new_year_songs_dict[year] = (len(new_songs), len(new_songs)/len(year_song_list), list(new_songs))
        #Shift the previous year song list to the current year before looping
        prev_year_songs = year_song_list


    #A bunch of empty lists and dicts for checking on placement and if songs had been played recently
    prev_show_list = []
    shows_two_ago = []
    three_shows_ago = []
    new_show_songs_dict = {}
    new_show_songs_dict2 = {}
    new_show_songs_dict3 = {}
    date_list = list(dates)
    dates_asc = date_list[::-1]
    song_position_lists = [[],[],[],[],[],[],[],[],[],[]]

    #Run through all dates from first to late show
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
            for song in show_song_list:
                #For the top 10 songs, get their placement in the show
                if song in top_songs:
                    #Get the song number in top songs to add to the right list
                    song_index = top_songs.index(song)
                    songlist = list(show_song_list)
                    #Add the placement and date to the right song position list
                    placement_tuple = (songlist.index(song)/len(show_song_list),date)
                    song_position_lists[song_index].append(placement_tuple)
            #New songs compared to the previous show
            new_songs = set(show_song_list) - set(prev_show_list)

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
    new_show_songs_df.columns=["NumberNewSongs", 'PercentSongsNew','NewSongs']
    new_show_songs_df.index.names = ['Date']
    new_show_songs_df2 = pd.DataFrame.from_dict(new_show_songs_dict2).T
    new_show_songs_df2.columns=["NumberNewSongs", 'PercentSongsNew','NewSongs']
    new_show_songs_df2.index.names = ['Date']
    new_show_songs_df3 = pd.DataFrame.from_dict(new_show_songs_dict3).T
    new_show_songs_df3.columns=["NumberNewSongs", 'PercentSongsNew','NewSongs']
    new_show_songs_df3.index.names = ['Date']
    pd.set_option('max_columns', None)
    #Join dicts for graph stacking
    new_show_songs_23_df = new_show_songs_df2.join(new_show_songs_df3, lsuffix='_2', rsuffix='_3')
    new_show_songs_overall_df = new_show_songs_df.join(new_show_songs_23_df)
    new_show_songs_overall_df['TotPerc'] = new_show_songs_overall_df['PercentSongsNew'] + new_show_songs_overall_df['PercentSongsNew_2'] + new_show_songs_overall_df['PercentSongsNew_3']
    new_show_songs_overall_df['Total Percent'] = new_show_songs_overall_df['TotPerc'].astype(float)
    new_show_songs_overall_df['Rolling Average'] = new_show_songs_overall_df['Total Percent'].rolling(window=10).mean()
    rolling_avs = new_show_songs_overall_df['Rolling Average'].values
    total_new_song_av = new_show_songs_overall_df['Total Percent'].values.mean()
    print(total_new_song_av)

    #Turn new year songs dict into a df
    new_year_songs_df = pd.DataFrame.from_dict(new_year_songs_dict).T
    new_year_songs_df.columns=["NumberNewSongs", 'Percent of Songs New','NewSongs']
    new_year_songs_df.index.names = ['Date']
    years = new_year_songs_df.index.values
    percents_year_list = list(new_year_songs_df['Percent of Songs New'].values)
    percents_year_list.pop(0)
    year_percents_avg = sum(percents_year_list)/len(percents_year_list)
    print(year_percents_avg)

    #Create graph for show gaps
    show_gaps = ['NumberNewSongs','NumberNewSongs_2','NumberNewSongs_3']
    show_gaps_perc = ['PercentSongsNew','PercentSongsNew_2','PercentSongsNew_3']
    legend_perc = ['% Songs Not Played in Previous Show', "% Songs Not Played in Last Two Shows", "% Songs Not Played  in Last Three Shows"]
    legend_num = ['# Songs Not Played in Previous Show', "# Songs Not Played in Last Two Shows", "# Songs Not Played  in Last Three Shows"]

    source_snsg = ColumnDataSource(new_show_songs_overall_df)

    show_new_songs_perc_graph = figure(y_range=list(dates), title="Percentage of Songs in a Show That Hadn't Been Played Recently", plot_height=900, plot_width=1000,
              toolbar_location=None, tooltips = [("Date", "@Date"), ("Not Played Prev Show",'@NewSongs') , ("2 Show Gap", "@NewSongs_2"), ('3 Show Gap','@NewSongs_3')])
    show_new_songs_perc_graph.hbar_stack(show_gaps_perc, y='Date', width=0.9, source=source_snsg, legend_label=legend_perc, color=["#ffeda0", "#feb24c", "#f03b20"])
    show_new_songs_perc_graph.xgrid.grid_line_color = None
    show_new_songs_perc_graph.ygrid.grid_line_color = None
    show_new_songs_perc_graph.yaxis.major_label_text_font_size = '0pt'
    show_new_songs_perc_graph.yaxis.major_tick_line_color = None  # turn off x-axis major ticks
    show_new_songs_perc_graph.yaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    show_new_songs_perc_graph.yaxis.axis_label = '(<-Most Recent)           All Shows Played           (Earliest Shows->)'
    show_new_songs_perc_graph.xaxis[0].formatter = NumeralTickFormatter(format="0%")
    show_new_songs_perc_graph.add_layout(show_new_songs_perc_graph.legend[0], 'right')
    show_new_songs_perc_graph.legend.click_policy = "hide"
    show_new_songs_perc_graph.legend.title = 'Click on Legend to Hide Individual Sections'
    show_new_songs_perc_graph.line(y=dates_asc, x=rolling_avs, line_width=3)

    #Total instead of percent
    show_new_songs_num_graph = figure(y_range=dates_asc, title="Number of Songs in a Show That Hadn't Been Played Recently", plot_width=1400,
              toolbar_location=None, tooltips=[("Date", "@Date"), ("Not Played Prev Show",'@NewSongs') , ("2 Show Gap", "@NewSongs_2"), ('3 Show Gap','@NewSongs_3')])

    show_new_songs_num_graph.hbar_stack(show_gaps, y='Date', width=0.9, source=source_snsg, legend_label=legend_num, color=["blue", "yellow", "red"])
    years_asc = years[::-1]
    #Create graph for new songs per years
    source_ynsg = ColumnDataSource(new_year_songs_df)
    year_new_songs_graph = figure(y_range=years_asc, plot_height=600, title="% of Songs Played Each Year That Weren't Played the Year Before",
              toolbar_location=None, tooltips=[("# of Songs Not Play Previous Year", "@NumberNewSongs"), ("New Songs", "@NewSongs")])
    year_new_songs_graph.hbar(y='Date', right='Percent of Songs New', height=0.9, source=source_ynsg, color='#2b8cbe')

    year_new_songs_graph.xaxis[0].formatter = NumeralTickFormatter(format="0%")


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

    source_top = ColumnDataSource(percent_of_shows_df)
    top_songs_percent_graph = figure(y_range=top_songs_w_avg, title="Percentage of Shows Where Most Popular Songs Were Played",
              toolbar_location=None, tooltips=[('Percent','@Percent'),("Times Played", "@TimesPlayed"), ("Shows Since Debut",'@ShowsSinceDebut') , ("Debut Date", "@DebutDate")])

    top_songs_percent_graph.hbar(y='song', right='Percent', height=0.9, source=source_top, color = '#2b8cbe')
    top_songs_percent_graph.xaxis[0].formatter = NumeralTickFormatter(format="0%")
    top_songs_percent_graph.circle(x=1,y=0)

    #Create graph for placement of top 10 songs
    #Turn placement lists into df
    placement_df = pd.DataFrame(columns=['song','placement','date'])
    for index, placement_list in enumerate(song_position_lists):
        for placement in placement_list:
            x = (top_songs[index],placement[0],placement[1])
            x_series = pd.Series(x, index = ['song','placement','date'])
            placement_df = placement_df.append(x_series, ignore_index = True)

    stdev_of_positions = []
    for placement_list in song_position_lists:
        stdev_of_positions.append(statistics.pstdev([x[0] for x in placement_list]))
    avg_std_dev_placement = statistics.mean(stdev_of_positions)


    #Create color coding for placement
    placement_df['year'] = placement_df['date'].str[-4:].astype(int)
    placement_df['Percent Whole'] = round(placement_df['placement']*100,2)
    placement_df['hover'] = placement_df['Percent Whole'].astype(str) + '% into Show'
    years = placement_df['year'].values
    mapper = linear_cmap(field_name='year', palette=RdYlBu11, low=min(years), high=max(years))

    source_place = ColumnDataSource(placement_df)
    top10_placement = figure(y_range=top_songs, title='Placement of Top 10 Most Played Songs', tooltips=[('Date',"@date"), ('Show Placement',"@hover")])
    top10_placement.circle(x='placement', y=jitter('song', width=0.4, range=top10_placement.y_range), radius=0.01, fill_alpha=0.6, source=source_place,
             color=mapper)
    color_bar = ColorBar(color_mapper=mapper['transform'], width=8, location=(0, 0))
    top10_placement.add_layout(color_bar, 'right')
    top10_placement.xaxis.ticker = [0, 0.5, 1]
    top10_placement.xaxis.major_label_overrides = {0: "Start of Show", 0.5: 'Middle of Show', 1: "End of Show", }
    top10_placement.circle(x=1,y=0)

    all_metrics = [total_new_song_av, avg_of_top_ten, year_percents_avg, avg_std_dev_placement]
    print(all_metrics)
    return show_new_songs_perc_graph, show_new_songs_num_graph, year_new_songs_graph, top_songs_percent_graph, top10_placement

graph1_vw, graph2_vw, graph3_vw, graph4_vw, graph5_vw = get_graphs('gratefuldead.json')

tab1 = Panel(child=graph1_vw, title="Show Gaps (%)")
tab2 = Panel(child=graph2_vw, title="Show Gaps (#)")
tab3 = Panel(child=graph3_vw, title="News Songs Per Year")
tab4 = Panel(child=graph4_vw, title="Top Songs Percent Played")
tab5 = Panel(child=graph5_vw, title="Top Songs Placement")

show(Tabs(tabs=[tab1,tab3,tab4,tab5]))

descriptions = ['Avg. percent of songs new each show', "Avg percent of shows top ten songs played (flip)", 'Avg % of songs per year not played prev year', 'Song Placement Variance Index']
vw_stats = ['Vampire Weekend', 0.16925978299549443, 0.8357536900860533, 0.3626107440839584, 0.16340568993761634]
af_stats = ['Arcade Fire', 0.1809164150103507, 0.7728686844882828, 0.4607002026828122, 0.2081494379861986]
bk_stats = ['Beck', 0.36055240017627993, 0.6546428360359876, 0.46314365942453123, 0.16574583438214688]
pj_stats = ['Pearl Jam', 0.4753179769170513, 0.7097834349492785, 0.39745100370919134, 0.14139250373148385]
ph_stats = ['Phish', 0.8671887131572218, 0.3017136475638559, 0.33022898420848007, 0.14663954130502976]
vw_fix = 1-vw_stats[2]
af_fix = 1-af_stats[2]
bk_fix = 1-bk_stats[2]
pj_fix = 1-pj_stats[2]
ph_fix = 1-ph_stats[2]
vw_stats[2] = vw_fix
af_stats[2] = af_fix
bk_stats[2] = bk_fix
pj_stats[2] = pj_fix
ph_stats[2] = ph_fix

metrics_desc = ['Band','Show', 'Top 10 Played', 'Year', 'Placement']
mets = ['Show', 'Top 10 Played', 'Year', 'Placement']
bands = ['Vampire Weekend', 'Arcade Fire', 'Beck', 'Pearl Jam', 'Phish']
stats_list = [vw_stats, af_stats, bk_stats, pj_stats, ph_stats]
metrics_df = pd.DataFrame(columns=metrics_desc)
for statlist in stats_list:
    stat_series = pd.Series(statlist, index=metrics_desc)
    metrics_df = metrics_df.append(stat_series, ignore_index=True)

print(metrics_df)
source_met = ColumnDataSource(metrics_df)
metrics_graph = figure(y_range=bands, title="Number of Songs in a Show That Hadn't Been Played Recently",
                                  plot_width=1400,
                                  toolbar_location=None)

metrics_graph.hbar_stack(mets, y='Band', width=0.9, source=source_met, legend_label=mets,
                                    color=["blue", "yellow", "red", 'green'])

#show(metrics_graph)

