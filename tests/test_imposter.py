# coding: utf8

from tankobon import imposter


def test_random():
    ua = imposter.UserAgent()
    print(ua.random())
