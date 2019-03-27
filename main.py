from urllib.request import urlopen, Request
import pygame, sys, time, io, os, textwrap, threading, webbrowser, math, shutil
from bs4 import BeautifulSoup

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
pygame.display.set_caption("Torrent Search")
gear = pygame.image.load('resources/gear_icon.png').convert_alpha()

bg_color = (250, 248, 239)

gui_font = "Calibri"

screen.fill(bg_color)
pygame.init()
pygame.key.set_repeat(500, 35)
# Sets the window name
pygame.display.set_caption("Torrent Search")

# TODO: Probably move scrapers into a separate file
# TODO: Make installer for Windows and Mac
# TODO: Research running plex as a service - Apparently it is much better
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
    - ** Check if the MEDIA-SERVER pc is available **                                                                   - DONE!
    - ** Next Check if PLEX is up and active **
    - At the start of the program, make sure the URLs are accessible since the websites change domains often
      
    - Auto-format TV show search terms (e.g. S__E__)
    - Automatically set download path when choosing to search for either a Movie of TV Show
    
    - Websites other than YIFY, show: Description, File Size, Seeders   - basically a list view                         - DONE!
        - Have a checkbox to choose "extensive search" to check other websites                                          - DONE!
        
    - Movie trailer button in movie screen                                                                              - DONE!
    - Magnifying glass at end of search bar                                                                             - DONE!
    
Site Specific Features
-----------------------
YIFY:
    - Resolution selector when downloading                                                                              - DONE!
    - Browse option to browse all movies from YIFY (latest, name, etc)
