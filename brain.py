
#returns the number of turns it would take to reach this food item
def distance_from_food(food, data):
    head = get_self_head(data)
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


def get_move_options(board, data):
    move_options = []
    self_head = get_self_head(data)
    directions = ['up', 'down', 'left', 'right']
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
        return backup_options
    print('CURR OPTIONS')
    print(curr_options)
    return curr_options

def get_closest_food(data):
    closest_food = {'d':999999999}
    for food in data['board']['food']:
        dist = distance_from_food(food, data)
        food_item = {'d':dist,'x':food['x'],'y':food['y']}
        if food_item['d'] < closest_food['d']:
            closest_food = food_item
    return closest_food

def is_move_in_options(move, options):
    for option in options:
        if option['direction'] == move:
            return True
    return False

def go_to_closest_food(curr_options, data):
    #dont choose that food item if it is closer to another snakes' head (unless that snake is 3 or more smaller than you)
    closest_food = get_closest_food(data)
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

def calc_connected_open_squares(option, board):
    return 999

def remove_dead_paths(curr_options, board):
    new_options = []
    for option in options:
        try:
            adj = calc_connected_open_squares(option, board)
            print('OPEN ADJACENT SQUARES')
            print(adj)
            option['connected_open_squares'] = adj
            if adj > 3:
                new_options.append(option)
        except Exception as e:
            print(e)
    if len(new_option) < 1:
        return curr_options
    return new_options

def kill_scenarios(curr_options, board):
    #if you find food next to a wall and are in correct possition, trap other snake
    kill_scenarios = []
    for option in curr_options:
        if board[option['x']][option['y']]['type'] in ['DESIRABLE', 'VERY DESIRABLE']:
            print('ATTEMPTING KILLING MOVE')
            kill_scenarios.append(option)
    return kill_scenarios

def get_direction(board, data):
    curr_options = get_current_options(board, data)
    if len(curr_options) == 1:
        return curr_options[0]['direction']
    curr_options = remove_dead_paths(curr_options, board)
    kill_options = kill_scenarios(curr_options, board)
    if len(kill_options) > 0:
        return kill_options[0]['direction']

    # look at the next move and treat possible move locations of other snakes as filled. Make sure there are two possible moves from this next location
    # when counting the number of adjacent empty spaces, and determining if an out, take into consideration where the next snake heads' move will be
    #don't go into spot with few adjacent open pieces, unless out will appear soon
    #dont enter a narrow hall with other snake heads nearby
    #prioritize staying away from big snake heads!
    # and not getting stuck against a wall and moving towards open areas
    #choose from remaining options - add choosing to kill over food in certain scenarios
    if data['you']['health'] < 101:
        direction = go_to_closest_food(curr_options, data)
        return direction
    # next things to add:
    #    don't go down dead routes
    #    kill snakes when you have them in a vulnerable position
    return curr_options[0]['direction']
