#coding=utf-8

def build_request(method, args, kwargs):
    """
    Returns a JSON-RPC-Dictionary for a method
    """
    if kwargs:
        params = kwargs
        if args:
            params['__args'] = args
    else:
        params = args
    data = {
        'id': next(IDGenerator()),
        'method': method,
        'params': params,
    }

    return data

#def parse_request(req):
#    pass
def parse_request_args(params):
    positional_params = []
    named_params = {}
    if isinstance(params, list):
        positional_params = params
    elif isinstance(params, dict):
        positional_params = params.get("__args", [])
        if positional_params:
            del params["__args"]
        named_params = params
    return positional_params, named_params

def build_response(result, id, error=None):
    r = {'id': id, 'result': result}
    if error:
        r.pop('result', None)
        r['error'] = error.to_dict()

    return r

#def parse_response(packed_str):
#    pass

def IDGenerator():
    """
    Message ID Generator.

    NOTE: Don't use in multithread. If you want use this
    in multithreaded application, use lock.
    """
    counter = 0
    while True:
        yield counter
        counter += 1
        if counter > (1 << 30):
            counter = 0
