import json
import os
import random
import bottle
import waitress
from brain import *
from api import ping_response, start_response, move_response, end_response

snake_sizes = {}
last_turn_food_locations = []

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

def add_snake_to_board(snake, board):
    #add different marker for a disapeering tail if food hasn't been eaten
    #maybe: add marker to each piece of snake of how long until the tail, and of how far away snake's head is from another food item
    #add marker to elements indicating how far they are from a wall or other snake piece (0 being an other snake piece)
    size = snake_sizes[snake['name']]
    for i in range(size):
        try:
            piece = snake['body'][i]
            element = board[piece['x']][piece['y']]
            element['type'] = snake_type(snake['name'])
            board[piece['x']][piece['y']] = element
        except Exception as e:
            print(e)
            print('SNAKE SIZE ERROR')
    return board

def add_danger_zone_near_head(snake, board):
    # set up desired spots next to the heads of small snakes. If much higher in size, and good amount of food, move in to kill (get to this spot)
    # if an other snake has only one option for moving, mark as a very desirable location (only if that snake is smaller)
    head = snake['body'][0]
    for dx in [-1, 1]:
        try:
            element = board[head['x']+dx][head['y']]
            if element['type'] == 'empty':
                element['type'] = 'DANGER'
            board[head['x']+dx][head['y']] = element
        except Exception as e:
            print(e)
    for dy in [-1, 1]:
        try:
            element = board[head['x']][head['y']+dy]
            if element['type'] == 'empty':
                element['type'] = 'DANGER'
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
        if not snake['name'] == 'fred2020' and is_snake_bigger_than_me(snake):# and other snake is bigger than me
            board = add_danger_zone_near_head(snake, board)
    return board

def add_adjacent_open_squares(data, board):
    self_head = get_self_head(data)
    options = get_move_options(board, data)
    for option in options:
        print(option)
    return board

def make_board(data):
    board = initialize_board(data)
    board = add_snakes_to_board(data, board)
    board = add_adjacent_open_squares(data, board)
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
    return move_response(direction)



@bottle.post('/end')
def end():
    data = bottle.request.json
    #print(json.dumps(data))
    return end_response()


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()


if __name__ == '__main__':
    waitress.serve(application, host='0.0.0.0',port=os.getenv('PORT', '8080'))
