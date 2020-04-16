import json
import os
import random
import bottle
import waitress
#from brain import *
from api import ping_response, start_response, move_response, end_response

snake_sizes = {}
last_turn_food_locations = []
saved_old_food = []

# OLD brain

#returns the number of turns it would take to reach this food item, if direct line available
def distance_from_food(food, head):
    distx = abs(head['x'] - food['x'])
    disty = abs(head['y'] - food['y'])
    return distx + disty

def get_self_head(data):
    head = data['you']['body'][0]
    return head

def update_x(x, direction):
    if direction == 'left':
        return x-1
    elif direction == 'right':
        return x+1
    return x

def update_y(y, direction):
    if direction == 'up':
        return y-1
    elif direction == 'down':
        return y+1
    return y

def get_move(direction, head):
    x = update_x(head['x'], direction)
    y = update_y(head['y'], direction)
    return {'direction':direction, 'x':x, 'y':y}


def get_move_options(board, data, head=None):
    move_options = []
    if head == None:
        head = get_self_head(data)
    directions = ['up', 'down', 'left', 'right']
    for direction in directions:
        move = get_move(direction, head)
        move_options.append(move)
    return move_options

def x_in_bounds(x, data):
    width = data['board']['width']
    if x < 0 or x >= width:
        return False
    return True

def y_in_bounds(y, data):
    height = data['board']['height']
    if y < 0 or y >= height:
        return False
    return True

def is_in_bounds(option, data):
    return (x_in_bounds(option['x'], data) and y_in_bounds(option['y'], data))

def is_space_empty(option, board):
    boardPiece = board[option['x']][option['y']]
    if boardPiece['type'] in ['empty','DESIRABLE', 'VERY DESIRABLE']:
        return True
    return False

def is_valid_move(option, data, board):
    if not is_in_bounds(option, data):
        return False
    if not is_space_empty(option, board):
        return False
    return True

def is_backup_move(option, data, board):
    if not is_in_bounds(option, data):
        return False
    boardPiece = board[option['x']][option['y']]
    print(boardPiece)
    type = boardPiece['type']
    if type in ['empty','DANGER','DESIRABLE', 'VERY DESIRABLE']:
        return True
    return False

def get_current_options(board, data):
    curr_options = []
    backup_options = []
    options = get_move_options(board, data)
    print(options)
    for option in options:
        print(option)
        if is_valid_move(option, data, board):
            curr_options.append(option)
        if is_backup_move(option, data, board):
            backup_options.append(option)
    if len(curr_options) == 0:
        print('USING BACKUP OPTIONS')
        print(backup_options)
        return backup_options
    print('CURR OPTIONS')
    print(curr_options)
    return curr_options

def get_closest_food(data):
    closest_food = {'d':999999999}
    for food in data['board']['food']:
        head = get_self_head(data)
        dist = distance_from_food(food, head)
        food_item = {'d':dist,'x':food['x'],'y':food['y']}
        if food_item['d'] < closest_food['d']:
            closest_food = food_item
    return closest_food

def is_move_in_options(move, options):
    for option in options:
        if option['direction'] == move:
            return True
    return False

def closest_to_food(food, data):
    head = get_self_head(data)
    length_to_food = distance_from_food(food, head)
    for snake in data['board']['snakes']:
        if not (snake['name'] == 'fred2020'):
            snake_head = snake['body'][0]
            snake_length_to_food = distance_from_food(food, snake_head)
            if snake_length_to_food < length_to_food:
                return False
    return True

def go_to_closest_food(curr_options, data):
    #(return false) if you are farther than 1 move away, dont choose a food without more than 2 open spaces next to it.
    # Attempt to move in the direction of path to the food, rather than directly to the food
    closest_food = get_closest_food(data)
    if not closest_to_food(closest_food, data):#
        return 'False'
    head = get_self_head(data)
    if head['x'] > closest_food['x'] and is_move_in_options('left',curr_options):
        return 'left'
    elif head['x'] < closest_food['x'] and is_move_in_options('right', curr_options):
        return 'right'
    elif head['y'] > closest_food['y'] and is_move_in_options('up', curr_options):
        return 'up'
    elif head['y'] < closest_food['y'] and is_move_in_options('down', curr_options):
        return 'down'
    print('ERROR FINDING FOOD')
    return curr_options[0]['direction']

