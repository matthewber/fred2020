



def get_current_options(board):
    print(board)
    return ['left']

def get_direction(board):
    curr_options = get_current_options(board)
    return curr_options[0]
