# module for storing global program data

entry_point = {}
module = {}
bp = {}
cn_flex = {}
cn_nodes=[]


def flush():
    """remove all datas"""
    global entry_point, module, bp, cn_flex, cn_nodes
    entry_point = {}
    module = {}
    bp = {}
    cn_flex = {}
    cn_nodes = []
