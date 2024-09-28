from django import template
import json

register = template.Library()

def file_format(value):
    result = ''
    d = json.loads(value)

    result += '<ul>'
    for k in d.keys():
        result += f'<li><a href="{k}">{d[k]}</a></li>'
    result += '</ul>'
    
    return(result)

register.filter('file_format', file_format)