def get_adjacent_pieces(piece, board):
    adjacent_pieces = []
    for direction in ['up','down','left','right']:
        move = get_move(direction, piece)
        adjacent_pieces.append(move)
    return adjacent_pieces

def calc_connected_open_squares(option, data, board):
    adj = 0
    adj_pieces = get_adjacent_pieces(option, board)
    for piece in adj_pieces:
        if is_valid_move(piece, data, board):
            print('VALID MOVE - INCREMENTING ADJ')
            print(piece)
            adj = adj + 1
    return adj

def is_big_snake_head(piece, data):
    for snake in data['board']['snakes']:
        if (not 'fred2020' in snake['name']) and (is_snake_bigger_than_me(snake)):
            head = snake['body'][0]
            if piece['x'] == head['x'] and piece['y'] == head['y']:
                return True
    return False


def calc_2deep_connected_open_squares(option, data, board):
    print("CALCULATING 2 DEEP")
    adj = 0
    adj_pieces = get_adjacent_pieces(option, board)
    for piece in adj_pieces:
        if is_valid_move(piece, data, board):
            adj = adj + 1 #THESE VALUES FOR ADJ INCREMENTING AT DIFFERENT LEVELS CAN BE TUNED
            adj2_pieces = get_adjacent_pieces(piece, board)
            for piece2 in adj2_pieces:
                if not (option['x'] == piece2['x'] and option['y'] == piece2['y']):
                    if is_big_snake_head(piece2, data):
                        adj = adj - 3
                        print('DEC 3')
                    if is_valid_move(piece2, data, board):
                        adj = adj + 1
                        adj3_pieces = get_adjacent_pieces(piece2, board)
                        for piece3 in adj3_pieces:
                            if not (piece3['x'] == piece['x'] and piece3['y'] == piece['y']):
                                if is_valid_move(piece3, data, board):
                                    adj = adj + 1
                                if is_big_snake_head(piece3, data):
                                    print('DEC 2')
                                    adj = adj - 2
    print("ADJ2 SCORE: based on 1-1-1 scoring for OPTION")
    print(option)
    print(adj)
    return adj


# look at the next move and treat possible move locations of other snakes as filled. Make sure there are two possible moves from this next location
def remove_dead_paths(curr_options, data, board):
    ok_options = []
    good_options = []
    great_options = []
    for option in curr_options:
        try:
            print('FINDING OPEN ADJACENT SQUARES FOR ')
            print(option)
            adj = calc_connected_open_squares(option, data, board)
            print('OPEN ADJACENT SQUARES')
            print(adj)
            option['connected_open_squares'] = adj
            if adj > 0:
                ok_options.append(option)
            if adj > 1:
                good_options.append(option)
            if adj > 2:
                great_options.append(option)
        except Exception as e:
            print(e)
            print("REMOVING DEAD PATH ERROR")
    #if len(great_options) > 0:
    #    return great_options
    if len(good_options) > 0:
        if data['turn'] < 10 or data['you']['health'] < 20:#Tunable PARAMETERS for testing or AI implementation
            return good_options
        #return good_options
    if len(ok_options) == 1:
        return ok_options
    if len(ok_options) > 0:
        maxadj2 = [{'score':0}]
        for option in ok_options:
            #Assigns a score to the move option
            adj2 = calc_2deep_connected_open_squares(option, data, board)
            print('NEW = '+str(adj2))
            print('OLD = '+str(maxadj2[0]['score']))
            threshold = snake_sizes['fred2020']
            if int(adj2) > threshold and int(maxadj2[0]['score']) > threshold:
                maxadj2.append({'score':adj2, 'direction':option['direction'], 'x':option['x'], 'y':option['y']})
            elif adj2 == maxadj2[0]['score']:
                maxadj2.append({'score':adj2, 'direction':option['direction'], 'x':option['x'], 'y':option['y']})
            elif int(adj2) > int(maxadj2[0]['score']):
                maxadj2 = [{'score':adj2, 'direction':option['direction'], 'x':option['x'], 'y':option['y']}]
            else:
                print('FALSE, OLD IS BIGGER THAN NEW ')
            print('NEW ADJ2')
            print(maxadj2)
        print(maxadj2)
        return maxadj2
    return curr_options

def g_kill_scenarios(curr_options, board):
    g_kill_scenarios = []
    for option in curr_options:
        if board[option['x']][option['y']]['type'] == 'VERY DESIRABLE':
            print('HERE I GO KILLING AGAIN')
            g_kill_scenarios.append(option)
    return g_kill_scenarios

