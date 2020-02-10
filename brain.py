

def make_board(data):
    return [[]]

def get_current_options(board, data):
    return ['left']

def get_direction(data, test):
    data['board'] = make_board(data)
    curr_options = get_current_options(data)
    return curr_options[0]
