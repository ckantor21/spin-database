# SPOTIFY SPIN DATABASE
#### Video Demo: https://www.youtube.com/watch?v=wRInCR1qQ4M
#### Description:

The purpose of this project is to take data from Spotify Web API for a specific user (me) and create a web database containing playlist information using a combination of Python (with Flask for web development), HTML/CSS (with Jinja for Flask integration), and SQLite to store information.

This project is especially meaningful to me as it is something I will actually use for my work. As a spin instructor, I am constantly creating playlists for my classes, and this project allows me to keep track of the music I have used, particularly the number of times I use songs and artists, and when I first created/used each playlist. 

I view this project as a continuous work in progress, as it can continue to be improved and refined for quicker processing and expanded capabilities.

#### Functionality:

Inside the project folder is app.py, the main file for Flask to pull the API data, create the database, and render the templates for each webpage. There is also a spin.db file, the SQLite database that contains 3 tables - playlists, tracks, and artists. Inside the static folder is styles.css, which contains a few important details such as brand colors for Spotify to use for displaying text on the website. The templates folder contains html files that utilize Jinja formatting in order to pass information from the database to the webpages to be displayed.

##### APP.PY:

app.py begins by initializing the connection to the Spotify Web API. Secret credentials are necessary in order to complete this connection, which in the testing phase were passed literally, but in the presentation stage can be passed as environment variables in order to preserve security. This connection is achieved using a Python package called spotipy, which returns JSON objects for further use in code.

Unfortunately, spotipy is limited to pulling only 50 playlists at a time. Considering I have, as of writing, well over 200 active playlists, pulling all of them required the repetition of the spotipy user_playlists call, using the *offset* parameter to pull 50 playlists at a time, until all playlists have been pulled. Playlist titles are checked against a regular expression (using the *re* library) in order to separate only playlists relevant to this project.

The next section of code extracts significant amounts of data from the playlists to create dictionaries of information for use in passing to the SQLite database. The playlist table stores playlist ids, playlist titles, playlist dates, and playlist lengths. The tracks table stores track ids, track titles, track artists, and track counts (more on that shortly). The artist table stores artist names and artist counts.

After the add_playlist function has been called on each group of up to 50 playlists, that data must be cleaned/counted before it can be stored into the SQLite database. At this time, the number of times each track is used is stored using a Counter object (from the *collections* library) and double-checked for duplicates. A similar process is used for counting the number of times each artist has been played across all playlists.

Finally, the SQLite database can be created, as information from the dictionaries is stored into the relevant tables. Once the data is in its appropriate table, a series of SELECT statements can be used in each of the html templates in order to pull the data for display on the webpage.

No distinction is necessary between "GET" and "POST" requests for this project as there is no online login function required, since this is a personal project designed to display data from my Spotify account. An initial login is required on first initialization through Spotify in order to pull user credentials.

#### Stylistic Notes:

Most of the CSS used in this project originates from Bootstrap, via the base formatting used in CS50's Week 9 Problem Set (Finance). Future iterations of this project might continue to improve the formatting and stylistic choices for a more personal touch; however, as my main focus in this intial stage was to have a functional website with an emphasis on the python-based back-end, I was willing to compromise on certain stylistic options.

Additionally, I would like to implement a feature to incorporate album artwork into the project for display on relevant webpages. This is part of the JSON track object data that can be pulled from Spotify Web API.

#### Acknowledgements:

Immense credit for the success of this project is due to Harvard's CS50x Team, for creating an incredible course that pushed me to explore a new field and challenged me all along the way without pushing me to give up.

I also appreciate the work of many developers whose libraries, functionalities, and other pre-existing components I was able to leverage to make this project, especially spotipy.

Finally, I am quickly realizing how collaborative the programming community is, and I am thankful that resources like w3schools.net and Stack Overflow exist to provide tutorials and in-depth answers to specific questions.