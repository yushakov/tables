from django import template
import re

register = template.Library()

@register.filter
def markup(value):
    out = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", value)
    out = re.sub(r"&amp;", r"&", out)
    return out
