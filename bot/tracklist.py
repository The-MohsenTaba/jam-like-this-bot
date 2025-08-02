""" some text cleaner functions for better api search performance """

def get_track_list(string:str):
    """ export musict to a list """

    track_list= string.split('\n')
    return track_list

def ft_remover(obj:str):
    """ removes any type of featuring mentions in songs """
    
    if obj.__contains__('feat'):
        obj = obj.replace(obj[obj.index('feat')-1:],'')
    if obj.__contains__(' ft'):
        obj = obj.replace(obj[obj.index('ft')-1:],'')
    if obj.__contains__('(ft'):
        obj = obj.replace(obj[obj.index('ft')-1:],'')
    return obj
