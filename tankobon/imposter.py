# coding: utf8

"""Imposter fakes a user agent to use in requests.
A random user agent is chosen using a weighted statistic, but if stats are unavailable a non-weighted random is chosen.
"""

import json
import pathlib
import random
import tempfile
from typing import Dict, List, Optional

import requests

from . import jsonclasses, utils

STATS_URL = "https://www.w3schools.com/browsers/default.asp"
USERAGENT_URL = "http://useragentstring.com/pages/useragentstring.php?name={browser}"

CACHE_PATH = pathlib.Path(tempfile.gettempdir()) / "imposter.json"


def _stats():
    soup = utils.soup(STATS_URL)

    table = soup.select("table[class='ws-table-all notranslate'] > tbody > tr")

    browsers = [t.text.lower() for t in table[0].select("th[class='right'] > a")]
    stats = [
        float(t.text.replace(" %", "")) / 100
        for t in table[1].select("td[class='right']")
    ]

    return dict(zip(browsers, stats))


def _user_agents(browser):
    soup = utils.soup(USERAGENT_URL.format(browser=browser))

    user_agents = soup.select("div[id='liste'] > ul > li > a")

    return [ua.text for ua in user_agents]


@jsonclasses.dataclass
class UserAgent:
    """An interface to get a randomised user agent.

    Attributes:
        browsers: A map of browser name to the possible user agent strings for that browser.
        stats: A map of browser name to its vistor statistics retreived from W3Schools.
    """

    browsers: Dict[str, List[str]] = jsonclasses.field(default_factory=dict)
    stats: Dict[str, float] = jsonclasses.field(default_factory=dict)

    def random(self, browser: Optional[str] = None, weighted: bool = True) -> str:
        """Get a randomised user agent.

        Args:
            browser: The browser to limit the user agent to.
            weighted: Whether or not to get a random browser by weighted statistic.
                If false, a non-weighted random choice is made.

        Returns:
            The random user agent, as a string.
        """
        if not browser:
            if not self.stats:
                self.stats = _stats()

            browsers = list(self.stats.keys())
            stats = list(self.stats.values())

            if weighted:
                browser = random.choices(browsers, weights=stats)[0]
            else:
                browser = random.choice(browsers)

        if browser not in self.browsers:
            self.browsers[browser] = _user_agents(browser)

        return random.choice(self.browsers[browser])

    def cache(self):
        """Save the downloaded user agent data to disk."""
        with open(CACHE_PATH, "w") as f:
            json.dump(self, f)


def cached() -> UserAgent:
    """Load the cached user agent data from disk."""
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return UserAgent()


class UserSession(requests.Session):
    """requests.Session with randomised user agent in the headers."""

    ua = cached()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.headers.update({"User-Agent": self.ua.random()})
        self.ua.cache()
