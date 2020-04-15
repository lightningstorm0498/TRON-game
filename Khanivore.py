# Import any libraries you might need to develop our agent.
import numpy as np
import matplotlib
import time
import signal
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import animation, rc
from IPython.display import HTML, clear_output
# the two packages listed below are additional
import copy
from collections import deque

start_point = None
end_point = None
open_list = {}
close_list = {}
close_list_fixed = {}
close_list_fixed_1 = {}
map_border = ()
actions = []
weight = 1
path_distance = 0


class Node2:
    def __init__(self, data1=None, data2=None, vboard=None, parent=None, v_p1_position=None):
        self.data1 = data1
        self.data2 = data2
        self.vboard = vboard
        self.parent = parent
        self.v_p1_position = v_p1_position

    def depth(self):
        if self.parent is not None:
            return self.parent.depth() + 1
        else:
            return 0


class Stack:
    def __init__(self):
        self.stack = deque([])

    def isEmpty(self):
        return len(self.stack) == 0

    def push(self, item):
        self.stack.append(item)

    def pop(self):
        return self.stack.pop()

    def peek(self):
        return self.stack[-1]

    def size(self):
        return len(self.stack)


# this agent was made by my roommate
class PlayerAgent:

    def __init__(self, player_id):
        self.player_id = player_id
        self.elo = 1000

    def v_legal_moves(self, id, game, vboard):
        return game.get_legal_moves(id, vboard)

    def exam_move(self, node, move):
        data1 = node.data1.copy()
        data2 = node.data2.copy()
        data1.append(move[0])
        data2.append(move[1])
        vboard = node.vboard.copy()
        vboard[move[0]][move[1]] = self.player_id
        vboard[node.v_p1_position[0]][node.v_p1_position[1]] = 4
        v_p1_position = move.copy()
        return Node2(data1=data1, data2=data2, vboard=vboard, parent=node, v_p1_position=v_p1_position)

    def dfs(self, node, game, goal):
        frontier = Stack()
        frontier.push(node)
        while not frontier.isEmpty():
            current_node = frontier.pop()
            if (current_node.depth()) == goal:
                return current_node
            else:
                PlayerAgent.v_legal_moves(self, self.player_id, game, current_node.vboard)
                for move in PlayerAgent.v_legal_moves(self, self.player_id, game, current_node.vboard):
                    next_node = PlayerAgent.exam_move(self, current_node, move)
                    frontier.push(next_node)
        return False

    def Survival(self, id, vboard):
        b = np.where(vboard == id)
        up_num = 0
        down_num = 0
        left_num = 0
        right_num = 0
        life = 0
        for up in range(1, 20):
            if b[0] - up + 1 == 0:
                break
            if vboard[b[0] - up, b[1]] == 0:
                up_num = up_num + 1
            else:
                break
        for down in range(1, 20):
            if b[0] + down == vboard.shape[0]:
                break
            if vboard[b[0] + down, b[1]] == 0:
                down_num = down_num + 1
            else:
                break
        for left in range(1, 20):
            if b[1] + 1 - left == 0:
                break
            if vboard[b[0], b[1] - left] == 0:
                left_num = left_num + 1
            else:
                break
        for right in range(1, 20):
            if b[1] + right == vboard.shape[1]:
                break
            if vboard[b[0], b[1] + right] == 0:
                right_num = right_num + 1
            else:
                break
        sum_num = (up_num + 1) * (down_num + 1) * (left_num + 1) * (right_num + 1)
        return sum_num

    def choose_move(self, game):
        # Get an array of legal moves from your current position.
        node = Node2()
        node.data1 = []
        node.data2 = []
        node.vboard = game.board.copy()
        node.v_p1_position = game.get_player_position(self.player_id, game.board)

        legal_moves = game.get_legal_moves(self.player_id)
        best_move = []
        best_stepsnum = 0
        best_survive = 0
        for move in legal_moves:
            node = Node2()
            node.data1 = []
            node.data2 = []
            node.vboard = game.board.copy()
            node.v_p1_position = game.get_player_position(self.player_id, game.board)
            move_board = []
            node = self.exam_move(node, move)
            for i in range(20):
                a = self.dfs(node, game, i + 1)
                if a:
                    move_board = a.vboard.copy()
                    move_step_num = a.depth()
                else:
                    break
            if move_step_num > best_stepsnum:
                best_stepsnum = move_step_num
                best_move = move
            elif move_step_num == best_stepsnum:
                if self.Survival(self.player_id, move_board) >= best_survive:
                    best_survive = self.Survival(self.player_id, move_board)
                    best_move = move
        return best_move


# special thanks to Mr.Wang
# https://www.cnblogs.com/nobugtodebug/p/4500278.html
class Node:
    def __init__(self, father, x, y):
        global weight
        if x < 0 or x >= map_border[0] or y < 0 or y >= map_border[1]:
            raise Exception

        self.father = father
        self.x = x
        self.y = y
        if father is not None:
            g = calc_g(father, self)
            self.G = g + father.G
            self.H = calc_h(self)
            self.F = weight * (self.G + self.H)
        else:
            self.G = 0
            self.H = 0
            self.F = 0

    def reset_father(self, father, new_g):
        global weight
        if father is not None:
            self.G = new_g
            self.F = weight * (self.G + self.H)

        self.father = father


def calc_g(node1, node2):
    if abs(node1.x - node2.x) == 1 or abs(node1.y - node2.y) == 1:
        return 1


def calc_h(cur):
    return abs(end_point.x-cur.x) + abs(end_point.y-cur.y)


