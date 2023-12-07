from turtle import width
import pygame 
import random
import copy
import tkinter as tk
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN_BLUE = (0, 153, 153)
LIGHT_GRAY = (192, 192, 192)
RED = (255, 0, 0)


block_size = 50
left_margin = 5 * block_size
upper_margin = 2 * block_size

size = (left_margin + 30 * block_size, upper_margin + 15 * block_size)
letters = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И', 'К']

pygame.init()

screen = pygame.display.set_mode(size)
pygame.display.set_caption("Морской бой")

font_size = int(block_size / 1.5)
font = pygame.font.SysFont('notosans', font_size)
game_over_font_size = block_size
game_over_font = pygame.font.SysFont('notosans', game_over_font_size)

around_last_computer_hit_set = set()
compueter_available_to_fire_set = set((x,y)for x in range(16,26) for y in range (1, 11))
hit_blocks = set() #поражённые клетки
dotted_set = set() #множество с точками
dotted_set_for_computer_not_to_shoot = set() #множество всех клеток, в которые не нужно стрелять
hit_blocks_for_computer_not_to_shoot = set() #те клетки, в которые компьютер уже попадал
last_hits_list = [] #список прошлого попадания компьютера
destroyed_computer_ships = [] #список для всех потопленных кораблей


#класс для построения кораблей
class AutoShips:
    def __init__(self, offset):
        self.offset = offset
        self.available_blocks = {(x, y) for x in range(1+self.offset, 11+self.offset) for y in range(1, 11)} #свободные клетки
        self.ships_set = set() #координаты клеток, занятых кораблями
        self.ships = self.populate_grid()

    #выбор стартовой клетки
    def create_start_block(self, available_blocks):
        x_or_y = random.randint(0, 1) #0 - горизонтальный корабль, 1 - вертикальный
        str_rev = random.choice((-1, 1)) #вправо или влево, вниз или вверх
        x, y = random.choice(tuple(available_blocks)) #начальная клетка
        return x, y, x_or_y, str_rev 
    
    #создание корабля
    def create_ship(self, number_of_blocks, available_blocks):
        ship_coordinates = []
        x, y, x_or_y, str_rev = self.create_start_block(available_blocks)
        for _ in range (number_of_blocks):
            ship_coordinates.append((x,y))
            #проверка границ игрового поля
            if not x_or_y:
                str_rev, x = self.get_new_block_for_ship(x, str_rev, x_or_y, ship_coordinates)
            else: 
                str_rev, y = self.get_new_block_for_ship(y, str_rev, x_or_y, ship_coordinates)
        #проверка построения
        if self.is_ship_valid(ship_coordinates):
            return ship_coordinates #возвращаем координаты корабля
        return self.create_ship(number_of_blocks, available_blocks) #запуск функции заново
    
    def get_new_block_for_ship(self, coor, str_rev, x_or_y, ship_coordinates):
        if (coor <= 1-self.offset*(x_or_y-1) and str_rev == -1) or (coor >= 10-self.offset*(x_or_y-1) and str_rev == 1):
            str_rev *= -1
            return str_rev, ship_coordinates[0][x_or_y] + str_rev
        else:
            return str_rev, ship_coordinates[-1][x_or_y] + str_rev

    #проверка границ корабля
    def is_ship_valid(self, new_ship):
        ship = set(new_ship)
        return ship.issubset(self.available_blocks)
    
    #обновление списка координат кораблей 
    def add_new_ship_to_set(self, new_ship):
        self.ships_set.update(new_ship)
    
    #удаление клеток вокруг построенного корабля
    def update_available_blocks_for_creating_ships(self, new_ship):
        for elem in new_ship:
            for k in range(-1, 2):
                for m in range(-1,2):
                    if 0+self.offset < (elem[0]+k) < 11+self.offset and 0 < (elem[1]+m) < 11:
                        self.available_blocks.discard((elem[0]+k, elem[1]+m))
            
    #вложенный список из списков координатов
    def populate_grid(self):
        ships_coordinates_list = []
        for number_of_blocks in range(4, 0, -1):
            for _ in range(5-number_of_blocks):
                new_ship = self.create_ship(number_of_blocks, self.available_blocks) #создание нового корабля
                ships_coordinates_list.append(new_ship) #добавить координаты нового корабля в общий список 
                self.add_new_ship_to_set(new_ship) #добавить координаты клетки в общий список
                self.update_available_blocks_for_creating_ships(new_ship) #обновить общий список свободных клеток
        return ships_coordinates_list
        
