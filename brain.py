
#returns the number of turns it would take to reach this food item
def distance_from_food(food, data):
    distx = abs(data['you']['body'][0]['x'] - food['x'])
    disty = abs(data['you']['body'][0]['y'] - food['y'])
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


def get_move_options(board, data):
    move_options = []
    self_head = get_self_head(data)
    directions = ['up', 'left', 'right', 'down']
    for direction in directions:
        move = get_move(direction, self_head)
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

def is_valid_move(option, data, board):
    if not is_in_bounds(option, data):
        return False
    return True

def get_current_options(board, data):
    curr_options = []
    options = get_move_options(board, data)
    for option in options:
        if is_valid_move(option, data, board):
            curr_options.append(option)
    return curr_options

def get_direction(board, data):
    curr_options = get_current_options(board, data)
    print(curr_options)
    return curr_options[0]['direction']
