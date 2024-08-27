from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
from datetime import datetime, timedelta

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers = headers, data = data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"
    query_url = url + query
    result = get(query_url, headers = headers)
    json_result = json.loads(result.content)["artists"]["items"]
    if len(json_result) == 0:
        print("no artist with name")
        return None
    return json_result[0]

def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers = headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def search_for_track(token, track_name, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q=track:{track_name} artist:{artist_name}&type=track&limit=1"
    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["tracks"]["items"]
    if len(json_result) == 0:
        print("No track found with the specified track and artist name")
        return None
    return json_result[0]

def get_recommended_tracks(token, seed_track_id, limit=10):
    url = "https://api.spotify.com/v1/recommendations"
    headers = get_auth_header(token)
    params = {
        "seed_tracks": seed_track_id,
        "limit": limit,
    }
    result = get(url, headers=headers, params=params)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def get_recommended_tracks_less_popular(token, seed_track_id, limit=10, max_popularity = 50):
    url = "https://api.spotify.com/v1/recommendations"
    headers = get_auth_header(token)
    params = {
        "seed_tracks": seed_track_id,
        "limit": limit,
        "max_popularity": max_popularity
    }
    result = get(url, headers=headers, params=params)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def get_time_range(release_date, years_range=2.5):
    release_date_obj = datetime.strptime(release_date, "%Y-%m-%d")
    min_date = release_date_obj - timedelta(days=int(365.25 * years_range))
    max_date = release_date_obj + timedelta(days=int(365.25 * years_range))
    return min_date.strftime("%Y-%m-%d"), max_date.strftime("%Y-%m-%d")

def get_recommended_tracks_same_time(token, seed_track_id, release_date, limit=10, max_popularity=50):
    min_release_date, max_release_date = get_time_range(release_date, years_range=5)
    
    url = "https://api.spotify.com/v1/recommendations"
    headers = get_auth_header(token)
    params = {
        "seed_tracks": seed_track_id,
        "limit": limit,
        "max_popularity": max_popularity,  
        "min_release_date": min_release_date,
        "max_release_date": max_release_date #within given time frame
    }
    result = get(url, headers=headers, params=params)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def get_recommended_tracks_by_mood(token, seed_track_id, energy, valence, danceability, limit=10):
    url = "https://api.spotify.com/v1/recommendations"
    headers = get_auth_header(token)
    params = {
        "seed_tracks": seed_track_id,
        "limit": limit,
        "target_energy": energy,
        "target_valence": valence,
        "target_danceability": danceability
    }
    result = get(url, headers=headers, params=params)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def get_artist_genres(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result.get("genres", [])

def get_recommended_tracks_by_genre(token, seed_genres, limit=10):
    url = "https://api.spotify.com/v1/recommendations"
    headers = get_auth_header(token)
    params = {
        "seed_genres": ",".join(seed_genres),
        "limit": limit
    }
    result = get(url, headers=headers, params=params)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def create_playlist_for_user(token, user_id, track_uris, playlist_name="Custom Playlist"):
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers = get_auth_header(token)
    data = json.dumps({
        "name": playlist_name,
        "description": "A custom playlist generated by the recommendation system",
        "public": False
    })
    response = post(url, headers=headers, data=data)
    playlist_id = json.loads(response.content)["id"]
    
    # Add tracks to the playlist
    add_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    add_tracks_data = json.dumps({"uris": track_uris})
    post(add_tracks_url, headers=headers, data=add_tracks_data)
    return playlist_id

def get_influenced_tracks(token, seed_artist_id, limit=10):
    # Get related artists
    url = f"https://api.spotify.com/v1/artists/{seed_artist_id}/related-artists"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    related_artists = json.loads(result.content)["artists"]
    
    # Get the IDs of the first 5 related artists
    related_artist_ids = [artist["id"] for artist in related_artists[:5]]
    
    # Get tracks recommended based on these related artists
    return get_recommended_tracks_by_artists(token, related_artist_ids, limit)

def get_recommended_tracks_by_artists(token, artist_ids, limit=10):
    url = "https://api.spotify.com/v1/recommendations"
    headers = get_auth_header(token)
    params = {
        "seed_artists": ",".join(artist_ids),
        "limit": limit
    }
    result = get(url, headers=headers, params=params)
    json_result = json.loads(result.content)["tracks"]
    return json_result
token = get_token()
result = search_for_artist(token, "blood orange")

# print artist from search_for_artist
#print(result["name"])
#artist_id = result["id"]
#songs = get_songs_by_artist(token, artist_id)

# print list of most popular songs
#for idx, song in enumerate(songs):
    #print(f"{idx+1}. {song['name']}")

#print track from search_for_tracks
track_name = "Here Comes The Sun"
artist_name = "The Beatles"
track_result = search_for_track(token, track_name, artist_name)

if track_result:
    track_id = track_result["id"]
    artist_id = track_result["artists"][0]["id"]
    release_date = track_result['album']['release_date']
    print(f"\nTrack Details:")
    print(f"Track Name: {track_result['name']}")
    print(f"Artist: {track_result['artists'][0]['name']}")
    print(f"Album: {track_result['album']['name']}")
    print(f"Release Date: {track_result['album']['release_date']}")

#less popular recommendations
recommended_tracks = get_recommended_tracks_less_popular(token, track_id, limit=10, max_popularity=50)
print("\nRecommended Tracks that are less Popular:")
for idx, track in enumerate(recommended_tracks):
    print(f"{idx + 1}. {track['name']} by {track['artists'][0]['name']} from album '{track['album']['name']}'")


recommended_tracks = get_recommended_tracks_same_time(token, track_id, release_date, limit=10, max_popularity=100)
print("\nRecommended Tracks within ±5 Years:")
for idx, track in enumerate(recommended_tracks):
    print(f"{idx + 1}. {track['name']} by {track['artists'][0]['name']} from album '{track['album']['name']}'")

genres = get_artist_genres(token, artist_id)
print(f"Genres for the artist '{artist_name}': {genres}")
if genres:
    recommended_tracks_by_genre = get_recommended_tracks_by_genre(token, genres, limit=10)
    print("\nRecommended Tracks By Genres:")
    for idx, track in enumerate(recommended_tracks_by_genre):
        print(f"{idx + 1}. {track['name']} by {track['artists'][0]['name']} from album '{track['album']['name']}'")
else:
    print("No genres found for the artist.")

influenced_tracks = get_influenced_tracks(token, artist_id, limit=10)
print("\nInfluenced Tracks Based on Related Artists:")
for idx, track in enumerate(influenced_tracks):
    print(f"{idx + 1}. {track['name']} by {track['artists'][0]['name']} from album '{track['album']['name']}'")