class Button:
    def __init__(self, x_offset, button_title, message_to_show):
        self.__title = button_title # название кнопки (title)
        self.__title_width, self.__title_height = font.size(self.__title)
        self.__message = message_to_show #пояснительное сообщение для печати на экране
        self.__button_width = self.__title_width + block_size
        self.__button_height = self.__title_height + block_size
        self.__x_start = x_offset #смещение по горизонтали, с которого начинается кнопка рисования
        self.__y_start = upper_margin + 10 * block_size + self.__button_height #смещение по вертикали, с которого следует начать рисование кнопки
        self.rect_for_draw = self.__x_start, self.__y_start, self.__button_width, self.__button_height #кортеж из четырех целых чисел: прямоугольник кнопки, который нужно нарисовать
        self.rect = pygame.Rect(self.rect_for_draw)
        self.__rect_for_button_title = self.__x_start + self.__button_width / 2 - \
            self.__title_width / 2, self.__y_start + \
            self.__button_height / 2 - self.__title_height / 2
        self.__color = BLACK

    #Рисует кнопку в виде цветного прямоугольника (по умолчанию ЧЕРНЫЙ)
    def draw_button(self, color=None):
        if not color:
            color = self.__color
        pygame.draw.rect(screen, color, self.rect_for_draw)
        text_to_blit = font.render(self.__title, True, WHITE)
        screen.blit(text_to_blit, self.__rect_for_button_title)
    
    #Рисует кнопку в виде прямоугольника ЗЕЛЕНО-синего цвета
    def change_color_on_hover(self):
        mouse = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse):
            self.draw_button(GREEN_BLUE)

    #Печатает пояснительное сообщение рядом с кнопкой
    def print_message_for_button(self):
        message_width, message_height = font.size(self.__message)
        rect_for_message = self.__x_start / 2 - message_width / 2, self.__y_start + self.__button_height / 2 - message_height / 2
        text = font.render(self.__message, True, BLACK)
        screen.blit(text, rect_for_message)
    
