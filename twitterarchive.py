import json, datetime, time, os
from operator import itemgetter, attrgetter
import logging

TWEETS_JS_PATH = "./twitter-archive/data/tweets.js"

f = open(TWEETS_JS_PATH)
c = f.read().replace("window.YTD.tweets.part0 = ", "")
tweets = json.loads(c)

def get_twdict(uid = "JulienGossa"):
    twdict = {}

    for index, tweet in enumerate(tweets):
        tweet = tweet.get("tweet")
        tweet['thread_length'] = 0
        twdict[tweet['id']] = tweet

    for twid in sorted(twdict):
        tweet = twdict[twid]
        #print("test")
        # First tweet
        if 'in_reply_to_screen_name' not in tweet:
            #print("first")
            tweet['thread_root_id'] = tweet['id']
            twdict[tweet['id']] = tweet
        # Reply
        elif tweet['in_reply_to_screen_name'] == uid:
            try:
                twpred = twdict[tweet['in_reply_to_status_id']]
            except KeyError as e:
                logging.warning("{}: Tweet {} not in archive".format(tweet['id'], tweet['in_reply_to_status_id']))
                continue

            try:
                tri = twpred['thread_root_id']
            except KeyError as e:
                #print("{}: Root of {} not defined".format(tweet['id'], twpred['id']))
                # not a thread
                continue

            tweet['thread_root_id'] = tri
            tweet['thread_length'] = -1

            if 'next_id' not in twpred:
                twdict[tri]['thread_length'] += 1
                #print(twdict[tri]['thread_length'])
                twpred['next_id'] = tweet['id']

            twdict[tweet['id']] = tweet

    return twdict

def get_threads(twdict, min_length = 5, tags = [ "#VeilleESR" ]):
    threads = []
    for twid in sorted(twdict):
        tweet = twdict[twid]
        if tweet['thread_length'] >= min_length or any(tag in tweet['full_text'] for tag in tags):
            threads.append(tweet)

    return threads

if __name__ == "__main__":
    twdict = get_twdict()
    threads = get_threads(twdict)

    for tweet in threads:
        print("https://twitter.com/JulienGossa/status/"+tweet['id'])

    print(len(threads))
    print(sum([tweet['thread_length'] for tweet in threads]))
    print(threads[0])
