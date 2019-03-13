from urllib.request import urlopen, Request
import pygame, sys, time, io
from bs4 import BeautifulSoup

""" URLLIB HEADER"""
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Connection': 'keep-alive'}

""" PYGAME SETTINGS """
#Initializes the Clock
clock = pygame.time.Clock()
FPS = 60

SCREEN_WIDTH, SCREEN_HEIGHT = 900, 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

bg_color = (250, 248, 239)

screen.fill(bg_color)


# Sets the window name
pygame.display.set_caption("Torrent Search")
# Draws all changes to the window


"""
                        WEBSITES
                    ----------------

Movies
-------
YIFY: https://yts.am/browse-movies/Search%20term%20here/all/all/0/latest        # Spaces = %20

TV Shows
--------
EZTV: 

Movies and TV shows
-------------------
TPB: 
KAT: 
RAR:

                        FEATURES
                    ----------------

Feature List:
    - ** Check if the MEDIA-SERVER pc is available **       possibly with os.path.exists(path_to_media_server)
    - ** Next Check if PLEX is up and active **
    
    - At the start of the program, make sure the URLs are accessible since the websites change domains often
    
    - Browse option to browse all movies from YIFY (latest, name, etc)
    
    - Auto-format TV show search terms (e.g. S__E__)
    - Automatically set download path when choosing to search for either a Movie of TV Show
    
    - Websites other than YIFY, show: Description, File Size, Seeders
        - Have a checkbox to choose "extensive search" to check other websites

Site Specific Features
-----------------------
YIFY:
    - Resolution selector when downloading
"""

# Array of Movie objects
movies = []

""" Link Definintions """
yify = lambda name: 'https://yts.am/browse-movies/' + name.replace(" ", "%20") + '/all/all/0/latest'

class Movie:
    def __init__(self, name, link, img_link):
        self.name = name
        self.link = link
        self.image = pygame.image.load(io.BytesIO(urlopen(img_link).read()))
        self.img_size = (160, 240)
        # Default image size is 230 x 345, Change it to 150 x 225
        self.image = pygame.transform.smoothscale(self.image, self.img_size)


# Check to make sure the link is open
# This is necessary in case the domain changes. Need to check all URLs are valid at start of program!
try:
    start = time.clock()
    #req = Request(yify("Alice in Wonderland"), headers=hdr)
    #req = Request(yify("the"), headers=hdr)
    req = Request(yify("Games"), headers=hdr)
    html = urlopen(req)
    soup = BeautifulSoup(html.read(), 'html.parser')
except:
    print("That is an invalid URL")
else:
    #print(soup.prettify())
    print("Time to retrieve Page: %.2fs" %(time.clock() - start))


raw_data = soup.findAll('div', class_="browse-movie-wrap")
start = time.clock()
if len(raw_data) > 0:
    # Limit the number of movies to load
    if len(raw_data) > 12:
        raw_data = raw_data[:12]
    print (len(raw_data), "Results Found\n----------------")
    for movie in raw_data:
        movies.append(Movie(movie.find("img")['alt'][:-9], movie.find("a")['href'], movie.find("img")['src']))
        print(movie.find("img")['alt'][:-9])
        # Link
        print(movie.find("a")['href'])
        # Picture
        print(movie.find("img")['src'])
        print()

    print(time.clock() - start, '\nAvg per movie %.2fs' % ((time.clock() - start) / len(movies)))


else:
    print("No Movies Found")

def show_movies():
    num_cols = 4
    top_padding = 120
    for movie in range(len(movies)):
        if movie < num_cols:
            screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+10)* num_cols))/2 + movie * (movies[movie].img_size[0]+10), top_padding))
        elif movie >= num_cols and movie < num_cols*2:
            screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+10)* num_cols))/2 + (movie - num_cols) * (movies[movie].img_size[0]+10), top_padding + (movies[movie].img_size[1]+10)))
        else:
            screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+10)* num_cols))/2 + (movie - num_cols*2) * (movies[movie].img_size[0]+10), top_padding + 2*(movies[movie].img_size[1]+10)))

running = True
while running:
    pygame.draw.rect(screen, (40,40,40), (0,0,SCREEN_WIDTH,80))
    if movies:
        show_movies()

    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.update()