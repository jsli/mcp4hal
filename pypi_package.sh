#!/bin/sh

rm -rf src/mcp4hal.egg-info
rm -rf build
rm -rf dist

uv build
