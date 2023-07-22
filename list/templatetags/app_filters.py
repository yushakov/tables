from django import template
import re

register = template.Library()

@register.filter
def markup(value):
    return re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", value)
