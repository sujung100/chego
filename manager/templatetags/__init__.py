from django import template

register = template.Library()

from .manager_filters import *