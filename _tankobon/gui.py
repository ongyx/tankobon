# coding: utf8
"""Pyglet-based gui. (WARNING: EXPRIMENTAL!)"""

import pyglet

from pyglet_gui.buttons import Button
from pyglet_gui.manager import Manager
from pyglet_gui.theme import Theme

window = pyglet.window.Window(resizable=True, vsync=True)
batch = pyglet.graphics.Batch()


@window.event
def on_draw():
    window.clear()
    batch.draw()


theme = Theme(
    {
        "font": "Lucida Grande",
        "font_size": 12,
        "text_color": [255, 255, 255, 255],
        "gui_color": [255, 0, 0, 255],
        "button": {
            "down": {
                "image": {
                    "source": "button-down.png",
                    "frame": [8, 6, 2, 2],
                    "padding": [18, 18, 8, 6],
                },
                "text_color": [0, 0, 0, 255],
            },
            "up": {
                "image": {
                    "source": "button.png",
                    "frame": [6, 5, 6, 3],
                    "padding": [18, 18, 8, 6],
                }
            },
        },
    },
    resources_path="",
)

button = Button("Hello World", on_press=lambda: print("pressed"))
Manager(button, window=window, theme=theme, batch=batch)

pyglet.app.run()