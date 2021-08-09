import os
import datetime
import xml.sax.saxutils

from PIL import Image

from django.shortcuts import render
from django.template import RequestContext
from django.conf import settings
from django.http import Http404

from pyweek.bleaching import html2text, html2safehtml

def page(request, page_id):
    path = os.path.join(settings.PAGES_DIR, f'{page_id}.html')
    if not os.path.exists(path):
        raise Http404(f'No file called {page_id}')
    content = open(path).read()
    return render(request, 'page.html', {'content': content})

