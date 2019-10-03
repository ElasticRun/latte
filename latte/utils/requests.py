from six import string_types

def json_to_xml(dict_to_convert):
    if isinstance(dict_to_convert, dict):
        return ''.join([f'''
        <{key}>
            {json_to_xml(dict_to_convert[key])}
        </{key}>
        ''' for key in dict_to_convert])
    elif isinstance(dict_to_convert, list):
        return ''.join(str(json_to_xml(row)) for row in dict_to_convert)
    else:
        return str(dict_to_convert)
