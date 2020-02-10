import json
import os
import random
import bottle
import waitress

from api import ping_response, start_response, move_response, end_response

snake_sizes = {}
last_turn_food_locations = {}

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
    print('dimensions not out of bounds: ', str(dimensions[0]), str(dimensions[1]))
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

def update_snake_lengths(data):
    global last_turn_food_locations
    global snake_sizes
    for snake in data['board']['snakes']:
        snake_exists = False
        for key in snake_sizes:
            if key == snake['name']:
                snake_exists = True
        if not snake_exists:
            snake_sizes[snake['name']] = 3
        else:
            snakeHead = snake['body'][0]
            for food in last_turn_food_locations:
                if food['x'] == snakeHead['x'] and food['y'] == snakeHead['y']:
                    snake_sizes[snake['name']] = snake_sizes[snake['name']] + 1
    #update last food locations
    last_turn_food_locations = []
    for food in data['board']['food']:
        last_turn_food_locations.append(food)



def get_current_options(data):
    options = ['up', 'down', 'left', 'right']
    selfPieces = []
    for bodyPiece in data['you']['body']:
        selfPieces.append(bodyPiece)
    otherSnakes = []
    update_snake_lengths(data)
    for snake in data['board']['snakes']:
        snakeBody = []
        index = 0
        for piece in snake['body']:
            snakeBody.append(piece)
            index = index + 1
            if index == snake_sizes[snake['name']]:
                break
        otherSnakes.append(snakeBody)
    option_dimensions = get_option_dimensions(selfPieces[0])
    for direction in option_dimensions:
        if len(options) == 1:
            return [options[0]], option_dimensions, otherSnakes
        dimensions = option_dimensions[direction]
        if out_of_bounds(dimensions, data) or on_another_snake(dimensions, otherSnakes):
            #dont remove direction if its a tail and the head isn't one away from a food
            #dont remove direction if its a competing head and you're bigger
            options.remove(direction)
    return options, option_dimensions, otherSnakes

def dead_path(point, otherSnakes, data):
    possible_directions = ['up', 'down', 'left', 'right']
    #return true if 4 directions blocked in new direction
    direction_blocked = {'up':False, 'down':False, 'left':False, 'right':False }
    for direction in possible_directions:
        if out_of_bounds(point, data):
            print('OUT of bounds'+direction)
            direction_blocked[direction] = True
        if on_another_snake(point, otherSnakes):
            print('On another snake'+direction)
            direction_blocked[direction] = True
    if direction_blocked['up'] and direction_blocked['down'] and direction_blocked['left'] and direction_blocked['right']:
        print('Dead path')
        return True
    print('Not a dead path')
    print('possible directions= ')
    print(possible_directions)
    return False

def remove_dead_paths(current_options, option_dimensions, otherSnakes, data):
    new_options = []
    for direction in current_options:
        if len(current_options) == 1:
            return [current_options[0]]
        dimensions = option_dimensions[direction]
        if not dead_path(dimensions, otherSnakes, data):
            print('Not a dead path '+direction)
            new_options.append(direction)
    if len(new_options) == 0:
        return current_options
    return new_options

#return true if dimension in one away from a snake bigger than self
def close_to_big_snake(dimensions, otherSnakes, size):
    count = 0 #one snake expected (self) only return true if 2 found
    for snake in otherSnakes:
        snakeHead = snake[0]
        option_dimensions = get_option_dimensions(snakeHead)
        for option in option_dimensions:
            print('testing option:')
            print(option)
            if snakeHead['x'] == option[0] and snakeHead['y'] == option[1]:
                if len(snake >= size):
                    print('Incrementing bigger snake count to '+str(count))
                    count = count + 1
                else:
                    print('Close snake is smaller')
            else:
                print('no snake at this option')
            if count == 2:
                return True
    return False


def remove_directions_close_to_big_snakes(options, option_dimensions, otherSnakes, size):
    new_options = []
    for direction in options:
        print('looking '+direction)
        if len(options) == 1:
            return [options[0]]
        dimensions = option_dimensions[direction]
        if close_to_big_snake(dimensions, otherSnakes, size):
            print('Close to snake')
            new_options.append(direction)
        else:
            print('not Close to Snake')
    if len(new_options) == 0:
        return options
    return new_options

def get_food_data(data):
    return data['board']['food']

def move_to_health(options, option_dimensions, food):
    for direction in options:
        if len(options) == 1:
            return [options[0]]
        dimensions = option_dimensions[direction]
        for item in food:
            if item['x'] == dimensions[0] and item['y'] == dimensions[1]:
                return [direction]
    return options

#remove paths that dont lead long.
def remove_poor_paths(options, option_dimensions, otherSnakes):
    return options

def isOtherSnakeCloserToFood(food, data):
    #return True if other snake closer to food than you
    return False

def distance_from_food(food, data):
    distx = abs(data['you']['body'][0]['x'] - food['x'])
    disty = abs(data['you']['body'][0]['y'] - food['y'])
    return distx + disty



def get_safe_food(data, food):
    safe_food_distance = 5
    safe_food = []
    for item in food:
        if distance_from_food(item, data) < safe_food_distance:
            if not isOtherSnakeCloserToFood(item, data):
                safe_food.append(item)
    return safe_food

def choose_best_food(food_options, data):
    #return closest piece of food
    #return best direction to go towards when good food exists
    #if big snakes in area take that into account
    #for each snake
    # if nearby snakeis  bigger same size or only 1 smaller run other direction
    return random.choice(food_options)

#returns string direction
def best_directions_towards_food(options, desired_food, data):
    best_food = choose_best_food(desired_food, data)
    my_head = data['you']['body'][0]
    if 'right' in options and best_food['x'] > my_head['x']:
        return 'right'
    if 'left' in options and best_food['x'] < my_head['x']:
        return 'left'
    if 'down' in options and best_food['y'] < my_head['y']:
        return 'down'
    if 'up' in options and best_food['y'] > my_head['y']:
        return 'up'
    return random.choice(options)

#returns string
def choose_from_remaining_options(remaining_options, data, food):
    desired_food = get_safe_food(data, food)
    if len(desired_food[0]) == 0:
        #if low on food aggressivley seek food
        #else if tail nearby chase tail
        #else go to open area
        return random.choice(remaining_options)
    direction = best_directions_towards_food(remaining_options, desired_food, data)
    return direction


def choose_best_option(current_options, option_dimensions, otherSnakes, health, food, data):
    if len(current_options) == 1:
        return current_options[0]
    #order functions in order of precedence
    current_options = remove_dead_paths(current_options, option_dimensions, otherSnakes, data)

    #print('removing big snake directs')
    current_options = remove_directions_close_to_big_snakes(current_options, option_dimensions, otherSnakes, snake_sizes['matthewber / fred2020'])#remove paths that are 1 away from a bigger snakes
    current_options = move_to_health(current_options, option_dimensions, food)#moves to health piece if one away
    current_options = remove_poor_paths(current_options, option_dimensions, otherSnakes)

    #!!!!tend to food if close by and not near other otherSnakes
    #else maybe chase tail
    #or choose the most open direction
    # or tend to run away from other snakes
    choice = choose_from_remaining_options(current_options, data, food)
    return choice

@bottle.post('/move')
def move():
    data = bottle.request.json
    food = data['board']['food']
    health = data['you']['health']
    food = get_food_data(data)
    current_options, option_dimensions, otherSnakes = get_current_options(data)
    direction = choose_best_option(current_options, option_dimensions, otherSnakes, health, food, data)
    print('my current size = '+str(snake_sizes['matthewber / fred2020']))
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
