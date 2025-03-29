import brian2 as b2

def rebuild_neurongroup(neurongroup_dict, namespace=None):
    """
    Recreate a NeuronGroup from its exported dictionary representation.
    
    Parameters
    ----------
    neurongroup_dict : dict
        Dictionary containing NeuronGroup export information.
    namespace : dict, optional
        Namespace for resolving variables and initial conditions.
    
    Returns
    -------
    brian2.NeuronGroup
    """
    namespace = namespace or {}
    
    equation_str = "\n".join(
        f"d{var}/dt = {details['expr']} : {details['unit']}"
        if details.get("type") == "differential"
        else f"{var} : {details['unit']}"
        for var, details in neurongroup_dict.get("equations", {}).items()
    )
    

    neuron_group = b2.NeuronGroup(
        N=neurongroup_dict.get("N", 0),
        model=equation_str,
        method=neurongroup_dict.get("user_method", "euler"),
        namespace=namespace,
        when=neurongroup_dict.get("when", "start"),
        order=neurongroup_dict.get("order", 0),
        name=neurongroup_dict.get("name", None)
    )
    

    if "threshold" in neurongroup_dict:
        neuron_group.threshold = neurongroup_dict["threshold"]
    if "reset" in neurongroup_dict:
        neuron_group.reset = neurongroup_dict["reset"]
    

    if "events" in neurongroup_dict:
        for event_name, event_info in neurongroup_dict["events"].items():
            if "condition" in event_info:
                setattr(neuron_group, event_name, event_info["condition"])
    

    for init in neurongroup_dict.get("initializers", []):
        var, value = init.get("variable"), init.get("value")
        try:

            resolved_value = eval(value, namespace) if isinstance(value, str) else value
        except Exception as e:
            raise ValueError(f"Failed to evaluate '{value}' in namespace: {e}")
        

        if "index" in init:
            neuron_group.variables[var][init["index"]] = resolved_value
        else:
            neuron_group.variables[var].set_value(resolved_value)
    

    for op in neurongroup_dict.get("run_regularly", []):
        code = op["code"]
        dt = op.get("dt", 1 * b2.ms)
        when = op.get("when", "end")
        order = op.get("order", 0)
        

        neuron_group.run_regularly(code, dt=dt, when=when, order=order)
    

    if "identifiers" in neurongroup_dict:
        for name, value in neurongroup_dict["identifiers"].items():
            if name not in namespace:
                namespace[name] = value
    
    return neuron_group
