import random

from trace_to_dag import TraceNode


def show_node_list(node_list):
    print [x.code for x in node_list]


def get_trace(file_name):
    from trace_to_dag import parse_web_lbr
    dag_list = parse_web_lbr(file_name)
    return dag_list


def topology_sort(node_list, graph, func):
    root = node_list[0]

    result_list = []
    zero_inedge_list = [root]
    while zero_inedge_list:
        picked_node = func(zero_inedge_list)
        result_list.append(picked_node)
        if graph.has_key(picked_node):
            for node in graph[picked_node]:
                if node.incoming_edge_num == 1:
                    node.incoming_edge_num = 0
                    zero_inedge_list.append(node)
                else:
                    node.incoming_edge_num -= 1

    return result_list


def get_traversal_list(node_list, graph, mode):
    if mode == 'random':
        def random_func(zero_inedge_list):
            index = random.sample(xrange(len(zero_inedge_list)), 1)[0]
            return zero_inedge_list.pop(index)

        return topology_sort(node_list, graph, random_func)

    if mode == 'greedy':
        def greedy_func(zero_inedge_list):
            max_node = min(zero_inedge_list, key=lambda x: x.trans_time_ms)
            zero_inedge_list.remove(max_node)
            return max_node

        return topology_sort(node_list, graph, greedy_func)

    if mode == 'optimal':
        from lpsolve_test import doit
        order_list = []
        for index, node in enumerate(node_list):
            setattr(node, 'index', index)
        for node in node_list:
            if graph.has_key(node):
                for sub_node in graph[node]:
                    order_list.append((node.index, sub_node.index))
        cost = [node.trans_time_ms for node in node_list]
        item_number = len(node_list)
        vars = doit(item_number, order_list, cost)
        result_order = []
        for i in range(0, item_number * item_number, item_number):
            row = vars[i:i + item_number]
            index = row.index(max(row))
            result_order.append(index)

        result = [-1] * len(node_list)
        for i, order in enumerate(result_order):
            result[order] = node_list[i]
        return result


def get_time(traversal_list):
    used_time = 0
    # for node in traversal_list:
    #     used_time += used_time + node.trans_time_ms
    for i, node in enumerate(traversal_list):
        used_time += (len(traversal_list) - i) * node.trans_time_ms
    return used_time


def show_performace_gain(time_random, time_optimal, time_greedy):
    print 'random: %s, greedy: %s, optimal: %s' % (time_random, time_greedy, time_optimal)
    print 'optimal compare to greedy: %f' % ((time_greedy - time_optimal) / float(time_greedy))
    print 'optimal compare to random: %f' % ((time_random - time_optimal) / float(time_random))


def generate_random_graph(dag_facebook):
    node_list = [TraceNode(start_time=0, size=0, trans_time=0, type='') for i in range(0, 10)]
    for i in range(0, 10):
        node_list[i].code = chr(i + ord('0'))

    graph1 = {}
    graph1[node_list[0]] = [node_list[1], node_list[2], node_list[3], node_list[4]]
    graph1[node_list[3]] = [node_list[5], node_list[6], node_list[7]]
    graph1[node_list[6]] = [node_list[8]]
    graph1[node_list[7]] = [node_list[8]]
    graph1[node_list[8]] = [node_list[9]]

    graph2 = {}
    graph2[node_list[0]] = [node_list[1], node_list[2], node_list[3]]
    graph2[node_list[1]] = [node_list[4], node_list[5]]
    graph2[node_list[2]] = [node_list[7]]
    graph2[node_list[3]] = [node_list[6]]
    graph2[node_list[7]] = [node_list[8]]
    graph2[node_list[6]] = [node_list[8]]
    graph2[node_list[8]] = [node_list[9]]

    graph3 = {}
    graph3[node_list[0]] = [node_list[1], node_list[2], node_list[3]]
    graph3[node_list[2]] = [node_list[4]]
    graph3[node_list[4]] = [node_list[5]]
    graph3[node_list[5]] = [node_list[6], node_list[7]]
    graph3[node_list[7]] = [node_list[8], node_list[9]]

    graph_list = [graph1, graph2, graph3]

    for i in xrange(0, 100):
        # pick the graph and node list
        random_index = random.randint(0, 3)
        if random_index == 3:
            graph = dag_facebook.graph
            output_node_list = dag_facebook.node_list
        else:
            graph = graph_list[random_index]
            output_node_list = node_list
        # generate the random number as cost
        random_int_list = random.sample(range(20, 1000), 10)
        for node, trans_time in zip(output_node_list, random_int_list):
            node.trans_time_ms = trans_time
        yield random_index, output_node_list, graph


