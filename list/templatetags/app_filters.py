from django import template
import re

register = template.Library()

@register.filter
def markup(value):
    out = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", value)
    out = re.sub(r"\*(.*?)\*", r"<i>\1</i>", out)
    out = re.sub("\n", r"<br />", out)
    out = re.sub(r"&amp;", r"&", out)
    out = re.sub(r"\[([^\]]+)\]\(([^\s\)]+)\)", r"<a href='\2' target='_blank'>\1</a>", out)
    return out

@register.filter
def strip(value):
    return value.strip()
