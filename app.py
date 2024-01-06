
from flask import Flask, request, url_for, session, redirect, render_template, flash
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import logging
import base64
import spotipy  
import pandas as pd
import time
import random
import os


#adjustable global variables

TIMERANGE = 'medium_term', #time range for the top artists and tracks, long = several years, medium = last 6 months
LIMIT_TOP_ARTIST = 20       #how many top_artists are found
LIMIT_TOP_TRACKS = 100       #how many top_tracks are found
LIMIT_RECOMMENDED_TRACKS = 15
RANDOM_TRACKS= 5
NUM_SONGS_RECOMMENDED = 12 #number of songs recommended through spotify api



app = Flask("recommendation app")

app.secret_key = "Something Random"
app.config['SESSION_COOKIE_NAME'] = 'Cookie'


CLIENT_ID = '<dummy_Client_ID>'
CLIENT_SECRET = '<dummy_CLIENT_SECRET>'


# Base64 encode the client ID and client secret
client_credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
client_credentials_base64 = base64.b64encode(client_credentials.encode())

#request access token
token_url = 'https://accounts.spotify.com/api/token'

TOKEN_INFO = "token_info" 



@app.route('/',methods=['GET','POST'])
def login():
    ''' if request.method == "POST": #player pressed button
        songs_dict,chosen_tracks = getRecommendations() #get recommendations

        session['recommended_songs'] = songs_dict #store variables in current session
        session['chosen_tracks'] = chosen_tracks

      
        #redirect to page, for displaying result
        return redirect(url_for('result_page',_external=True))
    else:
        return render_template('button_page.html')'''
    if request.method == "POST": #user pressed button, to go to the auth page
        sp_oath = create_spotify_oauth()
    
        auth_url = sp_oath.get_authorize_url()

        print(f"Auth URL: {auth_url}")
        return redirect(auth_url) #redirect user to authentication url
    
    return render_template('login_page.html')

    print("\n\n\nAT LOGIN PAGE\n\n\n")
   

#after authenticating users get here
@app.route('/redirect')
def redirectPage():
    sp_oath = create_spotify_oauth()
    session.clear() #clear any potential other sessions 
    code = request.args.get('code') 
    token_info = sp_oath.get_access_token(code)
    session[TOKEN_INFO] = token_info #saving token information (accesstoken,refresh token,expiresAt) in the current session 
    print("\n\nDebug1\n\n")
    user_name = getName()
    session['username'] = user_name
    
    return redirect(url_for('button_page', _external=True))

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()


    #remove cached file for cookie and access token
    cache_file = ".cache"
    if os.path.exists(cache_file):
        os.remove(cache_file)
    
    # Redirect to the login page
    return redirect(url_for('login', _external=True))



@app.route('/button_page', methods=['GET', 'POST'])
def button_page():
    if request.method == "POST":
        print("Handling POST request")
        getName()
        
        while True:
            songs_dict, chosen_tracks = getRecommendations()

            if songs_dict is not None:
                print("Recommendations retrieved")
                break
            else:
                print("Unable to retrieve recommendations. Retrying in 3 seconds...")
                time.sleep(3)  # Add a delay before retrying
    

        
        
        session['recommended_songs'] = songs_dict
        session['chosen_tracks'] = chosen_tracks

        
        return redirect(url_for('result_page', _external=True))
    else:
        return render_template('button_page.html',username=session['username'])
    

@app.route('/result_page', methods=['GET','POST'])
def result_page():
    if request.method == "POST": #player wants new recommendations
        time.sleep(1)
        # Clear the session data if needed
        session['recommended_songs'] = None
        session['chosen_tracks'] = None
        return redirect(url_for('button_page'),_external=True)  
    else:

               
        songs_dict = session.get('recommended_songs')
        chosen_tracks = session.get('chosen_tracks')
        
        songs_list = [(index, (track_name, track_info)) for index, (track_name, track_info) in enumerate(songs_dict.items())] #enumerate the list of songs, so I can properly have 3 songs in 1 row

        
        if songs_dict is None or chosen_tracks is None:
            # Data not present, flash an error message
            flash('error', 'No data available. Redirecting to recommendation page...')
            time.sleep(1)
            # Clear the session data if needed
            session['recommended_songs'] = None
            session['chosen_tracks_name'] = None
            return redirect(url_for('button_page',_external=True))

        


        return render_template('result_page.html',songs_list = songs_list, chosen_tracks = chosen_tracks)




 




