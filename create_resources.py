#!/usr/bin/python
# coding: utf8

import pathlib
import subprocess
import tempfile

QRC_TEMPLATE = """
<!DOCTYPE RCC><RCC version="1.0">
<qresource>
{files}
</qresource>
</RCC>
"""

CURDIR = pathlib.Path(__file__).parent
COMPILER = "pyside6-rcc"
RESOURCES = CURDIR / "resources"
DESTINATION = CURDIR / "tankobon" / "ui" / "resources.py"


def create_qrc():
    return QRC_TEMPLATE.format(
        files="\n".join(
            f'<file alias="{file.name}">{str(file)}</file>'
            for file in RESOURCES.glob("*")
            if not file.name.startswith(".")
        )
    ).strip()


def compile_qrc(path_to_qrc, dest):
    subprocess.run([COMPILER, path_to_qrc, "-o", dest], check=True)


if __name__ == "__main__":
    with tempfile.NamedTemporaryFile(suffix=".rc", delete=False) as f:
        f.write(create_qrc().encode("utf8"))
        f.seek(0)

        filename = f.name

    # On Windows, the tempfile cannot be left open while running a command on the file.
    # So we compile first and then remove the tempfile manually later.
    compile_qrc(filename, str(DESTINATION))
    pathlib.Path(filename).unlink()
