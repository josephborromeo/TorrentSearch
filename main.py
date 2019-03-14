from urllib.request import urlopen, Request
import pygame, sys, time, io, os
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
pygame.init()
pygame.key.set_repeat(500, 35)
# Sets the window name
pygame.display.set_caption("Torrent Search")
# Draws all changes to the window


"""
                        WEBSITES
                    ----------------

Movies
-------
YIFY: https://yts.am/browse-movies/Search%20term%20here/all/all/0/latest        # Spaces = %20


Movies and TV shows
-------------------
TPB: https://thepiratebay.org/search/Search%20term%20here
RAR: http://rarbg.to/torrents.php?search=search+term+here

    --- Not using KAT since you cannot eaily dl magnet link ---
KAT: https://kat2.biz/usearch/search%20term/
EZTV: Just not a good selection

                        FEATURES
                    ----------------

Feature List:
    - ** Check if the MEDIA-SERVER pc is available **                                                                   - DONE!
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

"""     STATUS CHECKS       """
def check_statuses():
    pc, plex = False, False
    if os.path.exists("//MEDIA-SERVER/E"):
        pc = True
    # TODO: Secondary check for plex
    return pc, plex

print(check_statuses())

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


def search_yify(name):
    print("SEARCHING")
    # Check to make sure the link is open
    # This is necessary in case the domain changes. Need to check all URLs are valid at start of program!
    # FIXME: This method is pretty slow and takes between 0.5s - 0.6s PER movie :( - Must make faster
    movies = []
    try:
        start = time.clock()
        req = Request(yify(str(name)), headers=hdr)
        #req = Request(yify("the"), headers=hdr)
        #req = Request(yify("transformers"), headers=hdr)
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
        return movies
    else:
        movies = [None]
        print("No Movies Found")
        return movies

def show_movies():
    # NEED TO ADD MOVIE TITLES
    num_cols = 4
    top_padding = 120
    if movies[0] == None:
        screen.fill(bg_color)
        draw_header()
        text = pygame.font.SysFont("Roboto", 72).render("No Movies Found", True, (240, 30, 15))
        screen.blit(text, (((SCREEN_WIDTH - text.get_width())/2), 150))
        del(movies[0])
    else:
        screen.fill(bg_color)
        draw_header()
        for movie in range(len(movies)):
            if movie < num_cols:
                screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+10)* num_cols))/2 + movie * (movies[movie].img_size[0]+10), top_padding))
            elif movie >= num_cols and movie < num_cols*2:
                screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+10)* num_cols))/2 + (movie - num_cols) * (movies[movie].img_size[0]+10), top_padding + (movies[movie].img_size[1]+10)))
            else:
                screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+10)* num_cols))/2 + (movie - num_cols*2) * (movies[movie].img_size[0]+10), top_padding + 2*(movies[movie].img_size[1]+10)))


class InputBox:

    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (100,100,100)
        self.color_active = (200,200,200)
        self.text_color = (0,0,0)
        self.text = text
        self.font = pygame.font.SysFont("Times New Roman", 30)
        self.txt_surface = self.font.render(self.text, True, self.color_inactive)
        self.active = False
        self.movies = []

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                if not self.active and self.text == 'Search':
                    self.text = ''
                    self.txt_surface = self.font.render(self.text, True, self.text_color)
                self.active = not self.active
            else:
                if self.active and self.text == '':
                    self.text = 'Search'
                    self.txt_surface = self.font.render(self.text, True, self.color_inactive)
                self.active = False
            # Change the current color of the input box.
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    print(self.text)
                    self.movies = search_yify(self.text)
                    self.text = ''
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if self.txt_surface.get_width() < self.rect.w-30:
                        self.text += event.unicode
                # Re-render the text.
                self.txt_surface = self.font.render(self.text, True, self.text_color)
        if self.movies:
            return self.movies

    def draw(self, screen):
        # Blit the rect.
        if self.active:
            pygame.draw.rect(screen, (245,245,245), self.rect, 0)
            pygame.draw.rect(screen, (66, 206, 245), (self.rect.x-2, self.rect.y-2, self.rect.w+2, self.rect.h+2), 3)
        else:
            pygame.draw.rect(screen, (245, 245, 245), self.rect, 0)

        # Blit the text. Now centered vertically
        screen.blit(self.txt_surface, (self.rect.x + 5, (self.rect.y + (self.rect.h - self.txt_surface.get_height())/2)))

textInput = InputBox(10,10,SCREEN_WIDTH/1.2,35, "Search" )
def draw_header():
    pygame.draw.rect(screen, (40, 40, 40), (0, 0, SCREEN_WIDTH, 80))
    #pygame.draw.rect(screen, (220, 220, 220), (5, 5, SCREEN_WIDTH/1.2, 40))
    textInput.draw(screen)

running = True
while running:
    if movies:
        show_movies()

    draw_header()
    clock.tick(FPS)
    for event in pygame.event.get():
        movies = textInput.handle_event(event)
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.update()