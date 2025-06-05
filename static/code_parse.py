from typing import Optional, Type

import tree_sitter_java as  tsjava
from tree_sitter import Language, Parser
from graphviz import Digraph
from collections import deque

from static.code_match import ProgramCode


def ast_bfs_with_call_graph(root):
    """
    Traverses an AST Tree using BFS to build a simplified call graph
    starting from the first 'method_declaration' node.
    Removes 'System' nodes and their related edges.

    :param root: The root node of the AST.
    :return: A tuple of two lists:
            - node_list: A list of tuples (node_id, node_str).
            - edge_list: A list of tuples (caller_id, callee_id).
    """
    node_list = []  # node_list: [(node_id, node_str), ...]
    edge_list = []  # edge_list: [(caller_id, callee_id), ...]
    node_id_map = {}  # Map for node IDs
    node_counter = 0
    recording_started = False  # Flag to indicate recording

    # Queue for BFS
    queue = deque([(root, None)])  # Tuple (Node<> node, int parent_id)

    # BFS
    while queue:
        (node, parent_id) = queue.popleft()

        if not node.is_named:
            continue

        node_type = str(node.type).strip()
        node_text = str(node.text.decode())
        current_node_id = node_id_map.get(node_text)

        # Check for the first 'method_declaration' node
        if node_type == "method_declaration":
            recording_started = True

        # If recording has started, add the node
        if recording_started:
            # Add node if it doesn't exist
            if current_node_id is None:
                current_node_id = f"node_{node_counter}"
                node_list.append((current_node_id, node_text, node.type))
                node_id_map[node_text] = current_node_id
                node_counter += 1

            # Add edge if there is a parent
            if parent_id is not None:
                edge_list.append((parent_id, current_node_id))

        # Enqueue child nodes
        for child in node.children:
            queue.append((child, current_node_id))  # Pass current node ID
    return node_list, edge_list

def get_call_graph(root_node, program_code: Type[ProgramCode]):
    data_flow_graph = {}
    stack = [(root_node, None)]

    # as different languages have different definition names and call name
    # code should get name from ast_call_type_map.
    while stack:
        node, current_function = stack.pop()
        if not node.is_named:
            continue

        # 处理函数定义
        if node.type == "method_declaration":
            function_name = node.child_by_field_name('name').text.decode('utf8')
            data_flow_graph[function_name] = {'definitions': [], 'uses': []}
            current_function = function_name

        # 处理变量定义
        elif node.type == "variable_declaration" and current_function:
            variable_name = node.child_by_field_name('name').text.decode('utf8')
            data_flow_graph[current_function]['definitions'].append(variable_name)

        # 处理变量使用
        elif node.type == "identifier" and current_function:
            variable_name = node.text.decode('utf8')  # 直接使用 text
            data_flow_graph[current_function]['uses'].append(variable_name)

        # 添加子节点到栈中
        for child in reversed(node.children):
            stack.append((child, current_function))

    return data_flow_graph

def get_code_ast(node, index=0):
    stack = [(node, 0)]  # Stack to hold nodes along with their indentation level
    output = []  # List to collect the output strings

    while stack:
        current_node, indent = stack.pop()  # Get the current node and its indentation level

        # Check if the node is valid
        if not hasattr(current_node, 'type') or not hasattr(current_node, 'children'):
            output.append('Invalid node')
            continue

        # Append the type of the current node with indentation to the output list
        output.append(str(current_node.type))
        if current_node.type == ";":
            output.append("\n")

        # Push child nodes onto the stack in reverse order to maintain the correct order
        for child in reversed(current_node.children):
            stack.append((child, indent + 1))

    return " ".join(output)  # Join the list into a single string with newlines