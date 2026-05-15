#!/bin/sh
find /log/ -type f -mtime +30 -exec rm {} +