def min_f_node():
    if len(open_list) == 0:
        raise Exception

    _min = 65535
    _k = (start_point.x, start_point.y)
    for k, v in open_list.items():
        if _min > v.F:
            _min = v.F
            _k = k

        elif _min == v.F:
            if abs(open_list[_k].x - open_list[_k].y) > abs(v.x - v.y):
                _min = v.F
                _k = k

            elif abs(open_list[_k].x - open_list[_k].y) == abs(v.x - v.y) and np.random.random() > 0.5:
                _min = v.F
                _k = k

    return open_list[_k]


def add_new_points(node):
    open_list.pop((node.x, node.y))
    close_list[(node.x, node.y)] = node

    _adjacent = []

    try:
        _adjacent.append(Node(node, node.x - 1, node.y))  # up
    except Exception as e:
        pass

    try:
        _adjacent.append(Node(node, node.x + 1, node.y))  # down
    except Exception as e:
        pass

    try:
        _adjacent.append(Node(node, node.x, node.y - 1))  # left
    except Exception as e:
        pass

    try:
        _adjacent.append(Node(node, node.x, node.y + 1))  # right
    except Exception as e:
        pass

    for a in _adjacent:
        if (a.x, a.y) == (end_point.x, end_point.y):
            new_g = calc_g(a, node) + node.G
            end_point.reset_father(node, new_g)
            return True

        if (a.x, a.y) in close_list:
            continue

        if (a.x, a.y) not in open_list:
            open_list[(a.x, a.y)] = a

        else:
            exist_node = open_list[(a.x, a.y)]
            new_g = calc_g(a, node) + node.G
            if new_g < exist_node.G:
                exist_node.reset_father(node, new_g)

    return False


def find_the_path(start_p):
    open_list[(start_point.x, start_point.y)] = start_p

    the_node = start_point
    try:
        while not add_new_points(the_node):
            the_node = min_f_node()
    except Exception as e:
        return False

    return True


def apply_path(node):
    global path_distance

    if node.father is None:
        row = node.x - end_point.x
        column = node.y - end_point.y

        if row == 1 and column == 0:
            actions.append(0)
        elif row == -1 and column == 0:
            actions.append(1)
        elif row == 0 and column == 1:
            actions.append(2)
        elif row == 0 and column == -1:
            actions.append(3)
        else:
            actions.append(4)
        return

    row = node.father.x - node.x
    column = node.father.y - node.y

    if row == 1 and column == 0:
        actions.append(0)
    elif row == -1 and column == 0:
        actions.append(1)
    elif row == 0 and column == 1:
        actions.append(2)
    elif row == 0 and column == -1:
        actions.append(3)

    path_distance += 1

    apply_path(node.father)


