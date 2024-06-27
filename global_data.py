# module for storing global program data

entry_point = {}
module = {}
bp = {}
cn_flex = {}


def flush():
    """remove all datas"""
    global entry_point, module, bp, cn_flex
    entry_point = {}
    module = {}
    bp = {}
    cn_flex = {}
