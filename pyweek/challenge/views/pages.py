import os
import datetime
import xml.sax.saxutils

from PIL import Image

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings
from django.http import Http404

from stripogram import html2text, html2safehtml

def page(request, page_id):
    path = os.path.join(settings.PAGES_DIR, '%s.html'%page_id)
    if not os.path.exists(path):
        raise Http404('No file called %s'%page_id)
    content = open(path, 'r').read()
    return render_to_response('page.html',
        dict(content=content), context_instance=RequestContext(request))

