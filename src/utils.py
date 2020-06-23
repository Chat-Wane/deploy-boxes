

def _get_address(host, network = None) -> str:
    """Get the IP address of the host.
    Args:
        host: the host.
        network: the network through which access the host.
    Returns:
        A string representing the ip address of the host.
    """
    # This assumes that `discover_network` has been run before
    # otherwise, extra is not set properly
    return host.address if network is None else host.extra[network + "_ip"]