def kill_scenarios(curr_options, board):
    #if you find food next to a wall and are in correct position, trap other snake
    #ie look for all types of kill scenario moves
    kill_scenarios = []
    for option in curr_options:
        if board[option['x']][option['y']]['type'] in ['DESIRABLE', 'VERY DESIRABLE']:
            print('ATTEMPTING KILLING MOVE')
            kill_scenarios.append(option)
    return kill_scenarios

def get_direction(board, data):
    print('FINDING DIRECTIONS')
    curr_options = get_current_options(board, data)
    print('CURRENT OPTIONS')
    print(curr_options)
    if len(curr_options) == 1:
        print('ONE OPTION AVAILABLE')
        return curr_options[0]['direction']
    print('LOOKING FOR GUARENTEED KILL MOVES')
    #still need to complmete the designation of very desirable board spots
    g_kill_options = g_kill_scenarios(curr_options, board)
    if len(g_kill_options) > 0:
        print('ATTEMPTING GUARENTEED KILL MOVE')
        return g_kill_options[0]['direction']
    print('DETECTING IF SNAKE IS TRAPPED')
    #detect if snake needs to make certain moves to become untrapped
    # also consider yourself trapped if there is only a 1-wide escape from current situation
    # consider a place to be entrapped if, with your current length, you can't escape( easy hack would be space a couple bigger than your snake's size)
    # if there is one exit of size 2, and another snake is one away from the exit, then move to escape
    # !!!!!!! dont move into a place where you could have a 2 spot standoff chice with a bigger snake (ie adjacent to Danger slots)
    print('LOOKING FOR CLOSE SNAKES TO RUN AWAY FROM ')
    #if you are the closest snake to a given food, and it is close by, move towards it
    if data['you']['health'] < 5:
        direction = go_to_closest_food(curr_options, data)
        if not direction == 'False':
            return direction
    print('REMOVING DEAD PATHS')
    curr_options = remove_dead_paths(curr_options, data, board)
    if len(curr_options) == 1:
        return curr_options[0]['direction']

    kill_options = kill_scenarios(curr_options, board)
    if len(kill_options) > 0:
        return kill_options[0]['direction']
    # when counting the number of adjacent empty spaces, and determining if an out, take into consideration where the next snake heads' move will be
    #don't go into spot with few adjacent open pieces, unless out will appear soon
    #dont enter a narrow hall with other snake heads nearby
    #prioritize staying away from big snake heads!
    # and not getting stuck against a wall and moving towards open areas
    #choose from remaining options - add choosing to kill over food in certain scenarios
    if data['you']['health'] < 101:
        direction = go_to_closest_food(curr_options, data)
        if not direction == 'False':
            return direction

    # !!! move away from the snake head closest from you
    # move away if there are two snakes close together to you
    # especially if within 3 blocks

    # when 2 snakes are left, be extra aggresive
    return curr_options[0]['direction']

@bottle.route('/')
def index():
    return '''
    Snake Successfully Snaking'''


@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.
    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')


@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()


@bottle.post('/start')
def start():
    data = bottle.request.json
    global snake_sizes
    global last_turn_food_locations
    snake_sizes = {}
    last_turn_food_locations = []
    print(json.dumps(data))
    color = "#00FF00"
    return start_response(color)

def snake_exists(name):
    for key in snake_sizes:
        if key == name:
            return True
    return False

def update_food_locations(data):
    global last_turn_food_locations
    global saved_old_food
    saved_old_food = last_turn_food_locations
    last_turn_food_locations = []
    for food in data['board']['food']:
        last_turn_food_locations.append(food)

def update_snake_size(snake_name, snake_head):
    global last_turn_food_locations
    global snake_sizes
    for food in last_turn_food_locations:
        if food['x'] == snake_head['x'] and food['y'] == snake_head['y']:
            snake_sizes[snake_name] = snake_sizes[snake_name] + 1
            return

def initialize_snake_size(snake_name):
    global snake_sizes
    snake_sizes[snake_name] = 3

def snake_size(snake):
    s_name = snake['name']
    s_head = snake['body'][0]
    if not snake_exists(s_name):
        initialize_snake_size(s_name)
    else:
        update_snake_size(s_name, s_head)

def update_snake_sizes(data):
    for snake in data['board']['snakes']:
        snake_size(snake)

