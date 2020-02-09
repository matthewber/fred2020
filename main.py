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
    if dimentions[1] < 0 or dimentions[1] >= height:
        return True
    return False

def on_another_snake(dimensions):
    return False

def get_current_options(data):
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
    option_dimensions = {'up':[selfPieces[0]['x'],selfPieces[0]['y']-1],'down':[selfPieces[0]['x'],selfPieces[0]['y']+1],'left':[selfPieces[0]['x']-1,selfPieces[0]['y']],'right':[selfPieces[0]['x']+1,selfPieces[0]['y']]}
    for direction in option_dimensions:
        if len(options) == 1:
            return options[0]
        dimensions = option_dimensions[direction]
        if out_of_bounds(dimensions, data) or on_another_snake(dimensions):
            options.remove(direction)
    print(option_dimensions)
    return options

def choose_best_option(current_options):
    choice = random.choice(current_options)
    return choice

@bottle.post('/move')
def move():
    data = bottle.request.json
    food = data['board']['food']
    health = data['you']['health']
    current_options = get_current_options(data)
    direction = choose_best_option(current_options)
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
