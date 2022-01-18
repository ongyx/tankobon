#!/usr/bin/bash
pydoc-markdown \
  -m tankobon.core \
  -m tankobon.exceptions \
  -m tankobon.iso639 \
  -m tankobon.models \
  -m tankobon.utils \
  -m tankobon.imposter \
  -m tankobon.sources.base \
  --render-toc > API.md