# TODO: Implement your agent here by modifying the 'choose_move' function.
# Do not change the instantiation function or any of the function signatures.
class KhanivoreAgent:

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #  Readme:                                                                    #
    #  I am the primary Khanivore Agent created by Lei                            #
    #  All the parameter only fit for the preset player number as 1 and 3.        #
    #  If the game size has been changed, changing the number '19' to 'game.size' #
    #  minus one in parameter 'self.last_rival'.                                  #
    #  Edited at 12:33 in 2020/04/09                                              #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def __init__(self, player_id):
        self.player_id = player_id
        self.lock_1 = False
        self.lock_2 = False
        self.last_rival = [19 - self.player_id, 19 - self.player_id]
        self.reverse_position = int((3 - self.player_id) * 9.5)
        self.zone_key = int((self.player_id - 1) * 0.5)
        self.area_size = [0, 0]

    def choose_move(self, game):
        global start_point, end_point, actions, open_list, close_list, weight, map_border, path_distance
        # stopwatch = time.time()
        trace_back = True
        safe_zone = int(game.size * 0.3)

        if game.board_type == 'rocky' and self.lock_1 is False:
            self.lock_1 = True
            self.lock_2 = True
            map_border = (game.size, game.size)
            for i in range(game.size):
                for j in range(game.size):
                    if game.board[i][j] == 4:
                        if i < j:
                            self.area_size[0] += 1
                        elif i > j:
                            self.area_size[1] += 1
                        block_node = Node(None, i, j)
                        close_list_fixed[(block_node.x, block_node.y)] = block_node
        elif game.board_type == 'default' and self.lock_1 is False:
            self.lock_1 = True
            self.lock_2 = True
            map_border = (game.size, game.size)

        elif game.board_type == 'obstacles' and self.lock_1 is False:
            self.lock_1 = True
            self.lock_2 = True
            self.last_rival = [9 - self.player_id, 4]
            map_border = (10, 10)
            for i in range(10):
                for j in range(10):
                    if game.board[i][j] == 4:
                        block_node = Node(None, i, j)
                        close_list_fixed[(block_node.x, block_node.y)] = block_node
        bias = []
        moves = []

        start_point = None
        end_point = None
        open_list.clear()
        close_list.clear()
        actions.clear()

        location_self = game.get_player_position(self.player_id)

        if self.lock_2 is False:
            if location_self[0] == game.size - 1 - self.reverse_position and location_self[1] == game.size - 1 - self.reverse_position:
                close_list_fixed.clear()
                self.area_size.clear()
                self.area_size = [0, 0]
                self.lock_1 = False
        self.lock_2 = False

        block_node = Node(None, location_self[0], location_self[1])
        close_list_fixed[(block_node.x, block_node.y)] = block_node

        if location_self[0] < location_self[1]:
            self.area_size[0] += 1
        elif location_self[0] > location_self[1]:
            self.area_size[1] += 1

        location_rival = game.get_player_position(4 - self.player_id)
        block_node = Node(None, location_rival[0], location_rival[1])
        close_list_fixed[(block_node.x, block_node.y)] = block_node

        if location_rival[0] < location_rival[1]:
            self.area_size[0] += 1
        elif location_rival[0] > location_rival[1]:
            self.area_size[1] += 1

        row = self.last_rival[0] - location_rival[0]
        column = self.last_rival[1] - location_rival[1]

        bias.clear()

        if row == 1 and column == 0:
            bias.extend([-1, 0])
        elif row == -1 and column == 0:
            bias.extend([1, 0])
        elif row == 0 and column == 1:
            bias.extend([0, -1])
        elif row == 0 and column == -1:
            bias.extend([0, 1])
        else:
            bias.extend([0, 0])

        self.last_rival = location_rival

        edge = False
        if location_self[0] == 0 or location_self[0] == game.size - 1 or location_self[1] == 0 or location_self[1] == game.size - 1:
            edge = True

        if location_rival[0] + bias[0] < 0 or location_rival[0] + bias[0] > game.size - 1 or \
                location_rival[1] + bias[1] < 0 or location_rival[1] + bias[1] > game.size - 1:
            bias.clear()
            bias.extend([0, 0])

        distance = abs(location_self[0] - location_rival[0] - bias[0]) + abs(location_self[1] - location_rival[1] - bias[1])

        close_list = copy.deepcopy(close_list_fixed)

        weight = 1
        start_point = Node(None, location_self[0], location_self[1])

        if game.board[location_rival[0] + bias[0]][location_rival[1] + bias[1]] == 0:
            end_point = Node(None, location_rival[0] + bias[0], location_rival[1] + bias[1])

        else:
            end_point = Node(None, location_rival[0], location_rival[1])

        moves.extend([[location_self[0] - 1, location_self[1]], [location_self[0] + 1, location_self[1]],
                      [location_self[0], location_self[1] - 1], [location_self[0], location_self[1] + 1]])

        if find_the_path(start_point) and (edge is False or distance > 1):
            apply_path(end_point.father)
            if len(actions) == 1:
                move = moves[actions[-1]]
            else:
                move = moves[actions[-2]]
            path_distance = 0

            if distance < 8:

                up_path = False
                down_path = False
                isolation = True

                try:
                    for i in range(safe_zone):
                        for j in range(safe_zone):
                            if game.board[i][game.size - 1 - j] == 0:
                                end_point = None
                                actions.clear()
                                open_list.clear()
                                close_list.clear()
                                close_list = copy.deepcopy(close_list_fixed)

                                end_point = Node(None, i, game.size - 1 - j)

                                if find_the_path(start_point):
                                    path_distance = 0
                                    up_path = True
                                    raise Exception
                except Exception as e:
                    pass

                try:
                    for i in range(safe_zone):
                        for j in range(safe_zone):
                            if game.board[game.size - 1 - i][j] == 0:
                                end_point = None
                                actions.clear()
                                open_list.clear()
                                close_list.clear()
                                close_list = copy.deepcopy(close_list_fixed)

                                end_point = Node(None, game.size - 1 - i, j)

                                if find_the_path(start_point):
                                    # print('up_down:', i, j)
                                    path_distance = 0
                                    down_path = True
                                    raise Exception
                except Exception as e:
                    pass

                if up_path is True and down_path is True:
                    isolation = False

                start_point = None

                start_point = Node(None, move[0], move[1])
                # print('real:', location_self)
                # print('predict:', move)

                if self.area_size[0] >= self.area_size[1]:
                    try:
                        for i in range(safe_zone):
                            for j in range(safe_zone):
                                if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) >= \
                                        game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                        and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                    end_point = None
                                    actions.clear()
                                    open_list.clear()
                                    close_list.clear()
                                    close_list = copy.deepcopy(close_list_fixed)
                                    block_node = Node(None, move[0], move[1])
                                    close_list[(block_node.x, block_node.y)] = block_node

                                    try:
                                        block_node = Node(None, location_rival[0] - 1, location_rival[1])
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0] + 1, location_rival[1])
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0], location_rival[1] - 1)
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0], location_rival[1] + 1)
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass

                                    end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))

                                    if find_the_path(start_point):
                                        # print('up_down:', i, j)
                                        path_distance = 0
                                        trace_back = False
                                        raise Exception

                    except Exception as e:
                        pass

                    if isolation is True:
                        try:
                            for i in range(safe_zone):
                                for j in range(safe_zone):
                                    if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) <= \
                                            game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                            and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                        end_point = None
                                        actions.clear()
                                        open_list.clear()
                                        close_list.clear()
                                        close_list = copy.deepcopy(close_list_fixed)
                                        block_node = Node(None, move[0], move[1])
                                        close_list[(block_node.x, block_node.y)] = block_node

                                        try:
                                            block_node = Node(None, location_rival[0] - 1, location_rival[1])
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0] + 1, location_rival[1])
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0], location_rival[1] - 1)
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0], location_rival[1] + 1)
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass

                                        end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))

                                        if find_the_path(start_point):
                                            # print('up_up:', i, j)
                                            path_distance = 0
                                            trace_back = False
                                            raise Exception

                        except Exception as e:
                            pass

                elif self.area_size[0] < self.area_size[1]:
                    try:
                        for i in range(safe_zone):
                            for j in range(safe_zone):
                                if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) <= \
                                        game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                        and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                    game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                    end_point = None
                                    actions.clear()
                                    open_list.clear()
                                    close_list.clear()
                                    close_list = copy.deepcopy(close_list_fixed)
                                    block_node = Node(None, move[0], move[1])
                                    close_list[(block_node.x, block_node.y)] = block_node

                                    try:
                                        block_node = Node(None, location_rival[0] - 1, location_rival[1])
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0] + 1, location_rival[1])
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0], location_rival[1] - 1)
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0], location_rival[1] + 1)
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass

                                    end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))

                                    if find_the_path(start_point):
                                        # print('down_up:', i, j)
                                        path_distance = 0
                                        trace_back = False
                                        raise Exception

                    except Exception as e:
                        pass

                    if isolation is True:
                        try:
                            for i in range(safe_zone):
                                for j in range(safe_zone):
                                    if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) >= \
                                            game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                            and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                        game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                        end_point = None
                                        actions.clear()
                                        open_list.clear()
                                        close_list.clear()
                                        close_list = copy.deepcopy(close_list_fixed)
                                        block_node = Node(None, move[0], move[1])
                                        close_list[(block_node.x, block_node.y)] = block_node

                                        try:
                                            block_node = Node(None, location_rival[0] - 1, location_rival[1])
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0] + 1, location_rival[1])
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0], location_rival[1] - 1)
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0], location_rival[1] + 1)
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass

                                        end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))

                                        if find_the_path(start_point):
                                            # print('down_down:', i, j)
                                            path_distance = 0
                                            trace_back = False
                                            raise Exception

                        except Exception as e:
                            pass
            else:
                trace_back = False
        else:
            trace_back = True

        if trace_back is True:
            start_point = None

            weight = -1
            start_point = Node(None, location_self[0], location_self[1])

            path_found = False

            if self.area_size[0] >= self.area_size[1]:
                try:
                    for i in range(safe_zone):
                        for j in range(safe_zone):
                            if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) >= \
                                    game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                    and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                end_point = None
                                actions.clear()
                                end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))
                                open_list.clear()
                                close_list.clear()
                                close_list = copy.deepcopy(close_list_fixed)

                                if find_the_path(start_point):
                                    apply_path(end_point.father)
                                    # print('target:', i, j)
                                    if len(actions) == 1:
                                        move = moves[actions[-1]]
                                    else:
                                        move = moves[actions[-2]]
                                        path_found = True
                                    path_distance = 0
                                    raise Exception
                except Exception as e:
                    pass

                if path_found is False:
                    try:
                        for i in range(safe_zone):
                            for j in range(safe_zone):
                                if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) <= \
                                        game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                        and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                    game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                    end_point = None
                                    actions.clear()
                                    end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))
                                    open_list.clear()
                                    close_list.clear()
                                    close_list = copy.deepcopy(close_list_fixed)

                                    if find_the_path(start_point):
                                        apply_path(end_point.father)
                                        # print('target:', i, j)
                                        if len(actions) == 1:
                                            move = moves[actions[-1]]
                                        else:
                                            move = moves[actions[-2]]
                                            path_found = True
                                        path_distance = 0
                                        raise Exception
                    except Exception as e:
                        pass

            elif self.area_size[0] < self.area_size[1]:
                try:
                    for i in range(safe_zone):
                        for j in range(safe_zone):
                            if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) <= \
                                    game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                    and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                end_point = None
                                actions.clear()
                                end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))
                                open_list.clear()
                                close_list.clear()
                                close_list = copy.deepcopy(close_list_fixed)

                                if find_the_path(start_point):
                                    apply_path(end_point.father)
                                    # print('target:', i, j)
                                    if len(actions) == 1:
                                        move = moves[actions[-1]]
                                    else:
                                        move = moves[actions[-2]]
                                        path_found = True
                                    path_distance = 0
                                    raise Exception
                except Exception as e:
                    pass

                if path_found is False:
                    try:
                        for i in range(safe_zone):
                            for j in range(safe_zone):
                                if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) >= \
                                        game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                        and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                    game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                    end_point = None
                                    actions.clear()
                                    end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))
                                    open_list.clear()
                                    close_list.clear()
                                    close_list = copy.deepcopy(close_list_fixed)

                                    if find_the_path(start_point):
                                        apply_path(end_point.father)
                                        # print('target:', i, j)
                                        if len(actions) == 1:
                                            move = moves[actions[-1]]
                                        else:
                                            move = moves[actions[-2]]
                                            path_found = True
                                        path_distance = 0
                                        raise Exception
                    except Exception as e:
                        pass

            if path_found is False:
                # print('random')
                legal_moves = game.get_legal_moves(self.player_id)
                np.random.shuffle(legal_moves)
                move = legal_moves[0]

        # print(time.time() - stopwatch)
        return move


