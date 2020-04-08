

def get_current_options(board):
    #for column in board:
        #for item in column:
            #print(item)
    return ['right']

def get_direction(board):
    curr_options = get_current_options(board)
    return curr_options[0]
