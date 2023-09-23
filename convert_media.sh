#!/bin/bash

TWITTER_ARCHIVE_PATH=./twitter-archive

for f in ${TWITTER_ARCHIVE_PATH}/data/tweets_media/*.mp4
do
  echo $f
  convert -coalesce -resize 200x -deconstruct ${f}[0] ${f/\.mp4/\.jpg}
done
