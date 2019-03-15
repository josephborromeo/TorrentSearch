from urllib.request import urlopen, Request
import pygame, sys, time, io, os, textwrap, threading
from bs4 import BeautifulSoup
from pygame import gfxdraw

""" URLLIB HEADER"""
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Connection': 'keep-alive'}

""" PYGAME SETTINGS """

# Center Window in display
os.environ['SDL_VIDEO_CENTERED'] = '1'

clock = pygame.time.Clock()
FPS = 60

SCREEN_WIDTH, SCREEN_HEIGHT = 900, 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

bg_color = (250, 248, 239)

gui_font = "Calibri"

screen.fill(bg_color)
pygame.init()
pygame.key.set_repeat(500, 35)
# Sets the window name
pygame.display.set_caption("Torrent Search")
# Draws all changes to the window

# TODO: Probably move scrapers into a separate file
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

    --- Not using KAT since you cannot easily dl magnet link ---
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
    
    - Websites other than YIFY, show: Description, File Size, Seeders   - basically a list view
        - Have a checkbox to choose "extensive search" to check other websites

Site Specific Features
-----------------------
YIFY:
    - Resolution selector when downloading
"""

# TODO: Change loading sequence so the GUI loads and then checks all links and statuses, etc

# Path to local server's main HDD
movie_path = "Movies"
tv_path = "Tv Shows"
path_to_server = "//MEDIA-SERVER/E/"

"""     STATUS CHECKS       """
def check_statuses():
    pc, plex = False, False
    if os.path.exists(path_to_server):
        pc = True
    # TODO: implement check for plex
    return pc, plex
#print("STATUS:",check_statuses())

# Array of Movie objects
movies = []

""" Link Definintions """
yify = lambda name: 'https://yts.am/browse-movies/' + name.replace(" ", "%20") + '/all/all/0/latest'


class Movie:
    def __init__(self, name, link, img_link = ''):
        self.name = name
        self.link = link
        self.img_link = img_link
        self.img_size = (190, 285)
        self.image = pygame.Surface(self.img_size)
        self.image.fill(bg_color)
        pygame.draw.rect(self.image, (180,180,240), (0,0,self.img_size[0], self.img_size[1]))
        pygame.draw.rect(self.image, (20,20,200), (0,0,self.img_size[0], self.img_size[1]), 5)


    def load_img(self, link):
        print(self.name, "Image Loading...")
        if self.img_link != '':
            self.image = pygame.image.load(io.BytesIO(urlopen(link).read()))
            # Default image size is 230 x 345, Change it to 150 x 225
            self.image = pygame.transform.smoothscale(self.image, self.img_size)


total_movies = 0


def search_yify(name):
    print("SEARCHING")
    # FIXME: Speed up opening links -> takes too long for the initial load which makes everything seem slow
    # FIXED THE DOWNLOAD SPEED! now takes ~0.16s per image compared to 0.6 -> ~4x speedup
    movies = []
    try:
        start = time.clock()
        req = Request(yify(str(name)), headers=hdr)
        # req = Request(yify("the"), headers=hdr)
        # req = Request(yify("transformers"), headers=hdr)
        html = urlopen(req)
        print("Time to Open Page: %.2fs" % (time.clock() - start))
        soup = BeautifulSoup(html.read(), 'html.parser')
        print("Time to Read Page: %.2fs" % (time.clock() - start))
    except:
        print("That is an invalid URL")
    else:
        # print(soup.prettify())
        print("Time to retrieve Page: %.2fs" %(time.clock() - start))

    raw_data = soup.findAll('div', class_="browse-movie-wrap")
    start = time.clock()
    if len(raw_data) > 0:
        print(len(raw_data), "Results Found\n----------------")
        # Limit the number of movies to load
        total_movies = len(raw_data)
        if len(raw_data) > 6:
            raw_data = raw_data[:6]
        for movie in raw_data:
            if not fast_search.active:
                movies.append(Movie(movie.find("img")['alt'][:-9], movie.find("a")['href'], movie.find("img")['src']))
                #movies[-1].load_img()
                print(movie.find("img")['alt'][:-9])
                # Link
                print(movie.find("a")['href'])
                # Picture
                print(movie.find("img")['src'])
                print()
            else:
                movies.append(Movie(movie.find("img")['alt'][:-9], movie.find("a")['href']))
        print("Total Time to parse movies: %.2fs\nAvg per movie %.2fs" % (time.clock() - start, ((time.clock() - start) / len(movies))))


        if movies and not fast_search.active:
            start = time.clock()
            threads = [threading.Thread(target=mv.load_img, args=(mv.img_link,)) for mv in movies]
            print(len(threads))
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            print("Time to download images: %.2fs    Time per image: %.2fs" %((time.clock() - start), ((time.clock() - start)/len(threads))))

        return movies, total_movies
    else:
        movies = [None]
        print("No Movies Found")
        return movies, 0

def show_movies():
    # TODO: Add option for multiple screens, can just keep the whole array and then pick which section we are looking at
    num_cols = 3
    top_padding = 110
    inter_padding = 100
    font = pygame.font.SysFont(gui_font, 22)
    char_lim = 20
    text_spacing = 3
    if movies[0] is None:
        clear_movies()
        del(movies[0])
    else:
        screen.fill(bg_color)
        draw_header()
        for movie in range(len(movies)):
            name = movies[movie].name
            name = textwrap.fill(name, char_lim)
            name = name.split("\n")
            text_list = []
            for word in range(len(name)):
                text = font.render(name[word], True, (0, 0, 0))
                text_list.append(text)

            if movie < num_cols:
                screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + movie * (movies[movie].img_size[0]+inter_padding), top_padding))
                for word in range(len(text_list)):
                    screen.blit(text_list[word], (((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + movie * (movies[movie].img_size[0]+inter_padding)) + (movies[movie].img_size[0] - text_list[word].get_width())/2, top_padding + movies[movie].img_size[1] + (text_list[word].get_height()-text_spacing)* word))

            elif movie >= num_cols and movie < num_cols*2:
                screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + (movie - num_cols) * (movies[movie].img_size[0]+inter_padding), top_padding + (movies[movie].img_size[1]+inter_padding)))
                for word in range(len(text_list)):
                    screen.blit(text_list[word], (((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + (movie - num_cols) * (movies[movie].img_size[0]+inter_padding)) + (movies[movie].img_size[0] - text_list[word].get_width())/2, top_padding + movies[movie].img_size[1]*2 + inter_padding + (text_list[word].get_height()-text_spacing)* word))
            else:
                screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + (movie - num_cols*2) * (movies[movie].img_size[0]+inter_padding), top_padding + 2*(movies[movie].img_size[1]+inter_padding)))
                # text = font.render(movies[movie].name, True, (0, 0, 0))


def clear_movies():
    screen.fill(bg_color)
    draw_header()
    text = pygame.font.SysFont(gui_font, 72).render("No Movies Found", True, (240, 30, 15))
    screen.blit(text, (((SCREEN_WIDTH - text.get_width()) / 2), 150))


class InputBox:
    # TODO: Add cursor support to edit parts of the input
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (100,100,100)
        self.color_active = (200,200,200)
        self.text_color = (0,0,0)
        self.text = text
        self.font = pygame.font.SysFont(gui_font, 26)
        self.txt_surface = self.font.render(self.text, True, self.color_inactive)
        self.active = False
        self.movies = []
        self.total_movies = 0

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
                    if not extensive_search.active:
                        self.movies, self.total_movies = search_yify(self.text)
                    else:
                        pass
                    self.text = 'Search'
                    self.txt_surface = self.font.render(self.text, True, self.color_inactive)
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if self.txt_surface.get_width() < self.rect.w-30:
                        self.text += event.unicode
                # Re-render the text.
                if self.active:
                    self.txt_surface = self.font.render(self.text, True, self.text_color)
        if self.movies:
            return self.movies, self.total_movies
        return [], 0

    def draw(self, screen):
        # Blit the rect.
        if self.active:
            pygame.draw.rect(screen, (245,245,245), self.rect, 0)
            pygame.draw.rect(screen, (66, 206, 245), (self.rect.x-2, self.rect.y-2, self.rect.w+2, self.rect.h+2), 3)
        else:
            pygame.draw.rect(screen, (245, 245, 245), self.rect, 0)

        # Blit the text. Now centered vertically
        screen.blit(self.txt_surface, (self.rect.x + 5, (self.rect.y + (self.rect.h - self.txt_surface.get_height())/2)))


class CheckBox:
    def __init__(self, x, y, desc=''):
        self.size = 20
        self.label = desc
        self.font = pygame.font.SysFont(gui_font, 16)
        self.active = False
        self.inactive_color = (240, 240, 240)
        self.border_color = (120, 120, 120)
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.timer = 0
        self.threshhold = 0.4

        if self.label != '':
            self.text = self.font.render(self.label, True, self.inactive_color)

    def draw(self):
        # Will handle drawing and toggle logic so only one call is needed for each object

        # TODO: Fix the toggling if the mouse is held down. Probably have to use events
        if pygame.mouse.get_pressed()[0] and self.rect.collidepoint(pygame.mouse.get_pos()) and time.clock() - self.timer > self.threshhold:
            self.active = not self.active
            self.timer = time.clock()

        if not self.active:
            pygame.draw.rect(screen, self.inactive_color, self.rect)
            pygame.draw.rect(screen, self.border_color, self.rect, 2)
        else:
            pygame.draw.rect(screen, self.inactive_color, self.rect)
            pygame.draw.aaline(screen, (0,0,0), (self.rect.x, self.rect.y), (self.rect.x + self.size-1, self.rect.y + self.size-1))
            pygame.draw.aaline(screen, (0, 0, 0), (self.rect.x, self.rect.y + self.size-1),(self.rect.x + self.size-1, self.rect.y))
            pygame.draw.rect(screen, self.border_color, self.rect, 2)


        if self.label != '':
            screen.blit(self.text, (self.rect.x + self.size + 5, self.rect.y + (self.size - self.text.get_height())))

class ModeSelector():
    def __init__(self, x, y):
        self.height = 29
        self.width = 100     # Width per side
        self.x = x
        self.y = y
        self.timer = 0
        self.threshhold = 0.2

        self.movie_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.tv_rect = pygame.Rect(self.x + self.width, self.y, self.width, self.height)

        self.movie_mode = True

        # Colors
        self.selected = (78, 194, 196)
        self.selected_hover = (108, 224, 226)

        self.unselected = (73, 92, 122)
        self.unselected_hover = (102, 129, 173)

        self.font = pygame.font.SysFont(gui_font, 24)
        self.movie_text = self.font.render("Movies", True, (40,40,40))
        self.tv_text = self.font.render("TV Shows", True, (40,40,40))

    def draw(self):
        if self.movie_mode:
            if self.tv_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, self.selected, self.movie_rect)
                pygame.draw.rect(screen, self.unselected_hover, self.tv_rect)

                if pygame.mouse.get_pressed()[0] and time.clock() - self.timer > self.threshhold:
                    self.movie_mode = not self.movie_mode
                    self.timer = time.clock()
            elif self.movie_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, self.selected_hover, self.movie_rect)
                pygame.draw.rect(screen, self.unselected, self.tv_rect)

            else:
                pygame.draw.rect(screen, self.selected, self.movie_rect)
                pygame.draw.rect(screen, self.unselected, self.tv_rect)

        else:
            if self.movie_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, self.unselected_hover, self.movie_rect)
                pygame.draw.rect(screen, self.selected, self.tv_rect)

                if pygame.mouse.get_pressed()[0] and time.clock() - self.timer > self.threshhold:
                    self.movie_mode = not self.movie_mode
                    self.timer = time.clock()

            elif self.tv_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, self.unselected, self.movie_rect)
                pygame.draw.rect(screen, self.selected_hover, self.tv_rect)

            else:
                pygame.draw.rect(screen, self.unselected, self.movie_rect)
                pygame.draw.rect(screen, self.selected, self.tv_rect)

        screen.blit(self.movie_text, (self.x + (self.width - self.movie_text.get_width())/2 , self.y + (self.height - self.movie_text.get_height())))
        screen.blit(self.tv_text, (self.x + self.width + (self.width - self.tv_text.get_width()) / 2, self.y + (self.height - self.tv_text.get_height())))

def movie_preview():
    # TODO: Write function to display the full size thumbnail, description, and download options
    # TODO: Extra features will include relevant movies and such
    pass


textInput = InputBox(10, 10, SCREEN_WIDTH/1.2, 35, "Search")
def draw_header():
    pygame.draw.rect(screen, (40, 40, 40), (0, 0, SCREEN_WIDTH, 90))
    textInput.draw(screen)
    user_buttons()
    font = pygame.font.SysFont(gui_font, 26)
    result_text = font.render("Results Found: " + str(total_movies), True, (230, 230, 230))
    screen.blit(result_text, (505, 56))


extensive_search = CheckBox(230, 57, "Extensive Search")
fast_search = CheckBox(385, 57, "Fast Search")
mode_select = ModeSelector(10, 53)
def user_buttons():
    pygame.draw.rect(screen, (130, 90, 95), ((SCREEN_WIDTH/1.2) + 20, 10, (SCREEN_WIDTH - (SCREEN_WIDTH/1.2 + 20) - 10), 35))
    extensive_search.draw()
    fast_search.draw()
    mode_select.draw()


running = True
while running:
    if movies:
        show_movies()

    draw_header()

    clock.tick(FPS)
    for event in pygame.event.get():
        movies, total_movies = textInput.handle_event(event)
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.update()