#returns a Tuple containing:
# 1. dictionaries with key = trackname, value = dictionary with elements {artists,track_id,track_img}
# 2. names of the 5 sample songs, the recommendation system utilized
# 3 (imgs of all recommended songs or add it in the dictionary)
def getRecommendations():
    try:
        print("Retrieving token information\n")
        token_info = get_token() #refresh token or authenticate again if needed
        print("token information retrieved!\n")
    except:
        print("User not logged in")
        return(redirect(url_for("login",_external=False)))
        


    sp = spotipy.Spotify(auth=token_info['access_token']) #create spotify api client

    print("Getting User's top items")
    #get user's top items
    #top_artists_info = sp.current_user_top_artists(limit=LIMIT_TOP_ARTIST, time_range=TIMERANGE)['items']
    #top_tracks_info = sp.current_user_top_tracks(limit=LIMIT_TOP_TRACKS,time_range=TIMERANGE)['items']
       # Number of retries
    
    #retrying since sometimes connection is reset by spotify api
    max_retries = 3

    for retry in range(max_retries):
        try:
            print("Getting User's top items")
            # get user's top items
            top_artists_info = sp.current_user_top_artists(limit=LIMIT_TOP_ARTIST, time_range=TIMERANGE)['items']
            top_tracks_info = sp.current_user_top_tracks(limit=LIMIT_TOP_TRACKS, time_range=TIMERANGE)['items']
            
            # Break out of the loop if successful
            break
        except Exception as e:
            print(f"Error getting top items: {e}")
            
            if retry < max_retries - 1:
                # Retry if there are more retries remaining
                print(f"Retrying ({retry + 1}/{max_retries})...")
                time.sleep(2)  # Add a small delay before retrying
            else:
                # Max retries reached, handle the error as needed
                print("Max retries reached. Unable to retrieve top items.")
                return None ,None#invalid return value
    

    top_artists = []
    for artist_info in top_artists_info:
        top_artists.append(artist_info)

        #print(artist_info['name'])
        #print(artist_info['genres'])

    top_tracks = []
    for track_info in top_tracks_info:
        top_tracks.append(track_info)
        #print(f"Track name: {track_info['name']}")
        track_artists = [artist['name'] for artist in track_info['artists']]

        #print(f"Track artists: {track_artists}")


    #chosen_artist_id,chosen_artist_name = choose_artist(top_artists) #get random top_artist id for recommendation


    
    chosen_tracks_dict = choose_tracks(top_tracks)
    chosen_tracks_id = list(chosen_tracks_dict.keys())
    chosen_tracks = list(chosen_tracks_dict.values())
    
    print("Getting recommendations\n")
    recommendations_info = sp.recommendations(seed_tracks=chosen_tracks_id,limit=NUM_SONGS_RECOMMENDED)
    recommended_tracks_dict = {} #dict to store recommended songs name['key] - and artist name
    for track in recommendations_info['tracks']:
        track_artists = [artist['name'] for artist in track['artists']]
        track_name = track['name']
        track_img_url = track['album']['images'][0]['url']
        track_id = track['id']
        recommended_tracks_dict[track_name] = {
            'artists':  track_artists,
            'track_id': track_id,
            'track_img':track_img_url
        }


    #TODO: get the users playlist, songs in here shouldn't be recommended twice
    #playlists = sp.current_user_playlists(limit=15)['items']

    #playlist_tracks_hrefs = []

    #for num,playlist in enumerate(playlists):
        #playlist_tracks_hrefs.append(playlist['href'])
        #print(f"Playlist {num}'s name: {playlist['name']}")
    
    #print(playlist_tracks_hrefs)

    return (recommended_tracks_dict,chosen_tracks)
           
#@return a string of the spotify user's username; 
#returns default value of "User" if failed
def getName():
    try:
        print("Retrieving token information\n")
        token_info = get_token() #refresh token or authenticate again if needed
        print("token information retrieved!\n")
    except:
        print("User not logged in")
        return(redirect(url_for("login",_external=False)))
        


    sp = spotipy.Spotify(auth=token_info['access_token']) #create spotify api client
    
    

    max_retries = 10

    for retry in range(max_retries):
        try:
            info = sp.current_user()
            print(info['display_name'])
            
            # Break out of the loop if successful
            return info['display_name']
        except Exception as e:
            print(f"Error getting user info: {e}")
            
            if retry < max_retries - 1:
                # Retry if there are more retries remaining
                print(f"Retrying ({retry + 1}/{max_retries})...")
                time.sleep(1)  # Add a small delay before retrying
            else:
                # Max retries reached, handle the error as needed
                print("Max retries reached. Unable to retrieve top items.")
                return "User" #invalid return value
    


#check if there is any token, or if access token has expired
def get_token():
    token_info = session.get(TOKEN_INFO, None) #try to get the token_info from the session 
    if not token_info: #token_info doesn't exist yet
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now<60

    if(is_expired):
        sp_oauth = create_spotify_oauth()
        token_info =  sp_oauth.refresh_access_token(token_info['refresh_token'])
        #refresh token information
    return token_info
    
#randomly chooses 1 artist from list of top artists and returns tuple = id, name
def choose_artist(top_artists):
    chosen_artist = random.choice(top_artists)
    return (chosen_artist['id'],chosen_artist['name'])

#randomly chooses RANDOM_TRACKS amount of tracks from the user's top tracks and returns dict
#dict:
#key- track_id
#value - track_name, list of trackartists
def choose_tracks(top_tracks):
    chosen_tracks = random.sample(top_tracks,RANDOM_TRACKS)
    track_dict = {}

    for track in chosen_tracks:
        
        track_artists = [artist['name'] for artist in track['artists']]
        track_dict[track['id']] = (track['name'],track_artists)

   
    
    return track_dict


def create_spotify_oauth():
    return SpotifyOAuth(        
        client_id=CLIENT_ID,
        client_secret= CLIENT_SECRET,
        redirect_uri = url_for('redirectPage', _external=True),
        scope="user-library-read, user-top-read",
        show_dialog=True
        )