class KhanivoreAgentAppendant:

    # If the game size has been changed, changing the number '19' to 'game.size' minus one in parameter 'self.last_rival'
    def __init__(self, player_id):
        self.player_id = player_id
        self.lock_1 = False
        self.lock_2 = False
        self.last_rival = [19 - self.player_id, 19 - self.player_id]
        self.reverse_position = int((3 - self.player_id) * 9.5)
        self.zone_key = int((self.player_id - 1) * 0.5)
        self.area_size = [0, 0]

    def choose_move(self, game):
        global start_point, end_point, actions, open_list, close_list, weight, map_border, path_distance
        # stopwatch = time.time()
        trace_back = True
        safe_zone = int(game.size * 0.3)

        if game.board_type == 'rocky' and self.lock_1 is False:
            self.lock_1 = True
            self.lock_2 = True
            map_border = (game.size, game.size)
            for i in range(game.size):
                for j in range(game.size):
                    if game.board[i][j] == 4:
                        if i < j:
                            self.area_size[0] += 1
                        elif i > j:
                            self.area_size[1] += 1
                        block_node = Node(None, i, j)
                        close_list_fixed_1[(block_node.x, block_node.y)] = block_node
        elif game.board_type == 'default' and self.lock_1 is False:
            self.lock_1 = True
            self.lock_2 = True
            map_border = (game.size, game.size)

        elif game.board_type == 'obstacles' and self.lock_1 is False:
            self.lock_1 = True
            self.lock_2 = True
            self.last_rival = [9 - self.player_id, 4]
            map_border = (10, 10)
            for i in range(10):
                for j in range(10):
                    if game.board[i][j] == 4:
                        block_node = Node(None, i, j)
                        close_list_fixed_1[(block_node.x, block_node.y)] = block_node
        bias = []
        moves = []

        start_point = None
        end_point = None
        open_list.clear()
        close_list.clear()
        actions.clear()

        location_self = game.get_player_position(self.player_id)

        if self.lock_2 is False:
            if location_self[0] == game.size - 1 - self.reverse_position and location_self[1] == game.size - 1 - self.reverse_position:
                close_list_fixed_1.clear()
                self.area_size.clear()
                self.area_size = [0, 0]
                self.lock_1 = False
        self.lock_2 = False

        block_node = Node(None, location_self[0], location_self[1])
        close_list_fixed_1[(block_node.x, block_node.y)] = block_node

        if location_self[0] < location_self[1]:
            self.area_size[0] += 1
        elif location_self[0] > location_self[1]:
            self.area_size[1] += 1

        location_rival = game.get_player_position(4 - self.player_id)
        block_node = Node(None, location_rival[0], location_rival[1])
        close_list_fixed_1[(block_node.x, block_node.y)] = block_node

        if location_rival[0] < location_rival[1]:
            self.area_size[0] += 1
        elif location_rival[0] > location_rival[1]:
            self.area_size[1] += 1

        row = self.last_rival[0] - location_rival[0]
        column = self.last_rival[1] - location_rival[1]

        bias.clear()

        if row == 1 and column == 0:
            bias.extend([-1, 0])
        elif row == -1 and column == 0:
            bias.extend([1, 0])
        elif row == 0 and column == 1:
            bias.extend([0, -1])
        elif row == 0 and column == -1:
            bias.extend([0, 1])
        else:
            bias.extend([0, 0])

        self.last_rival = location_rival

        edge = False
        if location_self[0] == 0 or location_self[0] == game.size - 1 or location_self[1] == 0 or location_self[1] == game.size - 1:
            edge = True

        if location_rival[0] + bias[0] < 0 or location_rival[0] + bias[0] > game.size - 1 or \
                location_rival[1] + bias[1] < 0 or location_rival[1] + bias[1] > game.size - 1:
            bias.clear()
            bias.extend([0, 0])

        distance = abs(location_self[0] - location_rival[0] - bias[0]) + abs(location_self[1] - location_rival[1] - bias[1])

        close_list = copy.deepcopy(close_list_fixed_1)

        weight = 1
        start_point = Node(None, location_self[0], location_self[1])

        if game.board[location_rival[0] + bias[0]][location_rival[1] + bias[1]] == 0:
            end_point = Node(None, location_rival[0] + bias[0], location_rival[1] + bias[1])

        else:
            end_point = Node(None, location_rival[0], location_rival[1])

        moves.extend([[location_self[0] - 1, location_self[1]], [location_self[0] + 1, location_self[1]],
                      [location_self[0], location_self[1] - 1], [location_self[0], location_self[1] + 1]])

        if find_the_path(start_point) and (edge is False or distance > 1):
            apply_path(end_point.father)
            if len(actions) == 1:
                move = moves[actions[-1]]
            else:
                move = moves[actions[-2]]
            path_distance = 0

            if distance < 8:

                up_path = False
                down_path = False
                isolation = True

                try:
                    for i in range(safe_zone):
                        for j in range(safe_zone):
                            if game.board[i][game.size - 1 - j] == 0:
                                end_point = None
                                actions.clear()
                                open_list.clear()
                                close_list.clear()
                                close_list = copy.deepcopy(close_list_fixed_1)

                                end_point = Node(None, i, game.size - 1 - j)

                                if find_the_path(start_point):
                                    path_distance = 0
                                    up_path = True
                                    raise Exception
                except Exception as e:
                    pass

                try:
                    for i in range(safe_zone):
                        for j in range(safe_zone):
                            if game.board[game.size - 1 - i][j] == 0:
                                end_point = None
                                actions.clear()
                                open_list.clear()
                                close_list.clear()
                                close_list = copy.deepcopy(close_list_fixed_1)

                                end_point = Node(None, game.size - 1 - i, j)

                                if find_the_path(start_point):
                                    # print('up_down:', i, j)
                                    path_distance = 0
                                    down_path = True
                                    raise Exception
                except Exception as e:
                    pass

                if up_path is True and down_path is True:
                    isolation = False

                start_point = None

                start_point = Node(None, move[0], move[1])
                # print('real:', location_self)
                # print('predict:', move)

                # if location_rival[0] - location_rival[1] <= 0:
                if self.area_size[0] >= self.area_size[1]:
                    try:
                        for i in range(safe_zone):
                            for j in range(safe_zone):
                                if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) >= \
                                        game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                        and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                    end_point = None
                                    actions.clear()
                                    open_list.clear()
                                    close_list.clear()
                                    close_list = copy.deepcopy(close_list_fixed_1)
                                    block_node = Node(None, move[0], move[1])
                                    close_list[(block_node.x, block_node.y)] = block_node

                                    try:
                                        block_node = Node(None, location_rival[0] - 1, location_rival[1])
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0] + 1, location_rival[1])
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0], location_rival[1] - 1)
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0], location_rival[1] + 1)
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass

                                    end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))

                                    if find_the_path(start_point):
                                        # print('up_down:', i, j)
                                        path_distance = 0
                                        trace_back = False
                                        raise Exception

                    except Exception as e:
                        pass

                    if isolation is True:
                        try:
                            for i in range(safe_zone):
                                for j in range(safe_zone):
                                    if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) <= \
                                            game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                            and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                        end_point = None
                                        actions.clear()
                                        open_list.clear()
                                        close_list.clear()
                                        close_list = copy.deepcopy(close_list_fixed_1)
                                        block_node = Node(None, move[0], move[1])
                                        close_list[(block_node.x, block_node.y)] = block_node

                                        try:
                                            block_node = Node(None, location_rival[0] - 1, location_rival[1])
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0] + 1, location_rival[1])
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0], location_rival[1] - 1)
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0], location_rival[1] + 1)
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass

                                        end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))

                                        if find_the_path(start_point):
                                            # print('up_up:', i, j)
                                            path_distance = 0
                                            trace_back = False
                                            raise Exception

                        except Exception as e:
                            pass

                # elif location_rival[0] - location_rival[1] > 0:
                elif self.area_size[0] < self.area_size[1]:
                    try:
                        for i in range(safe_zone):
                            for j in range(safe_zone):
                                if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) <= \
                                        game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                        and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                    game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                    end_point = None
                                    actions.clear()
                                    open_list.clear()
                                    close_list.clear()
                                    close_list = copy.deepcopy(close_list_fixed_1)
                                    block_node = Node(None, move[0], move[1])
                                    close_list[(block_node.x, block_node.y)] = block_node

                                    try:
                                        block_node = Node(None, location_rival[0] - 1, location_rival[1])
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0] + 1, location_rival[1])
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0], location_rival[1] - 1)
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass
                                    try:
                                        block_node = Node(None, location_rival[0], location_rival[1] + 1)
                                        close_list[(block_node.x, block_node.y)] = block_node
                                    except Exception as e:
                                        pass

                                    end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))

                                    if find_the_path(start_point):
                                        # print('down_up:', i, j)
                                        path_distance = 0
                                        trace_back = False
                                        raise Exception

                    except Exception as e:
                        pass

                    if isolation is True:
                        try:
                            for i in range(safe_zone):
                                for j in range(safe_zone):
                                    if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) >= \
                                            game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                            and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                        game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                        end_point = None
                                        actions.clear()
                                        open_list.clear()
                                        close_list.clear()
                                        close_list = copy.deepcopy(close_list_fixed_1)
                                        block_node = Node(None, move[0], move[1])
                                        close_list[(block_node.x, block_node.y)] = block_node

                                        try:
                                            block_node = Node(None, location_rival[0] - 1, location_rival[1])
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0] + 1, location_rival[1])
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0], location_rival[1] - 1)
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass
                                        try:
                                            block_node = Node(None, location_rival[0], location_rival[1] + 1)
                                            close_list[(block_node.x, block_node.y)] = block_node
                                        except Exception as e:
                                            pass

                                        end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))

                                        if find_the_path(start_point):
                                            # print('down_down:', i, j)
                                            path_distance = 0
                                            trace_back = False
                                            raise Exception

                        except Exception as e:
                            pass
            else:
                trace_back = False
        else:
            trace_back = True

        if trace_back is True:
            start_point = None

            weight = -1
            start_point = Node(None, location_self[0], location_self[1])

            path_found = False

            # if location_rival[0] - location_rival[1] <= 0:
            if self.area_size[0] >= self.area_size[1]:
                try:
                    for i in range(safe_zone):
                        for j in range(safe_zone):
                            if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) >= \
                                    game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                    and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                end_point = None
                                actions.clear()
                                end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))
                                open_list.clear()
                                close_list.clear()
                                close_list = copy.deepcopy(close_list_fixed_1)

                                if find_the_path(start_point):
                                    apply_path(end_point.father)
                                    # print('target:', i, j)
                                    if len(actions) == 1:
                                        move = moves[actions[-1]]
                                    else:
                                        move = moves[actions[-2]]
                                        path_found = True
                                    path_distance = 0
                                    raise Exception
                except Exception as e:
                    pass

                if path_found is False:
                    try:
                        for i in range(safe_zone):
                            for j in range(safe_zone):
                                if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) <= \
                                        game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                        and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                    game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                    end_point = None
                                    actions.clear()
                                    end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))
                                    open_list.clear()
                                    close_list.clear()
                                    close_list = copy.deepcopy(close_list_fixed_1)

                                    if find_the_path(start_point):
                                        apply_path(end_point.father)
                                        # print('target:', i, j)
                                        if len(actions) == 1:
                                            move = moves[actions[-1]]
                                        else:
                                            move = moves[actions[-2]]
                                            path_found = True
                                        path_distance = 0
                                        raise Exception
                    except Exception as e:
                        pass

            # elif location_rival[0] - location_rival[1] > 0:
            elif self.area_size[0] < self.area_size[1]:
                try:
                    for i in range(safe_zone):
                        for j in range(safe_zone):
                            if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) <= \
                                    game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                    and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                end_point = None
                                actions.clear()
                                end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))
                                open_list.clear()
                                close_list.clear()
                                close_list = copy.deepcopy(close_list_fixed_1)

                                if find_the_path(start_point):
                                    apply_path(end_point.father)
                                    # print('target:', i, j)
                                    if len(actions) == 1:
                                        move = moves[actions[-1]]
                                    else:
                                        move = moves[actions[-2]]
                                        path_found = True
                                    path_distance = 0
                                    raise Exception
                except Exception as e:
                    pass

                if path_found is False:
                    try:
                        for i in range(safe_zone):
                            for j in range(safe_zone):
                                if game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key) >= \
                                        game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key) \
                                        and game.board[game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key)][
                                    game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key)] == 0:
                                    end_point = None
                                    actions.clear()
                                    end_point = Node(None, game.size - 1 - self.reverse_position + i * (1 - 2 * self.zone_key), game.size - 1 - self.reverse_position + j * (1 - 2 * self.zone_key))
                                    open_list.clear()
                                    close_list.clear()
                                    close_list = copy.deepcopy(close_list_fixed_1)

                                    if find_the_path(start_point):
                                        apply_path(end_point.father)
                                        # print('target:', i, j)
                                        if len(actions) == 1:
                                            move = moves[actions[-1]]
                                        else:
                                            move = moves[actions[-2]]
                                            path_found = True
                                        path_distance = 0
                                        raise Exception
                    except Exception as e:
                        pass

            if path_found is False:
                # print('random')
                legal_moves = game.get_legal_moves(self.player_id)
                np.random.shuffle(legal_moves)
                move = legal_moves[0]

        # print(time.time() - stopwatch)
        return move