class Grid:
    def __init__(self, title, offset):
        self.title = title
        self.offset = offset
        self.render()

    def render(self):
        self.draw_grid()
        self.add_nums_letters_to_grid()
        self.sign_grids()

    def draw_grid(self):
        for i in range(11):
            # Horizontal lines
            pygame.draw.line(screen, BLACK, (left_margin + self.offset * block_size, upper_margin + i * block_size),
                             (left_margin + (10 + self.offset) * block_size, upper_margin + i * block_size), 1)
            # Vertical lines
            pygame.draw.line(screen, BLACK, (left_margin + (i + self.offset) * block_size, upper_margin),
                             (left_margin + (i + self.offset) * block_size, upper_margin + 10 * block_size), 1)
    def add_nums_letters_to_grid(self):
        for i in range(10):
            num_ver = font.render(str(i + 1), True, BLACK)
            letters_hor = font.render(letters[i], True, BLACK)
            num_ver_width = num_ver.get_width()
            num_ver_height = num_ver.get_height()
            letters_hor_width = letters_hor.get_width()

            # Numbers (vertical)
            screen.blit(num_ver, (left_margin - (block_size // 2 + num_ver_width // 2) + self.offset * block_size,
                                  upper_margin + i * block_size + (block_size // 2 - num_ver_height // 2)))
            # Letters (horizontal)
            screen.blit(letters_hor, (left_margin + i * block_size + (block_size // 2 - letters_hor_width // 2) +
                                      self.offset * block_size,
                                      upper_margin + 10 * block_size))
    #подписывание сеток
    def sign_grids(self):
        player = font.render(self.title(), True, BLACK)
        sign_width = player.get_width()
        surf = pygame.Surface((left_margin + 5*block_size - sign_width //2+self.offset*block_size, upper_margin - block_size//2 - font_size))
        surf.fill(WHITE)
        screen.blit(surf, (left_margin + 5*block_size - sign_width //2+self.offset*block_size, upper_margin - block_size//2 - font_size))
        screen.blit(player, (left_margin + 5*block_size - sign_width //2+self.offset*block_size, upper_margin - block_size//2 - font_size))

#рисование кораблей
def draw_ships(ships_coordinates_list):
    for elem in ships_coordinates_list:
        ship = sorted(elem)
        x_start = ship[0][0]
        y_start = ship[0][1]
        #горизонтальный и одноблочный корабль
        ship_wedth = block_size * len(ship)
        ship_height = block_size
        #вертикальные корабли
        if len(ship) > 1 and ship[0][0] == ship[1][0]:
            ship_wedth, ship_height = ship_height, ship_wedth  
        #преобразование координат в координаты по пикселям
        x = block_size *(x_start - 1) + left_margin
        y = block_size *(y_start - 1) + upper_margin
        #прорисовка кораблей
        pygame.draw.rect(screen, BLACK, ((x, y), (ship_wedth, ship_height)), width=block_size//10)
        
#метод для стрельбы компьютера
def computer_shoots(set_to_shoot_from):

    computer_fired_block = random.choice(tuple(set_to_shoot_from)) #клетка, в которую выстрелили
    return computer_fired_block


#проверка выстрела (удачный или неудачный) и для компьютера, и для пользователя
def check_hit_or_miss(fired_block, opponents_ships_list, computer_turn, opponents_ships_list_original_copy, opponents_ships_set, computer):
    #проходим по сиску кораблей и проверяем попали или нет
    for elem in opponents_ships_list:
        diagonal_only = True
        if fired_block in elem:
            ind = opponents_ships_list.index(elem)
            if len(elem) == 1:
                diagonal_only = False
            update_dotted_and_hit_sets(fired_block, computer_turn, diagonal_only) #ставим точки по диагонали
            elem.remove(fired_block)
            opponents_ships_set.discard(fired_block)
            if computer_turn:
                last_hits_list.append(fired_block) #записываем клетку, в которую комп. попал
                update_around_last_computer_hit(fired_block, True)
            if not elem:
                update_destroyed_ships(ind, computer_turn, opponents_ships_list_original_copy)
                if computer_turn:
                    last_hits_list.clear()
                    around_last_computer_hit_set.clear()
                else:
                    destroyed_computer_ships.append(computer.ships[ind])
            return True
    add_missed_block_to_dotted_set(fired_block)
    if computer_turn:
        update_around_last_computer_hit(fired_block, False)
    return False
    
def check_hit_or_miss_ships(fired_block, opponents_ships_list):
    #проходим по сиску кораблей и проверяем попали или нет
    for elem in opponents_ships_list:
        if fired_block in elem:
            return True
    return False

#рисование не попадания в корабль
def add_missed_block_to_dotted_set(fired_block):
    dotted_set.add(fired_block)
    dotted_set_for_computer_not_to_shoot.add(fired_block)

#добавление разрушенных кораблей в список
def update_destroyed_ships(ind, computer_turn, opponents_ships_list_original_copy):
    ship = sorted(opponents_ships_list_original_copy[ind])
    for i in range (-1, 1):
        update_dotted_and_hit_sets(ship[i], computer_turn, False)


#обновление клеток возле последнего попадания компьютера
def update_around_last_computer_hit(fired_block, computer_hits):
    global around_last_computer_hit_set, compueter_available_to_fire_set
    #если компьютер попал в корабль, в который он ранее попадал
    if computer_hits and fired_block in around_last_computer_hit_set:
        around_last_computer_hit_set = computer_hits_twice()

    #компьютерр попал, но попал первый раз
    elif computer_hits and fired_block not in around_last_computer_hit_set:
        computer_first_hit(fired_block)
        
    #если компьютер стрелял мимо
    elif not computer_hits:
        around_last_computer_hit_set.discard(fired_block)
 
    around_last_computer_hit_set -= dotted_set_for_computer_not_to_shoot
    around_last_computer_hit_set -= hit_blocks_for_computer_not_to_shoot
    compueter_available_to_fire_set -= around_last_computer_hit_set
    compueter_available_to_fire_set -= dotted_set_for_computer_not_to_shoot

def computer_hits_twice():
    last_hits_list.sort()
    new_around_last_hit_set = set()
    for i in range(len(last_hits_list)-1):
        x1 = last_hits_list[i][0]
        x2 = last_hits_list[i+1][0]
        y1 = last_hits_list[i][1]
        y2 = last_hits_list[i+1][1]
        if x1 == x2:
            if y1 > 1:
                new_around_last_hit_set.add((x1, y1 - 1))
            if y2 < 10:
                new_around_last_hit_set.add((x1, y2 + 1))
        elif y1 == y2:
            if x1 > 16:
                new_around_last_hit_set.add((x1 - 1, y1))
            if x2 < 25:
                new_around_last_hit_set.add((x2 + 1, y1))
    return new_around_last_hit_set

def computer_first_hit(fired_block):
    xhit, yhit = fired_block
    if xhit > 16:
        around_last_computer_hit_set.add((xhit-1, yhit))
    if xhit < 25:
        around_last_computer_hit_set.add((xhit+1, yhit))
    if yhit > 1:
        around_last_computer_hit_set.add((xhit, yhit-1))
    if yhit < 10:
        around_last_computer_hit_set.add((xhit, yhit+1))

#обнoвление списка со всеми точками и обновление множества, в котором находятся клетки с точками у человека (для понимания комп. куда не нужно стрелять)
#также обновление тех клеток, в которых нужно рисовать крестики
def update_dotted_and_hit_sets(fired_block, computer_turn, diagonal_only = True):
    global dotted_set
    x, y = fired_block
    a = 15 * computer_turn
    b = 11+15*computer_turn
    hit_blocks_for_computer_not_to_shoot.add(fired_block)
    hit_blocks.add(fired_block)
    for i in range(-1, 2):
        for j in range(-1, 2):
            if (not diagonal_only or i != 0 and j != 0) and a < x + i < b and 0 < y + j < 11:
                add_missed_block_to_dotted_set((x + i, y + j))
    dotted_set -= hit_blocks

def draw_from_dotted_set(dotted_set):
    for elem in dotted_set:
        pygame.draw.circle(screen, BLACK, (block_size * (elem[0]-0.5)+left_margin, block_size*(elem[1]-0.5)+upper_margin), block_size//6)

def draw_hit_blocks(hit_blocks):
    for block in hit_blocks:
        x1 = block_size * (block[0]-1) + left_margin
        y1 = block_size * (block[1]-1) + upper_margin
        pygame.draw.line(screen, BLACK, (x1, y1), (x1+block_size, y1+block_size), block_size//6)
        pygame.draw.line(screen, BLACK, (x1, y1+block_size), (x1+block_size, y1), block_size//6)
    
#функция для вывода окна "Вы проиграли\выиграли"
def show_message_at_rect_center(message, rect, which_font=font, color=RED):
    message_width, message_height = which_font.size(message)
    message_rect = pygame.Rect(rect)
    x_start = message_rect.centerx - message_width / 2
    y_start = message_rect.centery - message_height / 2
    background_rect = pygame.Rect(
        x_start - block_size / 2, y_start, message_width + block_size, message_height)
    message_to_blit = which_font.render(message, True, color)
    screen.fill(WHITE, background_rect)
    screen.blit(message_to_blit, (x_start, y_start))

def ship_is_valid(ship_set, blocks_for_manual_drawing):
    return ship_set.isdisjoint(blocks_for_manual_drawing)

#проверка количества кораблей
def check_ships_numbers(ship, num_ships_list):
    return (5 - len(ship)) > num_ships_list[len(ship)-1]

def update_used_blocks(ship, method):
    for block in ship:
        for i in range(-1, 2):
            for j in range(-1, 2):
                method((block[0]+i, block[1]+j))


#human = AutoShips(15)
#human_ships_working = copy.deepcopy(human.ships)

auto_button_place = left_margin + 17 * block_size
manual_button_place = left_margin + 20 * block_size
how_to_create_ships_message = "Как вы хотите создать корабли? Нажмите кнопку"
auto_button = Button(auto_button_place, "АВТО", how_to_create_ships_message)
manual_button = Button(manual_button_place, "ВРУЧНУЮ",
                       how_to_create_ships_message)
undo_message = "Для отмены последнего корабля нажмите кнопку"
undo_button_place = left_margin + 12 * block_size
undo_button = Button(undo_button_place, "ОТМЕНА", undo_message)

def calc_score(contract):
    if contract == 1:
        return 50
    elif contract == 2:
        return 75
    elif contract ==3:
        return 130
    else:
        return contract * 50

def main():

    game_close = False
    while game_close == False:
        global around_last_computer_hit_set
        around_last_computer_hit_set = set()
        global compueter_available_to_fire_set 
        compueter_available_to_fire_set = set((x,y)for x in range(16,26) for y in range (1, 11))
        global hit_blocks
        hit_blocks= set() #поражённые клетки
        global dotted_set
        dotted_set = set() #множество с точками
        global dotted_set_for_computer_not_to_shoot
        dotted_set_for_computer_not_to_shoot = set() #множество всех клеток, в которые не нужно стрелять
        global hit_blocks_for_computer_not_to_shoot
        hit_blocks_for_computer_not_to_shoot = set() #те клетки, в которые компьютер уже попадал
        global last_hits_list
        last_hits_list = [] #список прошлого попадания компьютера
        global destroyed_computer_ships
        destroyed_computer_ships = [] #список для всех потопленных кораблей
        computer = AutoShips(0)
        computer_ships_working =copy.deepcopy(computer.ships)
        ships_creation_not_decided = True
        ships_not_created = True
        drawing = False
        game_over = False
        computer_turn = False #очередь стрелять компьютера
        start = (0 ,0)
        ship_size = (0, 0)
        rect_for_grids = (0, 0, size[0], upper_margin + 12 * block_size)
        rect_for_messages_and_buttons = (
            0, upper_margin + 11 * block_size, size[0], 5 * block_size)
        message_rect_for_drawing_ships = (undo_button.rect_for_draw[0] + undo_button.rect_for_draw[2], upper_margin + 11 * block_size, size[0]-
            (undo_button.rect_for_draw[0] + undo_button.rect_for_draw[2]), 4 * block_size)
        message_rect_computer = (left_margin - 2 * block_size, upper_margin +
                                11 * block_size, 14 * block_size, 4 * block_size)
        message_rect_human = (left_margin + 15 * block_size, upper_margin +
                            11 * block_size, 10 * block_size, 4 * block_size)

        human_ships_to_draw = []
        num_ships_list = [0, 0, 0, 0]
        human_ships_set = set()
        used_blocks_for_manual_drawing = set()
        computer_score = 0
        human_score = 0
        computer_contract = 0
        human_cotract = 0
        human_shield_count = 1
        human_shield = False
        computer_shield_count = 1
        computer_shield = False
        human_available_to_fire_set = set((x,y)for x in range(1,11) for y in range (1, 11))
        screen.fill(WHITE)
        computer_grid = Grid(lambda: f"КОМПЬЮТЕР: {computer_score} {'Щит' if computer_shield else ''}", 0)
        human_grid = Grid(lambda: f"ЧЕЛОВЕК: {human_score} {'Щит' if human_shield else ''}", 15)
        #draw_ships(computer.ships)
        #draw_ships(human.ships)
        pygame.display.update()

        while ships_creation_not_decided:
            auto_button.draw_button()
            manual_button.draw_button()
            auto_button.change_color_on_hover()
            auto_button.print_message_for_button()

            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                    ships_creation_not_decided = False
                    ships_not_created = False
                elif event.type == pygame.MOUSEBUTTONDOWN and auto_button.rect.collidepoint(mouse):
                    print("Clicked AUTO!", event.pos)
                    human = AutoShips(15)
                    human_ships_to_draw = human.ships
                    human_ships_set = human.ships_set
                    human_ships_working = copy.deepcopy(human.ships)
                    ships_creation_not_decided = False
                    ships_not_created = False
                elif event.type == pygame.MOUSEBUTTONDOWN and manual_button.rect.collidepoint(mouse):
                    ships_creation_not_decided = False

            pygame.display.update()
            screen.fill(WHITE, rect_for_messages_and_buttons)

        #построение кораблей вручную
        while ships_not_created:
            screen.fill(WHITE, rect_for_grids)
            computer_grid = Grid(lambda: f"КОМПЬЮТЕР: {computer_score} {'Щит' if computer_shield else ''}", 0)
            human_grid = Grid(lambda: f"ЧЕЛОВЕК: {human_score} {'Щит' if human_shield else ''}", 15)
            undo_button.draw_button()
            undo_button.print_message_for_button()
            undo_button.change_color_on_hover()
            mouse = pygame.mouse.get_pos()
            if not human_ships_to_draw:
                undo_button.draw_button(LIGHT_GRAY)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    ships_not_created = False
                    game_over = True
                elif undo_button.rect.collidepoint(mouse) and event.type == pygame.MOUSEBUTTONDOWN:
                    if human_ships_to_draw:
                        screen.fill(WHITE, message_rect_for_drawing_ships)
                        deleted_ship = human_ships_to_draw.pop()
                        num_ships_list[len(deleted_ship) - 1] -= 1
                        update_used_blocks(deleted_ship, used_blocks_for_manual_drawing.discard)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    drawing = True
                    x_start, y_start = event.pos
                    start = x_start, y_start
                    ship_size = (0, 0)
                elif drawing and event.type == pygame.MOUSEMOTION:
                    x_end, y_end = event.pos
                    end = x_end, y_end
                    ship_size = x_end - x_start, y_end - y_start
                elif drawing and event.type == pygame.MOUSEBUTTONUP:
                    x_end, y_end = event.pos
                    drawing = False
                    ship_size = (0, 0)
                    start_block = ((x_start - left_margin) // block_size + 1,
                                (y_start - upper_margin) // block_size + 1)
                    end_block = ((x_end - left_margin) // block_size + 1,
                                (y_end - upper_margin) // block_size + 1)
                    if start_block > end_block:
                        start_block, end_block = end_block, start_block
                    temp_ship = []
                    if 15 < start_block[0] < 26 and 0 < start_block[1] < 11 and 15 < end_block[0] < 26 and 0 < end_block[1] < 11:
                        screen.fill(WHITE, message_rect_for_drawing_ships)
                        if start_block[0] == end_block[0] and (end_block[1] - start_block[1]) < 4:
                            for block in range(start_block[1], end_block[1]+1):
                                temp_ship.append((start_block[0], block))
                        elif start_block[1] == end_block[1] and (end_block[0] - start_block[0]) < 4:
                            for block in range(start_block[0], end_block[0]+1):
                                temp_ship.append((block, start_block[1]))
                        else:
                            show_message_at_rect_center("КОРАБЛЬ СЛИШКОМ БОЛЬШОЙ!", message_rect_for_drawing_ships)
                    else:
                        show_message_at_rect_center("КОРАБЛЬ ЗА ПРЕДЕЛАМИ СЕТКИ!", message_rect_for_drawing_ships)
                    if temp_ship:
                        temp_ship_set = set(temp_ship)
                        if ship_is_valid(temp_ship_set, used_blocks_for_manual_drawing):
                            if check_ships_numbers(temp_ship, num_ships_list):
                                num_ships_list[len(temp_ship) - 1] += 1
                                human_ships_to_draw.append(temp_ship)
                                human_ships_set |= temp_ship_set
                                update_used_blocks(temp_ship, used_blocks_for_manual_drawing.add)
                            else:
                                show_message_at_rect_center(
                                    f"УЖЕ ДОСТАТОЧНО {len(temp_ship)}-ПАЛУБНЫХ КОРАБЛЕЙ", message_rect_for_drawing_ships)
                        else:
                            show_message_at_rect_center(
                                "КОРАБЛИ ПРИКАСАЮТСЯ!", message_rect_for_drawing_ships)
                if len(human_ships_to_draw) == 10:
                    ships_not_created = False
                    human_ships_working = copy.deepcopy(human_ships_to_draw)
                    screen.fill(WHITE, rect_for_messages_and_buttons)
            pygame.draw.rect(screen, BLACK, (start, ship_size), 3)
            draw_ships(human_ships_to_draw)
            pygame.display.update()


        while not game_over:
            draw_ships(destroyed_computer_ships)
            draw_ships(human_ships_to_draw)
            if not (dotted_set | hit_blocks):
                show_message_at_rect_center("ИГРА НАЧАЛАСЬ! ВАШ ХОД", message_rect_computer)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                elif not computer_turn and event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                
                    fired_block = ((x - left_margin) // block_size + 1,(y - upper_margin) // block_size +1) #координты клетки, в которую мы выстрелили
                    #проверка, что клик мыши был по сетке компьютера
                    if (fired_block in human_available_to_fire_set):
                        if computer_shield:
                            fired_block = computer_shoots(human_available_to_fire_set)
                            while computer_shield and check_hit_or_miss_ships(fired_block, computer_ships_working):
                                fired_block = computer_shoots(human_available_to_fire_set)
                            computer_shield = False
                        computer_turn = not check_hit_or_miss(fired_block, computer_ships_working, False,computer.ships, computer.ships_set, computer )
                        human_available_to_fire_set.discard(fired_block)
                        if not computer_turn:                      
                            human_cotract +=1
                            human_score += calc_score(human_cotract)
                            if human_score / 300 > human_shield_count:
                                human_shield_count += 1
                                human_shield = True
                        else:
                            human_cotract = 0
                        computer_grid.render()
                        human_grid.render() 
                        draw_from_dotted_set(dotted_set)
                        draw_hit_blocks(hit_blocks)
                        screen.fill(WHITE, message_rect_computer)
                        show_message_at_rect_center(
                            f"Ваш последний ход: {letters[fired_block[0]-1] + str(fired_block[1])}", message_rect_computer, color=BLACK)
                    else:
                        show_message_at_rect_center(
                            "ВЫСТРЕЛ ЗА ПРЕДЕЛЫ СЕТКИ!", message_rect_computer)
            #если компьютер попал, создаем множество клеток, состоящее из накрест лежащих от пораженной клетки
            if computer_turn:
                set_to_shoot_from = compueter_available_to_fire_set
                if around_last_computer_hit_set and not human_shield:
                    set_to_shoot_from = around_last_computer_hit_set
                pygame.time.delay(500) #замедляем стрельбу, чтобы видеть в какую клетку был удар
                fired_block = computer_shoots(set_to_shoot_from)
                while human_shield and check_hit_or_miss_ships(fired_block, human_ships_working):
                    fired_block = computer_shoots(set_to_shoot_from)
                compueter_available_to_fire_set.discard(fired_block) #записываем эту клетку
                computer_turn = check_hit_or_miss(
                    fired_block, human_ships_working, True, human_ships_to_draw, human_ships_set, computer)
                if human_shield:
                    human_shield = False
                
                if computer_turn:
                    computer_contract += 1
                    computer_score += calc_score(computer_contract)
                    if computer_score / 300 > computer_shield_count:
                        computer_shield_count += 1
                        computer_shield = True
                else:
                    computer_contract = 0
                computer_grid.render()
                human_grid.render() 
                draw_from_dotted_set(dotted_set)
                draw_hit_blocks(hit_blocks)
                screen.fill(WHITE, message_rect_human)
                show_message_at_rect_center(
                    f"ПОСЛЕДНИЙ ХОД КОМПЬЮТЕРА: {letters[fired_block[0] - 16] + str(fired_block[1])}", message_rect_human, color=BLACK)
            if not computer.ships_set:
                show_message_at_rect_center(
                    "ВЫ ВЫИГРАЛИ! Для выхода нажмите Q или C для продолжения", (0, 0, size[0], size[1]), game_over_font)
                game_over = True
                #pygame.display.update()


            if not human_ships_set:
                show_message_at_rect_center(
                    "ВЫ ПРОИГРАЛИ! Для выхода нажмите Q или C для продолжения", (0, 0, size[0], size[1]), game_over_font) 
                game_over = True
            pygame.display.update()
        new_game =  False
        while not game_close and not new_game:
            pygame.display.update()
            for event in pygame.event.get():
                if event.type and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_close = True
                    if event.key == pygame.K_c:
                        new_game = True

           
main()
pygame.quit()