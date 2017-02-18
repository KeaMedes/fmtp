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

    for node in node_list:
        if graph.has_key(node):
            for sub_node in graph[node]:
                if hasattr(sub_node, 'incoming_edge_num'):
                    sub_node.incoming_edge_num += 1
                else:
                    setattr(sub_node, 'incoming_edge_num', 1)

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
    for node in traversal_list:
        used_time += used_time + node.trans_time_ms
    return used_time


def show_performace_gain(time_random, time_optimal, time_greedy):
    print 'random: %s, greedy: %s, optimal: %s' % (time_random, time_greedy, time_optimal)
    print 'optimal compare to greedy: %f' % ((time_greedy - time_optimal) / float(time_greedy))
    print 'optimal compare to random: %f' % ((time_random - time_optimal) / float(time_random))


def generate_random_graph(dag_facebook):
    node_list = [TraceNode(start_time=0, size=0, trans_time=0, type='') for i in range(0, 10)]

    graph1 = {}
    graph1[node_list[0]] = [node_list[1], node_list[2], node_list[3], node_list[4]]
    graph1[node_list[3]] = [node_list[5], node_list[6], node_list[7]]
    graph1[node_list[6]] = [node_list[8]]
    graph1[node_list[7]] = [node_list[8]]
    graph1[node_list[8]] = [node_list[9]]

    graph2 = {}
    graph2[node_list[0]] = [node_list[1], node_list[2], node_list[3]]
    graph2[node_list[1]] = [node_list[4], node_list[5]]
    graph1[node_list[2]] = [node_list[7]]
    graph1[node_list[3]] = [node_list[6]]
    graph1[node_list[7]] = [node_list[8]]
    graph1[node_list[6]] = [node_list[8]]
    graph1[node_list[8]] = [node_list[9]]

    graph3 = {}
    graph3[node_list[0]] = [node_list[1], node_list[2], node_list[3]]
    graph3[node_list[2]] = [node_list[4]]
    graph3[node_list[4]] = [node_list[5]]
    graph3[node_list[5]] = [node_list[6], node_list[7]]
    graph3[node_list[7]] = [node_list[8], node_list[9]]

    graph_list = [graph1, graph2, graph3]

    for i in xrange(0, 10):
        random_index = random.randint(0, 3)
        if random_index == 3:
            graph = dag_facebook.graph
            output_node_list = dag_facebook.node_list
        else:
            graph = graph_list[random_index]
            output_node_list = node_list
        for node in output_node_list:
            node.trans_time_ms = random.randint(0, 1000)
            yield output_node_list, graph


def test():
    trace_file = 'data_lbr.csv'
    dag_list = get_trace(trace_file)
    # for i in range(0, 5):
    #     dag = dag_list[i]
    #     dag.to_dot()
        # random_traversal_list = get_traversal_list(dag, 'random')
        # greedy_traversal_list = get_traversal_list(dag, 'greedy')
        # optimal_traversal_list = get_traversal_list(dag, 'optimal')
        #
        # random_time = get_time(random_traversal_list)
        # greedy_time = get_time(greedy_traversal_list)
        # optimal_time = get_time(optimal_traversal_list)
        #
        # show_performace_gain(random_time, greedy_time, optimal_time)
    dag_facebook = dag_list[1]
    with open('result.txt', 'w') as fout:
        for node_list, graph in generate_random_graph(dag_facebook):
            random_tl = get_traversal_list(node_list, graph, 'random')
            greedy_tl = get_traversal_list(node_list, graph, 'greedy')
            optimal_tl = get_traversal_list(node_list, graph, 'optimal')

            random_tm, greedy_tm, optimal_tm = get_time(random_tl), get_time(greedy_tl), get_time(optimal_tl)
            fout.write('%d %d %d %f %f\n' % (random_tm, greedy_tm, optimal_tm,
                       (random_tm - optimal_tm) / float(random_tm),
                       (greedy_tm - optimal_tm) / float(greedy_tm)))


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