class SoloDriveAgent:

    # # # # # # # # # # # # # # # # # # # # # # #
    #  Readme:                                  #
    #  I am the Solo Drive Agent created by Lei #
    #  as the training player                   #
    #  Edited in 2020/04/03                     #
    # # # # # # # # # # # # # # # # # # # # # # #

    def __init__(self, player_id):
        self.player_id = player_id

    def choose_move(self, game):
        move = 0
        moves = []
        direction = [0, 0, 0, 0]
        legal_moves = game.get_legal_moves(self.player_id)
        location_self = game.get_player_position(self.player_id)

        moves.extend([[location_self[0] - 1, location_self[1]], [location_self[0] + 1, location_self[1]],
                      [location_self[0], location_self[1] - 1], [location_self[0], location_self[1] + 1]])

        if len(legal_moves):
            for i in range(len(legal_moves)):
                row = location_self[0] - legal_moves[i][0]
                column = location_self[1] - legal_moves[i][1]

                if self.player_id == 1:

                    if row == 1 and column == 0:
                        direction[0] = 1
                    elif row == -1 and column == 0:
                        direction[1] = 3
                    elif row == 0 and column == 1:
                        direction[2] = 1
                    elif row == 0 and column == -1:
                        direction[3] = 3

                elif self.player_id == 3:

                    if row == 1 and column == 0:
                        direction[0] = 3
                    elif row == -1 and column == 0:
                        direction[1] = 1
                    elif row == 0 and column == 1:
                        direction[2] = 3
                    elif row == 0 and column == -1:
                        direction[3] = 1

        count = sum(direction)
        direction[0] = direction[0] / count
        direction[1] = direction[1] / count
        direction[2] = direction[2] / count
        direction[3] = direction[3] / count

        rand = np.random.rand()
        probability = 0.0

        i = 0
        for item in zip(moves, direction):
            i += 1
            probability += item[1]
            if rand < probability:
                move = item[0]
                break

        return move


