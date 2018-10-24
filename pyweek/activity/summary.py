from cgi import escape
from HTMLParser import HTMLParser
from io import StringIO


class Summarizer(HTMLParser):
    self_closing = {u'br', u'img', u'hr'}

    def __init__(self, maxchars=280):
        HTMLParser.__init__(self)
        self.stack = []
        self.maxchars = maxchars
        self.chars = 0
        self.done = False
        self.out = StringIO()

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        assert isinstance(tag, unicode)
        if tag not in self.self_closing:
            self.stack.append(tag)
        attrtext = u' '.join(
            (
                u'{}="{}"'.format(escape(k), escape(v))
                if v is not None else escape(k)
            ) for k, v in attrs
        )
        self.out.write(
            u'<{} {}>'.format(tag, attrtext)
        )

    def handle_endtag(self, tag):
        if self.done:
            return
        self.out.write(u'</{}>'.format(escape(tag)))
        if tag in self.stack:
            self.stack.remove(tag)

    def finish(self):
        while self.stack:
            tag = self.stack.pop()
            self.out.write(u'</{}>'.format(escape(tag)))
        self.done = True

    def handle_data(self, data):
        if self.done:
            return
        assert isinstance(data, unicode)
        words = data.split()
        take = []
        if data[:1].isspace():
            take.append(b'')
        for w in words:
            if self.chars + len(w) > self.maxchars:
                self.out.write(u' '.join(take) + u'...')
                self.finish()
                return
            take.append(w)
            self.chars += len(w)
        if data[-1:].isspace():
            take.append(b'')
        self.out.write(b' '.join(take))



def summarise(html, maxchars=280):
    """Take the first maxchars characters of the given HTML.

    Return a tuple (short_html, was_truncated).

    """
    p = Summarizer(maxchars)
    p.feed(html)
    p.close()
    truncated = p.done
    p.finish()
    return p.out.getvalue(), truncated
