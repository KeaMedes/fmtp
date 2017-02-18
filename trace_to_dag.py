import datetime
import csv
from graphviz import Digraph


class TraceNode(object):
    def __init__(self, start_time, size, trans_time, type):
        if start_time:
            self.start_time = datetime.datetime.strptime(start_time, '%H:%M:%S.%f')
        self.size = size
        if trans_time:
            self.trans_time_ms = int(trans_time[:-3])
        else:
            self.trans_time_ms = 0
        self.time_offset_ms = 0  # time delta in milliseconds format, 1/1000s
        self.type = type
        self.code = ''

    def set_code(self, code):
        self.code = code

    def is_static_file(self):
        return self.type in ['Image', 'TXT']

    def to_dot_desc(self):
        color = 'black'
        if self.type in ['Image', 'TXT']:
            color = 'red'
        elif self.type in ['JavaScript']:
            color = 'blue'
        elif self.type in ['HTML']:
            color = 'yellow'
        return {
            'label': '%s\n%s\n%dms' % (self.code, self.size, self.time_offset_ms),
            'color': color
        }


class TraceDAG(object):
    """
    DAG representation of a trace.
    Title is the web page name or the video name.
    """

    def __init__(self, title, node_list):
        self.title = title
        self.graph = {}
        self.node_list = node_list
        self.not_direct_path = {}
        self.level_list = []

    def add_edge(self, src, dst=None):
        if self.graph.has_key(src):
            self.graph[src] += [dst]
        else:
            if dst:
                self.graph[src] = [dst]
            else:
                self.graph[src] = []

    def remove_edge(self, src, dst):
        if self.graph.has_key(src):
            dst_list = self.graph[src]
            if dst in dst_list:
                dst_list.remove(dst)

    def has_edge(self, src, dst):
        if self.graph.has_key(src):
            dst_list = self.graph[src]
            if dst in dst_list:
                return True
        return False

    def has_not_direct_path(self, src, dst):
        if self.not_direct_path.has_key(src):
            dst_list = self.not_direct_path[src]
            if dst in dst_list:
                return True
        return False

    def add_not_direct_path(self, src, dst):
        if self.not_direct_path.has_key(src):
            self.not_direct_path[src] += [dst]
        else:
            self.not_direct_path[src] = [dst]

    def set_level_list(self, level_list):
        self.level_list = level_list

    def to_dot(self):
        dot = Digraph(comment=self.title, format='png')
        for node in self.node_list:
            dot.node(node.code, **node.to_dot_desc())
        for src, dst_list in self.graph.iteritems():
            if src.code == 'A':
                print src.time_offset_ms
            for dst in dst_list:
                dot.edge(src.code, dst.code)

        for level in self.level_list:
            subgraph = Digraph()
            for node in level:
                subgraph.node(node.code)
            subgraph.attr('graph', rank='same')
            dot.subgraph(subgraph)
        dot.render('%s' % self.title, view=False, cleanup=True)

    def remove_all_output_edge(self, node):
        if self.graph.has_key(node):
            self.graph.pop(node)


def is_title(trace_line):
    if len(trace_line[0]) != 0 and \
                    sum([len(x) for x in trace_line[1:]]) == 0:
        return True
    return False


def is_nonsense(trace_line):
    if sum([len(x) for x in trace_line]) == 0:
        return True
    if trace_line[0] == 'Time':
        return True
    return False


def remove_unwanted_edge(dag):
    """
    rules:
        1. remove the duplicate edge
        2. remove any out-edge of static files(image, txt)
    :param dag:
    :return:
    """
    pass


def dag_from_node_list(node_list, title, delta=3):
    """
    delta: if the difference time is within delta, we consider it to be the same
    :param node_list:
    :param title:
    :param delta:
    :return:
    """
    # set a code for all node
    print len(node_list)
    code = 0
    for node in node_list:
        code_name = ''
        if code <= 26:
            code_name = chr(code + ord('A'))
        else:
            code_name = chr(code / 26 - 1 + ord('A')) + chr(code % 26 -1 + ord('A'))
        node.set_code(code_name)
        code += 1

    # sort the node according to time
    node_list.sort(key=lambda x: x.start_time)
    for node in node_list:
        node.time_offset_ms = int((node.start_time - node_list[0].start_time).total_seconds() * 1000)

    # split the trace into levels
    level_list = []
    current_level = [node_list[0]]
    for node in node_list[1:]:
        if node.time_offset_ms - current_level[-1].time_offset_ms < delta:
            current_level.append(node)
        else:
            new_level = [node]
            level_list.append(current_level)
            current_level = new_level
    level_list.append(current_level)

    # construct a fully-connected graph based on the levels
    dag = TraceDAG(title=title, node_list=node_list)
    n = len(level_list)
    for i in range(0, n):
        for j in range(i + 1, n):
            src_level = level_list[i]
            dst_level = level_list[j]
            node_pair_list = [(x, y) for x in src_level for y in dst_level]
            for node_pair in node_pair_list:
                src_node = node_pair[0]
                dst_node = node_pair[1]
                if not src_node.is_static_file():
                    dag.add_edge(src=src_node, dst=dst_node)
                    # 1. for all node that has an output edge to src node now has a not-direct-path to dst node
                    if i > 0:
                        pre_node_list = [item for sublist in level_list[0:i] for item in sublist]
                        for node in pre_node_list:
                            if dag.has_edge(node, src_node):
                                dag.add_not_direct_path(node, dst_node)
                    # 2. for all node that has a not-direct-path to src node now has a not-direct-path to dst node
                    if i > 1:
                        pre_node_list = [item for sublist in level_list[0:i - 1] for item in sublist]
                        for node in pre_node_list:
                            if dag.has_not_direct_path(node, src_node):
                                dag.add_not_direct_path(node, dst_node)

    dag.set_level_list(level_list)

    # remove all output edge of static files
    # for node in node_list:
    #     if node.is_static_file():
    #         dag.remove_all_output_edge(node)
    # remove

    # remove duplicate edge
    for i, src_level in enumerate(level_list[:-2]):  # iterate all levels
        for src_node in src_level:  # iterate all node in the level
            for dst_level in level_list[i + 2:]:
                for dst_node in dst_level:
                    if dag.has_edge(src_node, dst_node):
                        if dag.has_not_direct_path(src_node, dst_node):
                            dag.remove_edge(src_node, dst_node)
    return dag


def parse_web_lbr(file_path):
    """Parse the file generated by lbr of web page, in csv format"""
    dag_list = []  # list of generated DAG
    current_node_list = []
    current_title = ''
    with open(file_path, 'rb') as fin:
        trace_reader = csv.reader(fin, dialect='excel')
        for trace_line in trace_reader:
            if is_title(trace_line):
                if current_node_list:
                    current_trace = dag_from_node_list(current_node_list, current_title)
                    dag_list.append(current_trace)
                    current_node_list = []
                    print current_title
                current_title = trace_line[0]
                continue
            if is_nonsense(trace_line):
                continue
            time, req, size, analysis, total_time = trace_line
            if not req.startswith('GET'):
                continue
            if not size.isdigit():
                continue
            size = int(size)
            node = TraceNode(start_time=time, size=size, trans_time=total_time, type=analysis.strip()[1:-1])
            current_node_list.append(node)
        current_trace = dag_from_node_list(current_node_list, current_title)
        dag_list.append(current_trace)

    return dag_list


def main():
    file_path = 'data_lbr.csv'
    dag_list = parse_web_lbr(file_path)
    dag = dag_list[1]
    dag.to_dot()


if __name__ == '__main__':
    main()
