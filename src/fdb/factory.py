import importlib

def debug_type(debug_mode, gdb_obj, config):
    module_ = importlib.import_module('src.fdb.debug')
    debug_type = getattr(module_, debug_mode, None)
    assert debug_type is not None, f'{debug_mode} not implemented'
    assert issubclass(debug_type, module_.DebugType), f'{debug_mode} not a DebugType'
    return debug_type(
        gdb_obj=gdb_obj,
        config=config
    )

def seed_comparator(seed_comparator_name, target):
    module_ = importlib.import_module('src.fdb_util')
    seed_cmp = getattr(module_, seed_comparator_name, None)
    assert seed_cmp is not None, f'{seed_comparator_name} not implemented'
    assert issubclass(seed_cmp, module_.SeedComparatorBase), f'{seed_comparator_name} not a SeedComparatorBase'
    return seed_cmp(
        target_seed_path=target
    )
