import urllib.request
import os

# Create the data folder if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# The correct URL for the file
url = 'https://raw.githubusercontent.com/datakind/datakind-chi/main/geographies/chicago_community_areas.geojson'

# The path where we want to save the file
save_path = os.path.join('data', 'chicago-community-areas.geojson')

print(f"Downloading blueprint file...")

try:
    # Use urllib to download the file from the url and save it to the specified path
    urllib.request.urlretrieve(url, save_path)
    print(f"Success! File saved correctly in your 'data' folder.")
except Exception as e:
    print(f"An error occurred: {e}")