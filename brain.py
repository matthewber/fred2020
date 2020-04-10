
#returns the number of turns it would take to reach this food item
def distance_from_food(food, data):
    distx = abs(data['you']['body'][0]['x'] - food['x'])
    disty = abs(data['you']['body'][0]['y'] - food['y'])
    return distx + disty

def get_self_head(data):
    head = data['you']['body'][0]
    print(head)
    return head

def get_adjacent_pieces(board, data):
    self_head = get_self_head(data)
    return False


def get_current_options(board):
    adjacent_pieces = get_adjacent_pieces()
    return ['right','left','up']



def get_direction(board, data):
    curr_options = get_current_options(board, data)
    print(curr_options)
    return curr_options[0]