def initialize_board(data):
    board = []
    for i in range(data['board']['width']):
        board.append([])
        for j in range(data['board']['height']):
            board[i].append({'type':'empty', 'n_until_empty': 0, 'n_until_filled': 0})
    return board

def snake_type(snake_name):
    if 'fred2020' in snake_name:
        return 'self'
    return 'snake'

def did_snake_just_eat_food(snake_head):
    print('TESTING IF SNAKE ATE FOOD')
    global saved_old_food
    print(saved_old_food)
    for food in saved_old_food:
        if food['x'] == snake_head['x'] and food['y'] == snake_head['y']:
            return True
    return False

def add_snake_to_board(snake, board):
    #add different marker for a disapeering tail if food hasn't been eaten
    #maybe: add marker to each piece of snake of how long until the tail, and of how far away snake's head is from another food item
    #add marker to elements indicating how far they are from a wall or other snake piece (0 being an other snake piece)
    size = snake_sizes[snake['name']]
    for i in range(size):
        try:
            piece = snake['body'][i]
            n_until_empty = size-i-1
            print('SNAKE N UNTIL EMPTY')
            print(n_until_empty)
            element = board[piece['x']][piece['y']]
            element['n_until_empty'] = n_until_empty
            element['type'] = snake_type(snake['name'])
            if (i > 3) and (i == size-1) and not did_snake_just_eat_food(snake['body'][0]):
                print('TAIL DISAPEERING FOR '+snake['name'])
                element['type'] = 'empty'
            board[piece['x']][piece['y']] = element
        except Exception as e:
            print(e)
            print('SNAKE SIZE ERROR')
    return board

def snake_has_1_option(snake, board, data):
    snake_head = snake['body'][0]
    num_options = 0
    options = get_move_options(board, data, head=snake_head)
    for option in options:
        if is_valid_move(option, data, board):
            num_options = num_options + 1
    if num_options < 2:
        return True
    return False

def add_danger_zone_near_head(snake, board, data):
    # set up desired spots next to the heads of small snakes. If much higher in size, and good amount of food, move in to kill (get to this spot)
    # if an other snake has only one option for moving, mark as a very desirable location (only if that snake is smaller)
    if is_snake_bigger_than_me(snake):
        type = 'DANGER'
    elif snake_has_1_option(snake, board, data):
        type = "VERY DESIRABLE"
    else:
        type = "DESIRABLE"
    head = snake['body'][0]
    for dx in [-1, 1]:
        try:
            element = board[head['x']+dx][head['y']]
            if element['type'] == 'empty':
                element['type'] = type
            board[head['x']+dx][head['y']] = element
        except Exception as e:
            print(e)
    for dy in [-1, 1]:
        try:
            element = board[head['x']][head['y']+dy]
            if element['type'] == 'empty':
                element['type'] = type
            board[head['x']][head['y']+dy] = element
        except Exception as e:
            print(e)
    return board

def is_snake_bigger_than_me(snake):
    my_size = snake_sizes['fred2020']
    snake_size = snake_sizes[snake['name']]
    return snake_size >= my_size

def add_snakes_to_board(data, board):
    for snake in data['board']['snakes']:
        board = add_snake_to_board(snake, board)
        if not snake['name'] == 'fred2020':
            board = add_danger_zone_near_head(snake, board, data)
    return board

def add_trapped_zones(data, board):
    self_head = get_self_head(data)
    options = get_move_options(board, data)
    for option in options:
        pass#adj = count_num_adjacent_squares(option, board)
    return board

def make_board(data):
    board = initialize_board(data)
    board = add_snakes_to_board(data, board)
    board = add_trapped_zones(data, board)
    # add counts of how many adjacent open squares there are to the move options
    return board

def proccess_data(data):
    update_snake_sizes(data)
    print(snake_sizes)
    update_food_locations(data)
    board = make_board(data)
    return board

@bottle.post('/move')
def move():
    data = bottle.request.json
    board = proccess_data(data)
    direction = get_direction(board, data)
    print('MOVING')
    print(direction)
    response = move_response(direction)
    print(response)
    return response#move_response(direction)



@bottle.post('/end')
def end():
    data = bottle.request.json
    #print(json.dumps(data))
    return end_response()


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()


if __name__ == '__main__':
    waitress.serve(application, host='0.0.0.0',port=os.getenv('PORT', '8080'))