# Ths is an example of an agent which simply picks a move at random.
class RandomAgent:

    def __init__(self, player_id):
        self.player_id = player_id

    def choose_move(self, game):
        # Get an array of legal moves from your current position.
        legal_moves = game.get_legal_moves(self.player_id)

        # Shuffle the legal moves and pick the first one. This is equivalent
        # to choosing a move randomly with no logic.
        np.random.shuffle(legal_moves)
        return legal_moves[0]
        return move

    # This handler will be used to time-out actions/games which take too long to compute.
    # Note that this handler does not function on Windows based systems.
    def signal_handler(signum, frame):
        raise TimeoutError("Timed out!")


class WallHuggerAgent:
    def __init__(self, player_id):
        self.player_id = player_id

    def choose_move(self, game):
        # Get an array of legal moves from your current position.
        legal_moves = game.get_legal_moves(self.player_id)
        # Hugs the nearest wall until it can't then hugs the next closest.
        return legal_moves[0]


class TronGame:

    def __init__(self, agent1_class, agent2_class, board_size, board_type):
        # Default board.
        if board_type == 'default':
            self.size = board_size
        # Board with obstacles and a fixed size of 10x10.
        elif board_type == 'obstacles':
            self.size = 10
        elif board_type == 'rocky':
            self.size = board_size
        else:
            raise ValueError('Invalid board type.')
