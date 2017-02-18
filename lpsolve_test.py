import operator
import random

from lp_solve import *
from lpsolve55 import *


def doit(item_number, order_list, cost_list):
    col_num = item_number * item_number  # number of variables
    lp = lpsolve('make_lp', 0, col_num)

    # set all variables to be binary
    lpsolve('set_binary', lp, [1] * col_num)

    # set object function
    lpsolve('set_minim', lp)

    vec = []
    for i in range(0, item_number):
        vec += [x * (item_number - i) for x in cost_list]
    lpsolve('set_obj_fn', lp, vec)

    # set constraint 1
    for k in range(0, item_number):
        # sum of every row should be 1
        vec1 = ([0] * item_number) * k + ([1] * item_number) + ([0] * item_number * (item_number - k - 1))
        lpsolve('add_constraint', lp, vec1, EQ, 1)
        # sum of every column should be 1
        vec2 = (([0] * k) + [1] + [0] * (item_number - k - 1)) * item_number
        lpsolve('add_constraint', lp, vec2, EQ, 1)

    # set constraint 2
    for pre, des in order_list:
        vec_stuff = [x for x in range(0, item_number)]
        vec_pre = ([0] * item_number) * pre + vec_stuff + ([0] * item_number * (item_number - pre - 1))
        vec_des = ([0] * item_number) * des + vec_stuff + ([0] * item_number * (item_number - des - 1))
        vec = map(operator.sub, vec_pre, vec_des)
        lpsolve('add_constraint', lp, vec, LE, 0)

    # set timeout
    lpsolve('set_timeout', lp, 60)

    lpsolve('solve', lp)
    vars = lpsolve('get_variables', lp)[0]

    for i in range(0, col_num, item_number):
        print vars[i:i+item_number]

    return vars

def main():
    lp = lpsolve('make_lp', 0, 4)
    # set object function
    obj_fn_row = [1, 3, 6.24, 0.1]
    lpsolve('set_obj_fn', lp, obj_fn_row)
    lpsolve('set_minim', lp)

    # set constraints
    cons_row1 = [0, 78.26, 0, 2.9, GE, 92.3]
    cons_row2 = [0.24, 0, 11.31, 0, LE, 14.8]
    cons_row3 = [12.68, 0, 0.08, 0.9, GE, 4]
    cons = [cons_row1, cons_row2, cons_row3]
    for cons_row in cons:
        lpsolve('add_constraint', lp, cons_row[0:4], cons_row[4], cons_row[5])

    # set bound
    bound1 = ['set_lowbo', 1, 28.6]
    bound2 = ['set_lowbo', 4, 18]
    bound3 = ['set_upbo', 4, 48.98]
    bounds = [bound1, bound2, bound3]
    for bound in bounds:
        lpsolve(bound[0], lp, *bound[1:])

    # set time out

    # solve the lp and get results
    lpsolve('solve', lp)
    obj = lpsolve('get_objective', lp)
    vars = lpsolve('get_variables', lp)[0]

    print obj
    print vars
    return vars

def performance_test():
    item_number = 15
    cost = random.sample(xrange(100), item_number)
    order_list = []
    for i in range(0, item_number-1):
        order_list.append((i, i+1))
    doit(item_number, order_list, cost)


def test():
    cost = [1, 100, 99, 1, 3]
    order_list = [(0, 1), (1, 3), (0, 2), (2,4)]
    item_number = 5
    doit(item_number, order_list, cost)


if __name__ == '__main__':
    performance_test()