"""

# TODO: Change loading sequence so the GUI loads and then checks all links and statuses, etc

# Path to local server's main HDD
#TODO: Place these in a configuration file, have them changeable through the gui
movie_path = "Movies"   # Folder Name
tv_path = "Tv Shows"    # Folder Name
path_to_server = "//MEDIA-SERVER/E/"    #TODO: Check to see if this works as a qbittorent URL
#path_to_server = '\\'  #TODO: Remove this after testing
plex_server = False
convert = lambda value: value/1e9
"""     STATUS CHECKS       """
def check_statuses():
    pc, plex = False, False
    total, used, free = 0, 0, 0
    if os.path.exists(path_to_server):
        pc = True
        total, used, free = shutil.disk_usage(path_to_server)
        total, used, free = convert(total), convert(used), convert(free)
        print("Disk Space: Total: %.2fGB Used: %.2fGB Free: %.2fGB" % (total, used, free))

        if plex_server:
            pass # TODO: implement check for plex server status

    return pc, plex, total, used, free


pc_stat, plex_stat, total, used, free = check_statuses()

# Array of Movie objects
movies, all_movies = [], []

""" Link Definintions """
"""     Have to think about whether I want to list the first couple by the default order or if I want to sort by seeders from the beginning     """
yify = lambda name: 'https://yts.am/browse-movies/' + name.replace(" ", "%20") + '/all/all/0/latest'

tpb = lambda name: 'https://thepiratebay.org/search/' + name.replace(" ", "%20") + '/0/99/200'

rar_movies = lambda name: 'http://rarbg.to/torrents.php?search=' + name.replace(" ", "+") + '&category%5B%5D=14&category%5B%5D=48&category%5B%5D=17&category%5B%5D=44&category%5B%5D=45&category%5B%5D=42&category%5B%5D=46'
rar_tv = lambda name: 'http://rarbg.to/torrents.php?search=' + name.replace(" ", "+") + '&category%5B%5D=18&category%5B%5D=41&category%5B%5D=49'


class Movie:
    def __init__(self, name, link, img_link = ''):
        self.name = name
        self.link = link
        self.img_link = img_link
        self.img_size = (190, 285)
        self.image = pygame.Surface(self.img_size)
        self.image.fill(bg_color)
        self.loaded = False
        pygame.draw.rect(self.image, (180,180,240), (0,0,self.img_size[0], self.img_size[1]))
        pygame.draw.rect(self.image, (20,20,200), (0,0,self.img_size[0], self.img_size[1]), 5)


    def load_img(self, link):
        print(self.name, "Image Loading...")
        if self.img_link != '':
            self.image = pygame.image.load(io.BytesIO(urlopen(link).read()))
            # Default image size is 230 x 345, Change it to 150 x 225
            self.image = pygame.transform.smoothscale(self.image, self.img_size)
            self.loaded = True


class Torrent:
    def __init__(self, name, link, size, seeders, leechers, source):
        self.name = name
        self.link = link
        self.size = size
        self.seeders = seeders
        self.leechers = leechers
        self.source = source
        self.hover = False

        self.height = 80

        self.title_font = pygame.font.SysFont(gui_font, 26)
        self.data_font = pygame.font.SysFont(gui_font, 20)

        self.name_text = self.title_font.render(self.name, True, (30,30,30))
        self.dl_btn = RoundedRectangle(0,0, 120, 30, 6, (240, 0, 42), text="Download", font_size=25)

        self.size_text = self.data_font.render("Size: " + self.size, True, (30, 30, 30))
        self.seeders_text = self.data_font.render("Seeders: " + self.seeders, True, (30, 30, 30))
        self.leechers_text = self.data_font.render("Leechers: " + self.leechers, True, (30, 30, 30))
        self.source_text = self.data_font.render("Source: " + self.source, True, (30, 30, 30))
        self.text_offset = self.size_text.get_height()


    def draw(self, y_index, y_offset):
        # Background to fix text overlapping
        pygame.draw.rect(screen, (bg_color[0] - 30, bg_color[1] - 15, bg_color[2] - 5), (0, 90 + y_offset + y_index * self.height, SCREEN_WIDTH, self.height + 2))
        self.text_rect = pygame.Rect(10, 100 + y_offset + y_index * self.height, self.name_text.get_width(), self.name_text.get_height())

        # Draw Border
        pygame.draw.rect(screen, (30, 30, 30), (0, 90 + y_offset + y_index*self.height, SCREEN_WIDTH, self.height + 2), 2)

        screen.blit(self.name_text, self.text_rect)

        # Download button
        self.dl_btn.x = SCREEN_WIDTH - self.dl_btn.width - 10
        self.dl_btn.y = 90 + y_offset + y_index*self.height + self.height - self.dl_btn.height - 10
        self.dl_btn.draw()

        # Display Torrent data
        screen.blit(self.size_text, (10, 90 + y_offset + y_index * self.height + self.height - self.text_offset))
        screen.blit(self.seeders_text, (30 + self.size_text.get_width(), 90 + y_offset + y_index * self.height + self.height - self.text_offset))
        screen.blit(self.leechers_text, (50 + self.size_text.get_width() + self.seeders_text.get_width(), 90 + y_offset + y_index * self.height + self.height - self.text_offset))
        screen.blit(self.source_text, (70 + self.size_text.get_width() + self.seeders_text.get_width() + self.leechers_text.get_width(), 90 + y_offset + y_index * self.height + self.height - self.text_offset))


class Download:
    def __init__(self, x, y, w, h, name, id, progress, dl_speed, ul_speed, size, surf=screen):
        self.rect = pygame.Rect(x, y, w, h)
        self.name = name
        self.progress = progress
        self.dl_speed = dl_speed
        self.ul_speed = ul_speed
        self.size = size
        self.id = id
        self.surf = surf
        self.progress_bar = ProgressBar(surf=self.surf)
        # Buttons for start/stop/pausing torrents
        self.bg_color = (120, 120, 240, 240)

        #self.start_btn = RoundedRectangle
        #self.stop_btn = RoundedRectangle
        #self.delete_btn = RoundedRectangle
        # TODO: Implement start/stop/delete buttons

    def draw(self):
        # Background
        pygame.draw.rect(self.surf, self.bg_color, self.rect)
        #Border
        pygame.draw.rect(self.surf, (30, 30, 30), self.rect, 2)


total_movies = 0

def load_movie_images(movies):
    start = time.clock()
    threads = [threading.Thread(target=mv.load_img, args=(mv.img_link,)) for mv in movies]
    print(len(threads))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print("Time to download images: %.2fs    Time per image: %.2fs" % (
    (time.clock() - start), ((time.clock() - start) / len(threads))))

def search_yify(name):
    print("SEARCHING")
    # FIXED THE DOWNLOAD SPEED! now takes ~0.16s per image compared to 0.6 -> ~4x speedup
    movies, all_movies = [], []
    try:
        start = time.clock()
        req = Request(yify(str(name)), headers=hdr)
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
        #if len(raw_data) > 6:
        #    raw_data = raw_data[:6]
        for movie in raw_data:
            if not fast_search.active:
                all_movies.append(Movie(movie.find("img")['alt'][:-9], movie.find("a")['href'], movie.find("img")['src']))
                #movies[-1].load_img()
                print(movie.find("img")['alt'][:-9])
                # Link
                print(movie.find("a")['href'])
                # Picture
                print(movie.find("img")['src'])
                print()
            else:
                all_movies.append(Movie(movie.find("img")['alt'][:-9], movie.find("a")['href']))

        print("Total Time to parse movies: %.2fs\nAvg per movie %.2fs" % (time.clock() - start, ((time.clock() - start) / len(all_movies))))

        if total_movies > 6:
            movies = all_movies[:6]
        else:
            movies = all_movies

        if movies and not fast_search.active:
            load_movie_images(movies)

        return movies, all_movies, total_movies
    else:
        movies, all_movies = [None], [None]
        print("No Movies Found")
        return movies, all_movies, 0

def search_tpb(name):
    num_results = 6
    torrents = []
    try:
        start = time.clock()
        req = Request(tpb(str(name)), headers=hdr)
        html = urlopen(req)
        soup = BeautifulSoup(html.read(), 'html.parser')
    except:
        print("That is an invalid URL")
    else:
        # print(soup.prettify())
        print("Time to retrieve Page: %.2fs" %(time.clock() - start))

    title = soup.findAll('div', class_="detName")
    size = soup.findAll('font', class_='detDesc')
    title = title[:num_results]
    size = size[:num_results]
    # raw_stats = soup.findAll('td')
    raw_stats = soup.find_all('td', {'align': 'right'})
    raw_stats = raw_stats[:num_results * 2]
    magnets = soup.findAll('a', {'title': 'Download this torrent using magnet'})
    if len(title) < num_results:
        num_results = len(title)
    if len(title) > 0:
        for i in range(0, num_results * 2, 2):
            name = title[int(i / 2)].text.replace('\n', "")[1:]
            file_size = size[int(i / 2)].text.split(',')[1].replace(" Size ", "")
            seeders = int(raw_stats[i].text)
            leechers = int(raw_stats[i + 1].text)
            magnet = magnets[int(i / 1)]['href']
            torrents.append(Torrent(name, magnet, str(file_size), str(seeders), str(leechers), 'TPB'))
    else:
        clear_movies()

    return torrents

def show_movies(movies, all_movies, total_movies, page):
    # TODO: add loading icon!
    num_cols = 3
    top_padding = 110
    inter_padding = 100
    font = pygame.font.SysFont(gui_font, 22)
    char_lim = 20
    text_spacing = 3
    start = 0
    loaded_movies = []
    page = page

    if movies[0] is None:
        clear_movies()
        del(movies[0])

    else:
        # Check to see how many pages, etc.
        if total_movies > 6:
            start_index, end_index = 0, 6
            next_btn = RoundedRectangle(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 45, 75, 35, 10, (50, 180, 90), font_size=26, text='Next')
            back_btn = RoundedRectangle(SCREEN_WIDTH - 160, SCREEN_HEIGHT - 45, 75, 35, 10, (180, 50, 90), font_size=26, text='Back')

            pages = math.ceil(total_movies/6)

            if page == 2:
                if total_movies > 12:
                    start_index, end_index = 6, 12
                else:
                    start_index, end_index = 6, total_movies
            elif page == 3:
                if total_movies > 18:
                    start_index, end_index = 12, 18
                else:
                    start_index, end_index = 12, total_movies

            elif page == 4:
                if total_movies == 20:
                    start_index, end_index = 18, 20
                else:
                    start_index, end_index = 18, total_movies

            if not all_movies[start_index].loaded and not fast_search.active:
                print("Have to load images")
                load_movie_images(all_movies[start_index:end_index])

            movies = all_movies[start_index:end_index]

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

            pos = pygame.mouse.get_pos()
            if movie < num_cols:
                # Click Detection
                if pos[0] > ((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + movie * (movies[movie].img_size[0]+inter_padding)) and pos[0] < (SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + movie * (movies[movie].img_size[0]+inter_padding) + movies[movie].img_size[0]:
                    if pos[1] > top_padding and pos[1] < top_padding + movies[movie].img_size[1]:
                        if pygame.mouse.get_pressed()[0] and time.clock()-start > 0.5:
                            print(movies[movie].name)
                            movie_preview(movies[movie])
                            start = time.clock()

                screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + movie * (movies[movie].img_size[0]+inter_padding), top_padding))
                for word in range(len(text_list)):
                    screen.blit(text_list[word], (((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + movie * (movies[movie].img_size[0]+inter_padding)) + (movies[movie].img_size[0] - text_list[word].get_width())/2, top_padding + movies[movie].img_size[1] + (text_list[word].get_height()-text_spacing)* word))

            elif movie >= num_cols and movie < num_cols*2:
                # Click Detection
                if pos[0] > ((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + (movie - num_cols) * (movies[movie].img_size[0]+inter_padding)) and pos[0] < ((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + (movie - num_cols) * (movies[movie].img_size[0]+inter_padding) + movies[movie].img_size[0]):
                    if pos[1] > top_padding + (movies[movie].img_size[1]+inter_padding) and pos [1] < top_padding + (movies[movie].img_size[1]+inter_padding) + movies[movie].img_size[1]:
                        if pygame.mouse.get_pressed()[0] and time.clock()-start > 0.5:
                            print(movies[movie].name)
                            movie_preview(movies[movie])
                            start = time.clock()

                screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + (movie - num_cols) * (movies[movie].img_size[0]+inter_padding), top_padding + (movies[movie].img_size[1]+inter_padding)))
                for word in range(len(text_list)):
                    screen.blit(text_list[word], (((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + (movie - num_cols) * (movies[movie].img_size[0]+inter_padding)) + (movies[movie].img_size[0] - text_list[word].get_width())/2, top_padding + movies[movie].img_size[1]*2 + inter_padding + (text_list[word].get_height()-text_spacing)* word))
            else:
                screen.blit(movies[movie].image, ((SCREEN_WIDTH - ((movies[movie].img_size[0]+inter_padding)* num_cols - inter_padding))/2 + (movie - num_cols*2) * (movies[movie].img_size[0]+inter_padding), top_padding + 2*(movies[movie].img_size[1]+inter_padding)))

            if total_movies> 6:
                pressed = pygame.mouse.get_pressed()[0]
                if page < pages:
                    if page < 4:
                        next_btn.draw()
                        if pressed and next_btn.onHover():
                            start = time.clock()
                            while pressed:
                                pygame.event.get()
                                pressed = pygame.mouse.get_pressed()[0]
                            page += 1
                            print(page)

                if page > 1:
                    back_btn.draw()
                    if pressed and back_btn.onHover():
                        start = time.clock()
                        while pressed:
                            pygame.event.get()
                            pressed = pygame.mouse.get_pressed()[0]
                        page -= 1
                        print(page)

    return page

def show_links(movies, offset, bg):
    pygame.draw.rect(screen, bg_color, (0, 90, SCREEN_WIDTH, SCREEN_HEIGHT))
    scrolling = False
    if len(movies) > 9:
        scrolling = True
    for movie in range(len(movies)):
        if scrolling:
            movies[movie].draw(movie, -offset)
        else:
            movies[movie].draw(movie, 0)

        if movies[movie].dl_btn.onHover() and pygame.mouse.get_pressed()[0]:
            dl_conf = confirmation_screen("confirm this download", bg)



def clear_movies(show_text = True):
    screen.fill(bg_color)
    draw_header()
    if show_text:
        if mode_select.movie_mode:
            text = pygame.font.SysFont(gui_font, 72).render("No Movies Found", True, (240, 30, 15))
        else:
            text = pygame.font.SysFont(gui_font, 72).render("No Shows Found", True, (240, 30, 15))
        screen.blit(text, (((SCREEN_WIDTH - text.get_width()) / 2), 150))

# TODO: Move drawing functions and classes to another file

class InputBox:
    def __init__(self, x, y, w, h, text='', show_icon=True, char_lim=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (100,100,100)
        self.color_active = (200,200,200)
        self.text_color = (0,0,0)
        self.text = text
        self.default_text = text
        self.font = pygame.font.SysFont(gui_font, 26)
        self.txt_surface = self.font.render(self.text, True, self.color_inactive)
        self.search_img = pygame.image.load('resources/search_icon.png').convert_alpha()
        self.active = False
        self.movies, self.all_movies = [], []
        self.total_movies = 0
        self.show_icon = show_icon
        self.pointer = 0
        self.cursor_active = True
        self.cursor_rate = 35
        self.cursor_count = 0
        self.char_lim = char_lim

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Search with Magnifying glass
                if self.show_icon and event.pos[0] > self.rect.x + self.rect.w - 35 and event.pos[0] < self.rect.x + self.rect.w and event.pos[1] > self.rect.y and event.pos[1] < self.rect.y + self.rect.h and self.text != 'Search':
                    self.search()
                # Toggle the active variable.
                elif not self.active and self.text == self.default_text:
                    self.text = ''
                    self.txt_surface = self.font.render(self.text, True, self.text_color)
                    self.active = not self.active
                elif self.active and self.text == '':
                    self.text = self.default_text
                    self.txt_surface = self.font.render(self.text, True, self.color_inactive)
                    self.active = not self.active
                else:
                    self.active = True

            else:
                if self.active and self.text == '':
                    self.text = self.default_text
                    self.txt_surface = self.font.render(self.text, True, self.color_inactive)
                self.active = False

            # Change the current color of the input box.
            self.color = self.color_active if self.active else self.color_inactive

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.search()
                    self.pointer = 0
                elif event.key == pygame.K_BACKSPACE:
                    if self.pointer > 0:
                        self.text = self.text[:self.pointer-1] + self.text[self.pointer:]
                        self.pointer -= 1
                elif event.key == pygame.K_DELETE:
                    self.text = self.text[:self.pointer] + self.text[self.pointer+1:]
                elif event.key == pygame.K_RIGHT:
                    if self.pointer < len(self.text):
                        self.pointer += 1
                elif event.key == pygame.K_LEFT:
                    if self.pointer > 0:
                        self.pointer -= 1

                else:
                    if self.txt_surface.get_width() < self.rect.w-45 and self.show_icon:
                        print(self.pointer, len(self.text))
                        if len(self.text) > 0:
                            self.text = self.text[:self.pointer] + event.unicode + self.text[self.pointer:]
                        else:
                            self.text += event.unicode
                        if event.key != pygame.K_LSHIFT and event.key != pygame.K_RSHIFT:
                            self.pointer += 1
                # Re-render the text.
                if self.active:
                    self.txt_surface = self.font.render(self.text, True, self.text_color)

        return self.movies, self.all_movies, self.total_movies


    def draw(self, screen):
        # Blit the rect.
        if self.active:
            pygame.draw.rect(screen, (245,245,245), self.rect, 0)
            pygame.draw.rect(screen, (66, 206, 245), (self.rect.x-2, self.rect.y-2, self.rect.w+2, self.rect.h+2), 3)

            # Draw cursor at end of text
            if self.cursor_active:
                self.temp_text_surf = self.font.render(self.text[:self.pointer], True, self.text_color)
                pygame.draw.line(screen, (30, 30, 30), (self.rect.x + self.temp_text_surf.get_width() + 5, self.rect.y + 3), (self.rect.x + self.temp_text_surf.get_width() + 5, self.rect.y + self.rect.h - 7), 2)
            self.cursor_count += 1

            if self.cursor_count >= self.cursor_rate:
                self.cursor_active = not self.cursor_active
                self.cursor_count = 0

        else:
            pygame.draw.rect(screen, (245, 245, 245), self.rect, 0)

        # Blit the text. Now centered vertically
        screen.blit(self.txt_surface, (self.rect.x + 5, (self.rect.y + (self.rect.h - self.txt_surface.get_height())/2)))

        # Blit search Icon
        if self.show_icon:
            screen.blit(self.search_img, (self.rect.x + self.rect.w - 35, self.rect.y + 1))

    def search(self):
        global page, disp_mode, scroll_offset
        page = 1
        print(self.text)
        if not mode_select.movie_mode:
            disp_mode = 'list'
            if textInput_season.text != '':
                self.text = self.text + " S" + textInput_season.text
                if textInput_episode.text != '':
                    self.text = self.text + "E" + textInput_tv.text

        if not extensive_search.active:
            disp_mode = 'thumb'
            self.movies, self.all_movies, self.total_movies = search_yify(self.text)
        else:
            disp_mode = 'list'
            self.movies = search_tpb(self.text)
        scroll_offset = 0
        self.text = 'Search'
        self.txt_surface = self.font.render(self.text, True, self.color_inactive)
        self.active = False

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
        if pygame.mouse.get_pressed()[0] and self.rect.collidepoint(pygame.mouse.get_pos()) and time.clock() - self.timer > self.threshhold:
            while pygame.mouse.get_pressed()[0]:
                pygame.event.get()
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
        self.movie_text = self.font.render("Movies", True, (40, 40, 40))
        self.tv_text = self.font.render("TV Shows", True, (40, 40, 40))

    def draw(self):
        if self.movie_mode:
            if self.tv_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, self.selected, self.movie_rect)
                pygame.draw.rect(screen, self.unselected_hover, self.tv_rect)

                if pygame.mouse.get_pressed()[0] and time.clock() - self.timer > self.threshhold:
                    self.movie_mode = not self.movie_mode
                    self.timer = time.clock()

                    if not extensive_search.active:
                        extensive_search.active = True
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

                    if extensive_search.active:
                        extensive_search.active = False

            elif self.tv_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, self.unselected, self.movie_rect)
                pygame.draw.rect(screen, self.selected_hover, self.tv_rect)

            else:
                pygame.draw.rect(screen, self.unselected, self.movie_rect)
                pygame.draw.rect(screen, self.selected, self.tv_rect)

        screen.blit(self.movie_text, (self.x + (self.width - self.movie_text.get_width())/2 , self.y + (self.height - self.movie_text.get_height())))
        screen.blit(self.tv_text, (self.x + self.width + (self.width - self.tv_text.get_width()) / 2, self.y + (self.height - self.tv_text.get_height())))

class RoundedRectangle():
    def __init__(self, x, y, width, height, radius, color, font = gui_font, font_size = 30, text = '', hover_enabled=True, surf=screen):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.radius = radius
        self.color = color
        self.hover_color = (color[0]+15 if color[0]+15 < 255 else 255, color[1]+15 if color[1]+15 < 255 else 255, color[2]+15 if color[2]+15 < 255 else 255)
        self.col_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.hover_check = hover_enabled
        self.surf = surf
        self.text = text

        if self.text != '':
            self.font_size = font_size
            self.font = pygame.font.SysFont(font, self.font_size)
            self.text_render = self.font.render(self.text, True, (30, 30, 30))

    def draw(self):
        self.col_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if self.onHover() and self.hover_check:
            # Body
            pygame.draw.rect(self.surf, self.hover_color, (self.x, self.y + self.radius, self.width, self.height - self.radius*2))
            pygame.draw.rect(self.surf, self.hover_color, (self.x + self.radius, self.y, self.width - self.radius*2, self.height))
    
            # Corners
            if self.radius > 0:
                pygame.draw.circle(self.surf, self.hover_color, (self.x + self.radius, self.y + self.radius), self.radius)
                pygame.draw.circle(self.surf, self.hover_color, (self.x + self.width - self.radius, self.y + self.radius), self.radius)
                pygame.draw.circle(self.surf, self.hover_color, (self.x + self.radius, self.y + self.height- self.radius), self.radius)
                pygame.draw.circle(self.surf, self.hover_color, (self.x + self.width - self.radius, self.y + self.height - self.radius), self.radius)

        else:
            # Hovered Body
            pygame.draw.rect(self.surf, self.color, (self.x, self.y + self.radius, self.width, self.height - self.radius*2))
            pygame.draw.rect(self.surf, self.color, (self.x + self.radius, self.y, self.width - self.radius*2, self.height))
    
            # Hovered Corners
            if self.radius > 0:
                pygame.draw.circle(self.surf, self.color, (self.x + self.radius, self.y + self.radius), self.radius)
                pygame.draw.circle(self.surf, self.color, (self.x + self.width - self.radius, self.y + self.radius), self.radius)
                pygame.draw.circle(self.surf, self.color, (self.x + self.radius, self.y + self.height- self.radius), self.radius)
                pygame.draw.circle(self.surf, self.color, (self.x + self.width - self.radius, self.y + self.height - self.radius), self.radius)

        if self.text != '':
            self.surf.blit(self.text_render, (self.x + (self.width - self.text_render.get_width())/2, self.y + (self.height - self.text_render.get_height())/2))

    def onHover(self):
        pos = pygame.mouse.get_pos()
        if self.col_rect.collidepoint(pos):
            return True
        return False

class ProgressBar():
    def __init__(self, x, y, percentage, surf=screen):
        self.width = 85
        self.height = 18
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.font = pygame.font.SysFont(gui_font, 20)
        self.percentage = percentage
        self.text = self.font.render(str(self.percentage)+"%", True, (30, 30, 30))
        self.surf = surf

    def draw(self):
        # Progress
        pygame.draw.rect(self.surf, (30, 240, 60), (self.rect.x, self.rect.y, int(self.rect.w * (self.percentage/100)), self.rect.h))
        #Outline
        pygame.draw.rect(self.surf, (30, 30, 30), self.rect, 2)

        self.surf.blit(self.text, (self.rect.x + self.rect.w + 5, self.rect.y + (self.rect.h - self.text.get_height())/2 + 3))

def confirmation_screen(text='', background=''):
    text = "Are you sure you want to " + text + "?"
    text = textwrap.fill(text, 30)
    running = True
    bg = background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA, 32)
    pygame.draw.rect(overlay, (160,50,90,120), (300,300, 150,150))
    body_rect = pygame.Rect(150, 250, 600, 300)
    font = pygame.font.SysFont(gui_font, 42, True)
    text_list = text.split('\n')
    disp_text = []
    btnfont = pygame.font.SysFont(gui_font, 65, True)
    yes_text = btnfont.render("YES", True, (50,50,50))
    no_text = btnfont.render("NO", True, (50,50,50))
    start = time.clock()
    for i in text_list:
        disp_text.append(font.render(i, True, (50,50,50)))

    while running:
        if bg != '':
            screen.blit(bg, (0, 0))
        pygame.draw.rect(overlay, (219, 243, 252, 240), body_rect)
        for i in range(len(disp_text)):
            overlay.blit(disp_text[i], (150 + (600 - disp_text[i].get_width())/2, 260 + 40*i))

        pos = pygame.mouse.get_pos()
        # Yes Button
        if pos[0] > body_rect.x + (300-200)/2 and pos[0] < body_rect.x + (300-200)/2 + 200 and pos[1] > body_rect.y + body_rect.h - 90 - (300-200)/2 and pos[1] < body_rect.y + body_rect.h - 90 - (300-200)/2 + 90:
            pygame.draw.rect(overlay, (100, 255, 157, 230), (body_rect.x + (300 - 200) / 2, body_rect.y + body_rect.h - 90 - (300 - 200) / 2, 200, 90))
            if pygame.mouse.get_pressed()[0]:
                while pygame.mouse.get_pressed()[0]:
                    pygame.event.get()
                return True
        else:
            pygame.draw.rect(overlay, (80,255,137, 240), (body_rect.x + (300-200)/2, body_rect.y + body_rect.h - 90 - (300-200)/2, 200, 90))
        overlay.blit(yes_text, (body_rect.x + (300-200)/2 + (200 - yes_text.get_width())/2, body_rect.y + body_rect.h - 85 - (300-200)/2 + (90 - yes_text.get_height())/2))

        # No Button
        if pos[0] > body_rect.x + body_rect.w - 200 - (300-200)/2 and pos[0] < body_rect.x + body_rect.w - 200 - (300-200)/2 + 200 and pos[1] > body_rect.y + body_rect.h - 90 - (300-200)/2 and pos[1] < body_rect.y + body_rect.h - 90 - (300-200)/2 + 90:
            pygame.draw.rect(overlay, (255, 100, 110, 230), (body_rect.x + body_rect.w - 200 - (300 - 200) / 2, body_rect.y + body_rect.h - 90 - (300 - 200) / 2, 200, 90))
            if pygame.mouse.get_pressed()[0]:
                while pygame.mouse.get_pressed()[0]:
                    pygame.event.get()
                return False
        else:
            pygame.draw.rect(overlay, (255,79,90, 240), (body_rect.x + body_rect.w - 200 - (300-200)/2, body_rect.y + body_rect.h - 90 - (300-200)/2, 200, 90))
        overlay.blit(no_text, (body_rect.x + body_rect.w - 200 - (300 - 200) / 2 + (200 - no_text.get_width()) / 2, body_rect.y + body_rect.h - 85 - (300 - 200) / 2 + (90 - no_text.get_height()) / 2))

        screen.blit(overlay, (0, 0))

        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP and not body_rect.collidepoint(pygame.mouse.get_pos()) and time.clock() - start > 0.2:
                return False
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.update()

def settings_screen():
    # TODO: Settings
    """
    Reboot Computer button,                                                                                             - Done
    Restart Plex Button                                                                                                 - Done
    Server and Computer status,                                                                                         - DONE
    status refresh button,                                                                                              - DONE
    Disable confirmation screen when downloading(Resets on restart)
    Open config file? -> Server mode OR Standalone mode
    Sort Priority: Seeders, File Size, Date Uploaded, Default order <-- Probably gonna be default. rest can come later
        - Write a sorting algorithm!
    """
    start = time.clock()
    running = True
    bg = screen_copy    # Fixes movies not showing up when settings menu is opened
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA, 32)
    title_font = pygame.font.SysFont(gui_font, 50)
    title_text = title_font.render("Settings", True, (30, 30, 30))
    setting_font = pygame.font.SysFont(gui_font, 35)
    width = int(SCREEN_WIDTH/1.5)
    height = int(SCREEN_HEIGHT/1.5)
    rect = pygame.Rect(int((SCREEN_WIDTH - width)/2), int((SCREEN_HEIGHT - height)/2), width, height)
    body = RoundedRectangle(int((SCREEN_WIDTH - width)/2), int((SCREEN_HEIGHT - height)/2), width, height, 15, (232, 220, 220), hover_enabled=False, surf=overlay)
    exit_btn = RoundedRectangle(int((SCREEN_WIDTH - width)/2) + width - 50, int((SCREEN_HEIGHT - height)/2) + 10, 40, 40, 10, (180, 80, 80), surf=overlay)
    reboot_btn = RoundedRectangle(int((SCREEN_WIDTH - width)/2) + int((width/2 - 250)/2), int((SCREEN_HEIGHT - height)/2) + height - 45, 250, 35, 5, (255, 200, 100), font_size=25, text="REBOOT COMPUTER", surf=overlay)
    restart_plex = RoundedRectangle(int((SCREEN_WIDTH - width)/2 + width - 250 - int((width/2 - 250)/2)), int((SCREEN_HEIGHT - height)/2) + height - 45, 250, 35, 5, (255, 200, 100), font_size=25, text="RESTART PLEX", surf=overlay)
    stat_radius = 16
    pc_status = setting_font.render("PC Status:", True, (30,30,30))
    plex_status = setting_font.render("Plex Status:", True, (30,30,30))
    usage_text = setting_font.render("Disk Usage:", True, (30, 30, 30))
    refresh_status_btn = RoundedRectangle(int((SCREEN_WIDTH - width)/2) + width - 125, int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + 15, 90, 30, 10, (30, 190, 95), font_size=25, text="Refresh", surf=overlay)

    if pc_stat:
        disk_usage = ProgressBar(int((SCREEN_WIDTH - width)/2) + 40 + usage_text.get_width(), int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + 32 + pc_status.get_height(), int((used/total)*100), surf=overlay)
        disk_usage.rect.h = 30
        disk_usage.font = pygame.font.SysFont(gui_font, 30)
        disk_usage.text = disk_usage.font.render(str(disk_usage.percentage) + "% Used", True, (30, 30, 30))

    while running:
        screen.blit(bg, (0, 0))
        body.draw()
        if plex_server:
            reboot_btn.draw()
            restart_plex.draw()
        pygame.draw.line(overlay, (80, 80, 80), (int((SCREEN_WIDTH - width)/2), int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + 8), (int((SCREEN_WIDTH - width)/2) + width, int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + 8), 2)

        # Exit Button
        exit_btn.draw()
        overlay.blit(title_text, (int((SCREEN_WIDTH - width) / 2) + (width - title_text.get_width()) / 2, int((SCREEN_HEIGHT - height) / 2) + 10))

        # Status
        overlay.blit(pc_status, (int((SCREEN_WIDTH - width)/2) + 30, int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + 15))
        if pc_stat:
            overlay.blit(usage_text, (int((SCREEN_WIDTH - width)/2) + 30, int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + 30 + pc_status.get_height()))
            disk_usage.draw()
            pygame.draw.circle(overlay, (20,255,20), (int((SCREEN_WIDTH - width)/2) + pc_status.get_width() + 60, int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + int(pc_status.get_height()/2) + 15), stat_radius)
        else:
            pygame.draw.circle(overlay, (255,20,20), (int((SCREEN_WIDTH - width)/2) + pc_status.get_width() + 60, int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + int(pc_status.get_height()/2) + 15), stat_radius)

        if plex_server:
            overlay.blit(plex_status, (int((SCREEN_WIDTH - width)/2) + width/2 - 70, int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + 15))
            if plex_stat:
                pygame.draw.circle(overlay, (20,255,20), (int((SCREEN_WIDTH - width)/2) + int(width/2) + plex_status.get_width() - 40, int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + int(plex_status.get_height()/2) + 15), stat_radius)
            else:
                pygame.draw.circle(overlay, (255,20,20), (int((SCREEN_WIDTH - width)/2) + int(width/2) + plex_status.get_width() - 40, int((SCREEN_HEIGHT - height)/2) + title_text.get_height() + int(plex_status.get_height()/2) + 15), stat_radius)


        refresh_status_btn.draw()


        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP and time.clock() - start > 0.4:
                if exit_btn.onHover() or not rect.collidepoint(pygame.mouse.get_pos()):
                    running = False

                if reboot_btn.onHover() and plex_server:
                    # TODO: Actually make it reboot the computer
                    print("REBOOT")
                    if confirmation_screen("reboot the plex host computer", overlay):
                        print("ACTUALLY REBOOTING COMPUTER")

                if restart_plex.onHover() and plex_server:
                    # TODO: Actually make it restart plex
                    print("RESTART")
                    if confirmation_screen("restart the plex instance?", overlay):
                        print("ACTUALLY RESTARING PLEX")

                if refresh_status_btn.onHover():
                    print("Checking Status")
                    print(check_statuses())

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.blit(overlay, (0, 0))
        pygame.display.update()

    screen.blit(bg, (0, 0))
    pygame.display.update()

def donwloads_screen():
    running = True
    bg = screen_copy
    start = time.clock()
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA, 32)
    overlay.set_alpha(150)
    # Main Body
    width = 700
    height = 750
    body_rect = pygame.Rect(int((SCREEN_WIDTH-width)/2), int((SCREEN_HEIGHT-height)/2), width, height)
    body = RoundedRectangle(body_rect.x, body_rect.y, body_rect.w, body_rect.h, 5, (120, 120, 240, 240), hover_enabled=False, surf=overlay)
    # Exit Button
    exit_size = 40
    padding = 12
    exit_rect = pygame.Rect(int((SCREEN_WIDTH-width)/2) + width - exit_size - padding, int((SCREEN_HEIGHT-height)/2) + padding, exit_size, exit_size)
    exit_btn = RoundedRectangle(exit_rect.x, exit_rect.y, exit_rect.w, exit_rect.h, 10, (245, 66, 100), surf=overlay)
    # Refresh Button
    refresh_rect = pygame.Rect(int((SCREEN_WIDTH - width) / 2) + padding, int((SCREEN_HEIGHT - height) / 2) + padding, 130, exit_size)
    reset_btn = RoundedRectangle(refresh_rect.x, refresh_rect.y, refresh_rect.w, refresh_rect.h, 10, (245, 66, 100), surf=overlay, text="Refresh", font_size=28)

    # Text
    title_font = pygame.font.SysFont(gui_font, 48)
    title = title_font.render("Torrents", True, (30, 30, 30))

    prog = ProgressBar(600, 100, 93, surf=overlay)

    while running:
        screen.blit(bg, (0, 0))

        body.draw()
        exit_btn.draw()
        reset_btn.draw()
        pygame.draw.line(overlay, (30, 30, 30, 220), (body_rect.x, body_rect.y + padding*2 + exit_size), (body_rect.x + body_rect.w - 1, body_rect.y + padding*2 + exit_size), 2)
        prog.draw()

        overlay.blit(title, (body_rect.x + (body_rect.w - title.get_width())/2, body_rect.y + 10))
        screen.blit(overlay, (0, 0))

        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP and time.clock() - start > 0.4:
                if not body_rect.collidepoint(pygame.mouse.get_pos()):
                    running = False
                    screen.blit(bg, (0,0))
                if exit_btn.onHover():
                    running = False
                    screen.blit(bg, (0, 0))

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.update()


def get_yify_data(movie):
    link = movie.link
    resolutions, magnets = [], []
    description, trailer_link = '', ''
    # [likes, RT Critics, RT Audience, IMDB]
    ratings, images = [], []

    try:
        start = time.clock()
        req = Request(link, headers=hdr)
        html = urlopen(req)
        soup = BeautifulSoup(html.read(), 'html.parser')
    except:
        print("Unable to get Movie Data")
    else:
        print("Time to retrieve Page: %.2fs" %(time.clock() - start))

        # Parse Resolutions
        raw_resolutions = soup.findAll('p', class_="hidden-md hidden-lg")
        resolutions = raw_resolutions[0].text.split("\n")
        while '' in resolutions:
            resolutions.remove('')
        for i in range(len(resolutions)):
            resolutions[i] = resolutions[i].replace(".", " ")

        # Parse magnet links
        raw_magnets = soup.findAll('a')
        for data in raw_magnets:
            data = data.get('href')
            if "magnet" in data:
                magnets.append(data)
        print("Magnets Found:", len(magnets), resolutions)

        description = soup.find('p', class_="hidden-sm hidden-md hidden-lg").text[1:]

        # Parse Ratings
        raw_ratings = soup.findAll('div', class_="rating-row")
        ratings = []
        for rating in raw_ratings:
            ratings.append(rating.text)
        for rate in range(len(ratings)):
            ratings[rate] = ratings[rate].replace('\n', '')
            ratings[rate] = ratings[rate].replace(' ', '')

        print(ratings)
        ratings = ratings[:-1]
        temp = ''
        for rating in range(1,len(ratings)):
            temp = ''
            for char in range(len(ratings[rating])):
                temp += ratings[rating][char]
                if ratings[rating][char] == "%":
                    ratings[rating] = temp
                    break
                if ratings[rating][char] == ".":
                    temp += ratings[rating][char + 1]
                    ratings[rating] = temp
                    break
            if rating == len(ratings)-1:
                if not '.' in ratings[rating]:
                    ratings[rating] = ratings[rating][0] + '.0'
        print(ratings)
        # Rating Images
        raw_images = soup.findAll('a', class_="icon")
        raw_images = raw_images[:-1]
        if raw_images:
            for img in raw_images:
                images.append(img.find('img')['src'])

        # Parse trailer Link

        trailer_link = soup.find('div', class_="screenshot").find('a', class_="youtube")['href']
        print(trailer_link)

    return resolutions, magnets, description, ratings, images, trailer_link

def recommended_movies(link, background):
    bg = background
    try:
        start = time.clock()
        req = Request(link, headers=hdr)
        html = urlopen(req)
        soup = BeautifulSoup(html.read(), 'html.parser')
    except:
        print("Unable to get Movie Data")
    else:
        print("Time to retrieve Page: %.2fs" %(time.clock() - start))

        # Get names and image URLs
        raw_movies = soup.find('div', id="movie-related").findAll('a')
        rec_movies = []
        for movie in raw_movies:
            title = movie['title']
            img_link = movie.find('img')['src']
            link = movie['href']
            rec_movies.append(Movie(title, link, img_link))

        load_movie_images(rec_movies)

    running = True
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA, 32)

    body_rect = pygame.Rect(10, (SCREEN_HEIGHT - 500)/2, SCREEN_WIDTH - 20, 430)
    spacing = 20
    char_lim = 20
    font = pygame.font.SysFont(gui_font, 20)

    while running:
        screen.blit(bg, (0, 0))
        pygame.draw.rect(overlay,  (40, 95, 174, 200), body_rect)

        for movie in range(len(rec_movies)):
            name = rec_movies[movie].name
            name = textwrap.fill(name, char_lim)
            name = name.split("\n")
            text_list = []
            for word in range(len(name)):
                text = font.render(name[word], True, (0, 0, 0), (255,255,255))
                text_list.append(text)
                # Title
                overlay.blit(text, (body_rect.x + 30 + (rec_movies[movie].image.get_width() + spacing) * movie + (rec_movies[movie].image.get_width() - text.get_width())/2, body_rect.y + 35 + rec_movies[movie].image.get_height() + 22*word))
            # Cover
            overlay.blit(rec_movies[movie].image, (body_rect.x + 30 + (rec_movies[movie].image.get_width() + spacing)*movie, body_rect.y + 30))

            pos = pygame.mouse.get_pos()
            if pos[0] > body_rect.x + 30 + (rec_movies[movie].image.get_width() + spacing)*movie and pos[0] < body_rect.x + 30 + (rec_movies[movie].image.get_width() + spacing)*movie + rec_movies[movie].image.get_width():
                if pos[1] > body_rect.y + 30 and pos[1] < body_rect.y + 30 + rec_movies[movie].image.get_height():
                    if pygame.mouse.get_pressed()[0]:
                        while(pygame.mouse.get_pressed()[0]):
                            pygame.event.get()
                        running = False
                        movie_preview(rec_movies[movie])

        if running:
            screen.blit(overlay, (0, 0))

        clock.tick()
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP and not body_rect.collidepoint(pygame.mouse.get_pos()):
                running = False

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()

def movie_preview(movie):
    running = True
    resolutions, links, description, ratings, images, trailer = get_yify_data(movie)
    rotten_imgs = []
    if len(resolutions) != len(links):
        print("SOMETHING IS WRONG \n RESOLUTIONS DO NOT MATCH LINKS")

    print("Images Parsed:", len(images))
    if images:
        print("Loading Images", images)
        for img in images:
            req = Request(url='http://yts.am'+img, headers=hdr)
            rotten_imgs.append(pygame.image.load(io.BytesIO(urlopen(req).read())))

    rotten_imgs.insert(0, pygame.image.load('resources/heart.png').convert_alpha())
    rotten_imgs.append(pygame.image.load('resources/imdb_logo.png').convert_alpha())

    rotten_imgs[0] = pygame.transform.smoothscale(rotten_imgs[0], (25,25))
    rotten_imgs[-1] = pygame.transform.smoothscale(rotten_imgs[-1], (50, 25))
    background = screen.copy()

    print(len(rotten_imgs))

    # Scale images
    size = (int(movie.img_size[0]*1.2), int(movie.img_size[1]*1.2))
    image = pygame.transform.smoothscale(movie.image, size)
    font = pygame.font.SysFont(gui_font, 44)
    dl_font = pygame.font.SysFont(gui_font, 32)
    desc_font = pygame.font.SysFont(gui_font, 22)
    synopsis_font = pygame.font.SysFont(gui_font + " Bold", 34)
    synopsis_text = synopsis_font.render("Synopsis", True, (20, 20, 20))

    title_text = []
    movie_name = textwrap.fill(movie.name, 40)
    movie_name = movie_name.split('\n')
    for i in movie_name:
        title_text.append(font.render(i, True, (40, 40, 40)))

    rec_movies = synopsis_font.render("Recommended", True, (20, 20, 20))
    back = font.render("Back", True, (40,40,40))
    start = time.clock()
    while running:
        background = screen.copy()
        screen.fill(bg_color)

        bottom_text_y = 10
        for text in range(len(title_text)):
            screen.blit(title_text[text], ((SCREEN_WIDTH - title_text[text].get_width())/2, bottom_text_y + 5))
            bottom_text_y += title_text[text].get_height() + 5

        screen.blit(image, (30, bottom_text_y + 40))

        # Description

        if description != '':
            desc_text = textwrap.fill(description, 92)
            desc_text = desc_text.split("\n")
            screen.blit(synopsis_text, (30, bottom_text_y + 45 + size[1] ))
            for line in range(len(desc_text)):
                text = desc_font.render(desc_text[line], True, (30,30,30))
                screen.blit(text, (30, bottom_text_y + 75 + size[1] + 22*line))

        # Ratings
        if ratings:
            for rate in range(len(rotten_imgs)):
                rating = desc_font.render(ratings[rate], True, (30,30,30))
                screen.blit(rotten_imgs[rate], (775 - rotten_imgs[rate].get_width() - 10, bottom_text_y + 40 + 40 * rate))
                screen.blit(rating, (775, bottom_text_y + 40 + (rotten_imgs[rate].get_height() - rating.get_height())/2 + 1 + 40*rate))

        pos = pygame.mouse.get_pos()

        # Trailer Button
        if trailer != '':
            trailer_text = synopsis_font.render("Trailer", True, (20, 20,20))
            if pos[0] > SCREEN_WIDTH - 120 and pos[0] < SCREEN_WIDTH-20 and pos[1] > image.get_height() + bottom_text_y and pos[1] < image.get_height() + bottom_text_y + 40:
                pygame.draw.rect(screen, (65, 175, 45),(SCREEN_WIDTH - 120, image.get_height() + bottom_text_y, 100, 40))
                if pygame.mouse.get_pressed()[0] and time.clock() - start > 0.3:
                    webbrowser.open(trailer, autoraise=True)
                    start = time.clock()
            else:
                pygame.draw.rect(screen, (50, 160, 30), (SCREEN_WIDTH - 120, image.get_height() + bottom_text_y, 100, 40))
            screen.blit(trailer_text, (SCREEN_WIDTH - 120 + (100 - trailer_text.get_width()) / 2, image.get_height() + bottom_text_y + trailer_text.get_height()/2 - 2))

        # Recommended Movies Button
        #FIXME: Clicks too fast. Implement while loop, go back to recommendation and break!
        if pos[0] > SCREEN_WIDTH - 200 and pos[0] < SCREEN_WIDTH - 20 and pos[1] > image.get_height() + bottom_text_y - 50 and pos[1] < image.get_height() + bottom_text_y - 10:
            pygame.draw.rect(screen, (155, 160, 255), (SCREEN_WIDTH - 200, image.get_height() + bottom_text_y - 50, 180, 40))
            if pygame.mouse.get_pressed()[0]:
                while pygame.mouse.get_pressed()[0]:
                    pygame.event.get()
                recommended_movies(movie.link, background)
        else:
            pygame.draw.rect(screen, (140, 145, 255), (SCREEN_WIDTH - 200, image.get_height() + bottom_text_y - 50, 180, 40))
        screen.blit(rec_movies, (SCREEN_WIDTH - 200 + (180 - rec_movies.get_width()) / 2, image.get_height() + bottom_text_y - 50 + (40 - rec_movies.get_height())/2 ))

        # Back Button
        pygame.draw.rect(screen, (190, 30, 50), (SCREEN_WIDTH - 160, SCREEN_HEIGHT - 70, 140, 50))
        if pos[0] > SCREEN_WIDTH - 160 and pos[0] < SCREEN_WIDTH - 20:
            if pos[1] > SCREEN_HEIGHT - 70 and pos[1] < SCREEN_HEIGHT - 20:
                pygame.draw.rect(screen, (205, 45, 65), (SCREEN_WIDTH - 160, SCREEN_HEIGHT - 70, 140, 50))
                if pygame.mouse.get_pressed()[0]:
                    time.sleep(0.05)
                    running = False
        screen.blit(back, ((SCREEN_WIDTH - 160 + (140 - back.get_width())/2), SCREEN_HEIGHT - 68 + (50 - back.get_height())/2))

        # Display Links
        total_link_height = len(resolutions) * 60 - 10

        for download in range(len(resolutions)):
            dl_res = dl_font.render(resolutions[download], True, (220, 220, 220))
            pos_rect = pygame.Rect(SCREEN_WIDTH / 2 - dl_res.get_width() / 2 - 10, (bottom_text_y + 40 + (size[1] - total_link_height) / 2) + 60 * download, dl_res.get_width() + 20, dl_res.get_height() + 10)
            pygame.draw.rect(screen, (80, 80, 80), (pos_rect.x - 2, pos_rect.y - 2, pos_rect.w + 4, pos_rect.h + 4))
            pygame.draw.rect(screen, (40, 40, 40), pos_rect)
            screen.blit(dl_res, (pos_rect.x + (pos_rect.w - dl_res.get_width()) / 2, pos_rect.y + (pos_rect.h - dl_res.get_height()) / 2))

            pos = pygame.mouse.get_pos()
            if pos[0] > pos_rect.x and pos[0] < pos_rect.x + pos_rect.w:
                if pos[1] > pos_rect.y and pos[1] < pos_rect.y + pos_rect.h:
                    pygame.draw.rect(screen, (120, 120, 120),(pos_rect.x - 2, pos_rect.y - 2, pos_rect.w + 4, pos_rect.h + 4))
                    pygame.draw.rect(screen, (80, 80, 80), pos_rect)
                    screen.blit(dl_res, (pos_rect.x + (pos_rect.w - dl_res.get_width()) / 2, pos_rect.y + (pos_rect.h - dl_res.get_height()) / 2))
                    if pygame.mouse.get_pressed()[0] and time.clock() - start > 0.5:
                        dl_confirmed = confirmation_screen('confirm this download', background)
                        if dl_confirmed:
                            # TODO: Enable actual Downloading
                            print(resolutions[download], links[download])
                            running = False

        if pygame.key.get_pressed()[pygame.K_BACKSPACE]:
            time.sleep(0.05)
            running = False


        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()
    time.sleep(0.1)


# Input boxes - Movie
textInput_movie = InputBox(10, 10, SCREEN_WIDTH - 65, 35, "Search")

# TV Shows
textInput_tv = InputBox(10, 10, SCREEN_WIDTH - 220, 35, "Search")
textInput_season = InputBox(SCREEN_WIDTH - 200, 10, 70, 35, "S:", show_icon=False)
textInput_episode = InputBox(SCREEN_WIDTH - 125, 10, 70, 35, "E:", show_icon=False)

def draw_header():
    pygame.draw.rect(screen, (40, 40, 40), (0, 0, SCREEN_WIDTH, 90))
    if mode_select.movie_mode:
        textInput_movie.draw(screen)
    else:
        textInput_tv.draw(screen)
        textInput_season.draw(screen)
        textInput_episode.draw(screen)

    font = pygame.font.SysFont(gui_font, 26)
    if disp_mode == 'thumb':
        result_text = font.render("Results Found: " + str(total_movies), True, (230, 230, 230))
    else:
        result_text = font.render("Results Found: " + str(len(movies)), True, (230, 230, 230))

    screen.blit(result_text, (505, 56))
    user_buttons()


extensive_search = CheckBox(230, 57, "Extensive Search")
fast_search = CheckBox(385, 57, "Fast Search")
mode_select = ModeSelector(10, 53)
setting_box = RoundedRectangle(SCREEN_WIDTH - 45, 10, 35, 35, 0, (130, 90, 95))
download_btn = RoundedRectangle(SCREEN_WIDTH - 130, 53, 120, 30, 4, (90, 90, 176), text="Downloads", font_size=25)
def user_buttons():
    if not mode_select.movie_mode:
        extensive_search.active = True
    extensive_search.draw()
    fast_search.draw()
    mode_select.draw()

    # Settings Icon
    setting_box.draw()
    screen.blit(gear, (SCREEN_WIDTH - 44, 11))
    if setting_box.onHover() and pygame.mouse.get_pressed()[0]:
        settings_screen()
    # Downloads button
    download_btn.draw()
    if download_btn.onHover() and pygame.mouse.get_pressed()[0]:
        donwloads_screen()

torrents = []
disp_mode = 'thumb'
page, scroll_offset = 1, 0
running = True
while running:

    if movies:
        if disp_mode == 'thumb':
            scroll_offset = 0
            page = show_movies(movies, all_movies, total_movies, page)
        else:
            show_links(movies, scroll_offset, screen_copy)
    else:
        page = 1

    draw_header()
    screen_copy = screen.copy()

    clock.tick(FPS)
    for event in pygame.event.get():
        if mode_select.movie_mode:
            movies, all_movies, total_movies = textInput_movie.handle_event(event)
        else:
            _ = textInput_episode.handle_event(event)
            _ = textInput_season.handle_event(event)
            _ = textInput_tv.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if movies and disp_mode == 'list':
                if event.button == 5 and scroll_offset < 80*len(movies) - SCREEN_HEIGHT + 90:
                    scroll_offset += 10
                if event.button == 4 and scroll_offset >= 10:
                    scroll_offset -= 10

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.update()