# 46206c8fb51329e6a3ba88cfccef498cd730a3b8783f965c41eaf3e18532594c
# 0e3c76e64d62dab9f53e56832e1b95d6397e0dc0cd93201ade3d463e6c45e020
# 5cb237c50a74473324d3f43f9bac9ebb7410c0e3adc71b79c8c74a3b3b7db953
        # Build the game board.
        self.board_type = board_type
        self.board = self.build_board(board_type)

        # Initialize the game state variables and set the values using the
        # 'reset_game()' method.
        self.reset_game()

        # Initialize our agents.
        self.agent1 = agent1_class(1)
        self.agent2 = agent2_class(3)

    def build_board(self, board_type):
        """
        This method takes a board_type: ['default', 'obstacles'] and returns a
        new board (NumPy matrix).
        """

        # Default board.
        if board_type == 'default':
            board = np.zeros((self.size, self.size))
            board[0, 0] = 1
            board[self.size - 1, self.size - 1] = 3

        # Board with obstacles and a fixed size of 10x10.
        elif board_type == 'obstacles':
            board = np.zeros((10, 10))
            board[1, 4] = 1
            board[8, 4] = 3
            board[3:7, 0:4] = 4
            board[3:7, 6:] = 4
        # Board with obstacles and a fixed size of 10x10.
        elif board_type == 'rocky':
            board = np.zeros((self.size, self.size))
            a = np.random.randint(2, size=(self.size, self.size))
            b = np.random.randint(2, size=(self.size, self.size))
            c = np.random.randint(2, size=(self.size, self.size))
            d = np.random.randint(2, size=(self.size, self.size))

            board = board + (a * b * c * d) * 4
            board[0, 0] = 1
            board[self.size - 1, self.size - 1] = 3


        else:
            raise ValueError('Invalid board type.')

        return board

    def reset_game(self):
        """
        Helper method which re-initializes the game state.
        """

        self.board = self.build_board(self.board_type)

    def get_player_position(self, player_id, board=None):
        """
        Helper method which finds the coordinate of the specified player ID
        on the board.
        """

        if board is None:
            board = self.board
        coords = np.asarray(board == player_id).nonzero()
        coords = np.stack((coords[0], coords[1]), 1)
        coords = np.reshape(coords, (-1, 2))
        return coords[0]

    def get_legal_moves(self, player, board=None):
        """
        This method returns a list of legal moves for a given player ID and
        board.
        """

        if board is None:
            board = self.board

        # Get the current player position and then check for all possible
        # legal moves.
        prev = self.get_player_position(player, board)
        moves = []

        # Up
        if (prev[0] != 0) and (board[prev[0] - 1, prev[1]] == 0):
            moves.append([prev[0] - 1, prev[1]])
        # Down
        if (prev[0] != self.size - 1) and (board[prev[0] + 1, prev[1]] == 0):
            moves.append([prev[0] + 1, prev[1]])
        # Left
        if (prev[1] != 0) and (board[prev[0], prev[1] - 1] == 0):
            moves.append([prev[0], prev[1] - 1])
        # Right
        if (prev[1] != self.size - 1) and (board[prev[0], prev[1] + 1] == 0):
            moves.append([prev[0], prev[1] + 1])

        return moves

    def examine_move(self, player, coordinate, board):
        board_clone = board.copy()
        prev = self.get_player_position(player, board_clone)
        board_clone[prev[0], prev[1]] = 4
        board_clone[coordinate[0], coordinate[1]] = player
        return board_clone

    @staticmethod
    def view_game(board_history):
        """
        This is a helper function which takes a board history
        (i.e., a list of board states) and creates an animation of the game
        as it progresses.
        """

        fig, ax = plt.subplots()
        colors = ['black', 'blue', 'pink', 'white', 'red', 'yellow']
        cmap = matplotlib.colors.ListedColormap(colors)
        bounds = np.linspace(0, 5, 6)
        norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
        matrix = ax.matshow(board_history[0], cmap=cmap, norm=norm)

        def update(i):
            matrix.set_array(board_history[i])
            return matrix

        ani = FuncAnimation(fig, update, frames=len(board_history), interval=100)
        plt.show()
        # return HTML(ani.to_html5_video())

    def play_series(self, num_games, debug=True):
        """
        This method plays a series of games between the two agents.

        It returns two objects: (i) a tuple which indicates the number of
        wins per player, and (ii) a history of the board state as the game
        progresses.
        """

        wins_player_1 = 0
        wins_player_2 = 0
        games = []
        winner_history = []
        for i in range(num_games):
            print("round %s" % int(i+1))
            winning_player_id, board_history = self.__play_game(debug=debug)
            games.append(board_history)
            winner_history.append(winning_player_id)
            if winning_player_id == 1:
                wins_player_1 += 1
            elif winning_player_id == 2:
                wins_player_2 += 1
            else:
                raise ValueError('Invalid winning player ID.')

        print(f'Finished playing [{num_games}] games.')
        print(f'Player 1 won [{wins_player_1}] games and has a win-rate of [{wins_player_1 / num_games * 100}%].')
        print(f'Player 2 won [{wins_player_2}] games and has a win-rate of [{wins_player_2 / num_games * 100}%].')
        return (wins_player_1, wins_player_2), games, winner_history

    def __apply_move(self, player, coordinate):
        """
        This private method moves a player ID to a new coordinate and obstructs
        the previously occupied tile.
        """

        prev_coord = self.get_player_position(player)

        self.board[prev_coord[0], prev_coord[1]] = 4
        self.board[coordinate[0], coordinate[1]] = player

    def __play_game(self, debug=True):
        """
        This private method plays a single game between the two agents. It
        returns the winning player ID as well as the history of the board
        as the game progresses.
        """

        # Reset the game.
        self.reset_game()
        board_history = []

        # Play the game until it's conclusion.
        while True:
            # ---------------------------------------
            # PLAYER 1's TURN
            # ---------------------------------------
            # Check legal moves.
            poss_moves = self.get_legal_moves(1)
            if not len(poss_moves):
                if debug:
                    print("Player 2 wins")
                winning_player_id = 2
                break

            # Compute and apply the chosen move.
            # signal.alarm(3)
            try:
                move = self.agent1.choose_move(self)
            except Exception as e:
                print(e)
                print("There was an error while choosing a move.")
                print("Player 2 wins")
                winning_player_id = 2
                break
            self.__apply_move(1, move)

            # Record keeping.
            board_history.append(np.array(self.board.copy()))
            # if False:
            #     print(self.board)
            #     time.sleep(.5)
            #     clear_output()

            # ---------------------------------------
            # PLAYER 2's TURN
            # ---------------------------------------
            # Check legal moves.
            poss_moves = self.get_legal_moves(3)
            if not len(poss_moves):
                if debug:
                    print("Player 1 wins")
                winning_player_id = 1
                break

            # Compute and apply the chosen move.
            # signal.alarm(3)
            try:
                move = self.agent2.choose_move(self)
            except Exception as e:
                print(e)
                print("There was an error while choosing a move.")
                print("Player 1 wins")
                winning_player_id = 1
                break
            self.__apply_move(3, move)

            # Record keeping.
            board_history.append(np.array(self.board.copy()))
        #     if False:
        #         print(self.board)
        #         time.sleep(.5)
        #         clear_output()
        # signal.alarm(0)

        return winning_player_id, board_history


my_tron_game = TronGame(board_size=20, agent1_class=KhanivoreAgent, agent2_class=PlayerAgent, board_type='rocky')
# only support the 'default' and 'rocky' map temperately when using the Khanivore Agent

(player1_wins, player2_wins), game_histories, winner_history = my_tron_game.play_series(num_games=1, debug=False)

TronGame.view_game(game_histories[-1])

# print(winner_history)
