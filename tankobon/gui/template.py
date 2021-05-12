# coding: utf8
"""This template generates the HTML view for a manga."""

import string
import re

from ..core import Metadata

RE_CSS_STYLE = re.compile(r"(\#?\w+) {(.*?)}", flags=re.DOTALL)

RE_TAG = re.compile(r"<(\w+)(.*?)>")
RE_TAG_ATTR = re.compile(r"(\w+)=\"(.*?)\"")

_CSS = """
table {
    bgcolor:#f8f9fa;
    border:#a2a9b1;
}

#header {
    align:center;
    colspan:2;
    padding:5px;
}
"""

_TEMPLATE = """
<h2>Description</h2>
$desc

<table align="right" float="right" width="auto">

    <tr>
        <td id="header" bgcolor="#CCF"><h2><i>$title</i></h2></td>
    </tr>

    <tr>
        <td><img src="image://cover"/></td>
    </tr>

    <tr>
        <td id="header" bgcolor="#DDF">$alt_titles</td>
    </tr>

    <tr>
        <td><b>Genre</b></td>
        <td>$genres</td>
    </tr>

    <tr>
        <td id="header" bgcolor="#CCF"><b>Manga</b></td>
    </tr>

    <tr>
        <td><b>Authored by</b></td>
        <td>$authors</td>
    </tr>

</table>
"""


def _safe_join(iterator, delimiter=", ", repl="(empty)", norm=True):
    if iterator is None:
        return repl

    if norm:
        iterator = (s.replace("_", " ").capitalize() for s in iterator)

    return delimiter.join(iterator)


def parse_css(css: str) -> dict:
    css_map = {}

    for match in RE_CSS_STYLE.finditer(css):
        tag = match.group(1)
        style = {}

        for attr in match.group(2).split(";"):
            attr = attr.strip()

            if attr:
                name, _, value = attr.partition(":")
                style[name] = value

        css_map[tag] = style

    return css_map


class CSSTemplate(string.Template):
    def __init__(self, template: str, css: str):
        self.css = parse_css(css)

        template = RE_TAG.sub(self._replace, template)

        super().__init__(template)

    def _replace(self, match: re.Match):
        tag = match.group(1)
        _attrs = match.group(2)

        attrs = {m.group(1): m.group(2) for m in RE_TAG_ATTR.finditer(_attrs)}

        if tag in self.css:
            # direct tag selector
            css_attrs = self.css[tag]
        elif "id" in attrs:
            # id attribute selector
            css_attrs = self.css[f"#{attrs['id']}"]
        else:
            css_attrs = None

        if css_attrs is not None:
            attrs.update(css_attrs)

        attrs_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return f"<{tag} {attrs_str}>"


TEMPLATE = CSSTemplate(_TEMPLATE, _CSS)


def create_html(meta: Metadata):
    return TEMPLATE.substitute(
        title=meta.title,
        alt_titles=_safe_join(meta.alt_titles, delimiter="<br>"),
        genres=_safe_join(meta.genres, norm=True),
        authors=_safe_join(meta.authors),
        desc=meta.desc,
    )
