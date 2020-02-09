import json
import os
import random
import bottle
import waitress

from api import ping_response, start_response, move_response, end_response


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

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    print(json.dumps(data))

    color = "#00FF00"

    return start_response(color)

def out_of_bounds(dimensions, data):
    height = data['board']['height']
    width = data['board']['width']
    if dimensions[0] < 0 or dimensions[0] >= width:
        return True
    if dimensions[1] < 0 or dimensions[1] >= height:
        return True
    return False

def snake_in_dimensions(dimensions , snake):
    for bodyPiece in snake:
        if bodyPiece['x'] == dimensions[0] and bodyPiece['y'] == dimensions[1]:
            return True
    return False

def on_another_snake(dimensions, otherSnakes):
    for snake in otherSnakes:
        if snake_in_dimensions(dimensions, snake):
            return True
    return False

def get_option_dimensions(piece):
    return {'up':[piece['x'],piece['y']-1],'down':[piece['x'],piece['y']+1],'left':[piece['x']-1,piece['y']],'right':[piece['x']+1,piece['y']]}



def get_current_options(data, size):
    options = ['up', 'down', 'left', 'right']
    selfPieces = []
    for bodyPiece in data['you']['body']:
        selfPieces.append(bodyPiece)
    otherSnakes = []
    for snake in data['board']['snakes']:
        snakeBody = []
        for piece in snake['body']:
            snakeBody.append(piece)
        otherSnakes.append(snakeBody)
    option_dimensions = get_option_dimensions(selfPieces[0])#{'up':[selfPieces[0]['x'],selfPieces[0]['y']-1],'down':[selfPieces[0]['x'],selfPieces[0]['y']+1],'left':[selfPieces[0]['x']-1,selfPieces[0]['y']],'right':[selfPieces[0]['x']+1,selfPieces[0]['y']]}
    for direction in option_dimensions:
        if len(options) == 1:
            return [options[0]], option_dimensions, otherSnakes
        dimensions = option_dimensions[direction]
        if out_of_bounds(dimensions, data) or on_another_snake(dimensions, otherSnakes):
            #dont remove direction if its a tail and the head isn't one away from a food
            #dont remove direction if its a competing head and you're bigger
            options.remove(direction)
    return options, option_dimensions, otherSnakes

def dead_path(dimensions, otherSnakes):
    #check to see if the path is a dead endpoint
    return False

def remove_dead_paths(current_options, option_dimensions, otherSnakes):
    for direction in current_options:
        if len(current_options) == 1:
            return [current_options[0]]
        dimensions = option_dimensions[direction]
        if dead_path(dimensions, otherSnakes):
            current_options.remove(direction)
    return current_options

#return true if dimension in one away from a snake bigger than self
def close_to_big_snake(dimensions, otherSnakes, size):
    count = 0 #one snake expected (self) only return true if 2 found
    for snake in otherSnakes:
        snakeHead = snake['body'][0]
        option_dimensions = get_option_dimensions(snakeHead)
        for option in option_dimensions:
            if snakeHead['x'] == option[0] and snakeHead['y'] == option[1]:
                if len(snake['body'] >= size):
                    count = count + 1
            if count == 2:
                return True
    return False


def remove_directions_close_to_big_snakes(options, option_dimensions, otherSnakes, size):
    for direction in options:
        if len(options) == 1:
            return [options[0]]
        dimensions = option_dimensions[direction]
        if close_to_big_snake(dimensions, otherSnakes, size):
            options.remove(direction)
    return directions

def choose_best_option(current_options, option_dimensions, otherSnakes, size):
    if len(current_options) == 1:
        return current_options[0]
    current_options = remove_dead_paths(current_options, option_dimensions, otherSnakes)
    current_options = remove_directions_close_to_big_snakes(current_options, option_dimensions, otherSnakes, size)#remove paths that are 1 away from a bigger snakes
    #tend to food if close by and not near other otherSnakes
    #else maybe chase tail
    #or choose the most open direction
    # or tend to run away from other snakes
    choice = random.choice(current_options)
    return choice

@bottle.post('/move')
def move():
    data = bottle.request.json
    food = data['board']['food']
    health = data['you']['health']
    size = len(data['you']['body'])
    current_options, option_dimensions, otherSnakes = get_current_options(data, size)
    direction = choose_best_option(current_options, option_dimensions, otherSnakes, size)
    return move_response(direction)



@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    print(json.dumps(data))

    return end_response()


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()


if __name__ == '__main__':
    waitress.serve(application, host='0.0.0.0',port=os.getenv('PORT', '8080'))
