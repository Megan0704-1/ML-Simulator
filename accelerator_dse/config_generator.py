def generate_config(array_h, array_w, ifmap_kb, filter_kb, ofmap_kb):
    """Generate a Scale-Sim config file as a string."""
    return f"""
        [general]
        run_name = scale_run_{array_h}x{array_w}_ifmap{ifmap_kb}_filter{filter_kb}_ofmap{ofmap_kb}

        [architecture_presets]
        ArrayHeight:    {array_h}
        ArrayWidth:     {array_w}
        IfmapSramSzkB:  {ifmap_kb}
        FilterSramSzkB: {filter_kb}
        OfmapSramSzkB:  {ofmap_kb}
        IfmapOffset:    0
        FilterOffset:   10000000
        OfmapOffset:    20000000
        Bandwidth:      10
        Dataflow:       ws
        MemoryBanks:    1

        [run_presets]
        InterfaceBandwidth: CALC
        """