def reset_node_list(node_list, graph):
    for node in node_list:
        if hasattr(node, 'incoming_edge_num'):
            node.incoming_edge_num = 0
        else:
            setattr(node, 'incoming_edge_num', 0)
    for node in node_list:
        if graph.has_key(node):
            for sub_node in graph[node]:
                sub_node.incoming_edge_num += 1


def test():
    trace_file = 'data_lbr.csv'
    dag_list = get_trace(trace_file)
    dag_facebook = dag_list[1]
    pg_random, pg_greedy, pg_greedy_random = 0.0, 0.0, 0.0
    with open('result.txt', 'w') as fout:
        iter = 0
        # for index, node_list, graph in generate_random_graph(dag_facebook):
        for dag in dag_list:
            node_list = dag.node_list
            graph = dag.graph
            index = -1
            fout.write('iter: %d, graph index: %d\n' % (iter, index))
            fout.write('node list: %s \n' % (str([(node.code, node.trans_time_ms) for node in node_list])))
            reset_node_list(node_list, graph)
            fout.write(
                'incoming_edge before: %s\n' % (str([(node.code, node.incoming_edge_num) for node in node_list])))
            random_tl = get_traversal_list(node_list, graph, 'random')
            reset_node_list(node_list, graph)
            greedy_tl = get_traversal_list(node_list, graph, 'greedy')
            reset_node_list(node_list, graph)
            # optimal_tl = get_traversal_list(node_list, graph, 'optimal')
            random_tm = get_time(random_tl)
            greedy_tm = get_time(greedy_tl)
            # optimal_tm = get_time(optimal_tl)
            fout.write('incoming_edge after: %s\n' % (str([(node.code, node.incoming_edge_num) for node in node_list])))
            fout.write('random travel: %s \n' % (str([(node.code, node.trans_time_ms) for node in random_tl])))
            fout.write('greedy travel: %s \n' % (str([(node.code, node.trans_time_ms) for node in greedy_tl])))
            # fout.write('optimal travel: %s \n' % (str([(node.code, node.trans_time_ms) for node in optimal_tl])))
            # pg_random += (random_tm - optimal_tm) / float(random_tm)
            # pg_greedy += (greedy_tm - optimal_tm) / float(greedy_tm)
            pg_greedy_random_tmp = (random_tm - greedy_tm) / float(random_tm)
            # fout.write('%d %d %d %f %f\n\n' % (random_tm, greedy_tm, optimal_tm,
            #                                    (random_tm - optimal_tm) / float(random_tm),
            #                                    (greedy_tm - optimal_tm) / float(greedy_tm)))
            fout.write('%d %d %f\n\n' % (random_tm, greedy_tm, pg_greedy_random_tmp))
            iter += 1
            pg_greedy_random += pg_greedy_random_tmp
        # print 'average pg_random: %f, pg_greedy: %f' % (pg_random / iter, pg_greedy / iter)
        print iter
        print 'averge: %f' % (pg_greedy_random / iter)


def main():
    test()
    # trace_file = 'data_lbr_google.csv'
    # dag_list = get_trace(trace_file)
    # for dag in dag_list:
    #     random_traversal_list = get_traversal_list(dag, 'random')
    # optimal_traversal_list = get_traversal_list(dag, 'optimal')
    # greedy_traversal_list = get_traversal_list(dag, 'greedy')

    # time_random = get_time(random_traversal_list)
    # time_optimal = get_time(optimal_traversal_list)
    # time_greedy = get_time(greedy_traversal_list)
    #
    # show_performace_gain(time_random, time_optimal, time_greedy)


if __name__ == '__main__':
    main()
