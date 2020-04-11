import json
import os
import random
import bottle
import waitress
from brain import get_direction
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
            print('Food WAS ATE LAST TURN')
            print(food)
            print(snake_head)
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
    size = snake_sizes[snake['name']]
    for i in range(size):
        piece = snake['body'][i]
        element = board[piece['x']][piece['y']]
        element['type'] = snake_type(snake['name'])
        board[piece['x']][piece['y']] = element
    return board

def add_snakes_to_board(data, board):
    for snake in data['board']['snakes']:
        board = add_snake_to_board(snake, board)
    return board

def make_board(data):
    board = initialize_board(data)
    board = add_snakes_to_board(data, board)
    return board

def proccess_data(data):
    update_snake_sizes(data)
    print(snake_sizes)
    update_food_locations(data)
    board = make_board(data)
    return board


#def make_snakes(data):#
    #snakes = []
    #for snake in snake_sizes:
    #return snakes

@bottle.post('/move')
def move():
    data = bottle.request.json
    board = proccess_data(data)
    direction = get_direction(board, data)
    #food = data['board']['food']
    #health = data['you']['health']
    #food = get_food_data(data)
    #current_options, option_dimensions, otherSnakes = get_current_options(data)
    #direction = choose_best_option(current_options, option_dimensions, otherSnakes, health, food, data)
    #print('my current size = '+str(snake_sizes['matthewber / fred2020']))
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
