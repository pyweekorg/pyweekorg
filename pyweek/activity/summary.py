from html import escape
from html.parser import HTMLParser
from io import StringIO


class Summarizer(HTMLParser):
    self_closing = {'br', 'img', 'hr'}

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
        assert isinstance(tag, str)
        if tag not in self.self_closing:
            self.stack.append(tag)
        attrtext = ' '.join(
            (
                f'{escape(k)}="{escape(v)}"'
                if v is not None else escape(k)
            ) for k, v in attrs
        )
        self.out.write(
            f'<{tag} {attrtext}>'
        )

    def handle_endtag(self, tag):
        if self.done:
            return
        self.out.write(f'</{escape(tag)}>')
        if tag in self.stack:
            self.stack.remove(tag)

    def finish(self):
        while self.stack:
            tag = self.stack.pop()
            self.out.write(f'</{escape(tag)}>')
        self.done = True

    def handle_data(self, data):
        if self.done:
            return
        assert isinstance(data, str)
        words = data.split()
        take = []
        if data[:1].isspace():
            take.append('')
        for w in words:
            if self.chars + len(w) > self.maxchars:
                self.out.write(' '.join(take) + '...')
                self.finish()
                return
            take.append(w)
            self.chars += len(w)
        if data[-1:].isspace():
            take.append('')
        self.out.write(' '.join(take))



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
