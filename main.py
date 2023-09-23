import json, datetime, time, os
import atprotocol as atpt
import twitterarchive
import requests
import re
import logging
import argparse
import sys

# import sys; sys.path = ['/home/user/atprototools'] + sys.path # dev hack to import the local

TWEETS_ARCHIVE_PATH = "./twitter-archive/"
TWEETS_JS_PATH = TWEETS_ARCHIVE_PATH+"data/tweets.js"
TWEETS_MEDIA_PATH = TWEETS_ARCHIVE_PATH+"data/tweets_media/"

USERNAME = os.environ.get("BSKY_USERNAME")
PASSWORD = os.environ.get("BSKY_PASSWORD")

logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("ttb.log"),
        logging.StreamHandler(sys.stdout)
    ])

bs = None

def get_text_facet(text,string,url):
    start=bytes(text,'utf-8').find(bytes(string,'utf-8'))
    end = start + len(string)
    return {
        'index':{'byteStart': start,'byteEnd': end},
        'features': [{'$type': "app.bsky.richtext.facet#link", 'uri': url}]}


def post_tweet_on_bs(tweet, reply_to = None):
    logging.info("Post bs "+tweet['id'])

    facets = []
    cardurl = None
    text = tweet.get("full_text")
    text = re.sub("^(@[^ ]* )*","",text) # Remove replay_ti

    if 'media' in tweet['entities']:
        for media in tweet['entities']['media']:
            text = text.replace(media['url'],"")

    if 'urls' in tweet['entities'] and len(tweet['entities']['urls']) > 0:
        cardurl = tweet['entities']['urls'][-1]['expanded_url']
        text = text.replace(tweet['entities']['urls'][-1]['url'],"")
        for url in tweet['entities']['urls'][:-1]:
            text = text.replace(url['url'],url['display_url'])
        for url in tweet['entities']['urls'][:-1]:
            facets.append(get_text_facet(text, url['display_url'], url['expanded_url']))

    handlers = re.findall("@[a-zA-Z0-9_)]*",text)
    for handler in handlers:
        facets.append(get_text_facet(text, handler, "https://twitter.com/"+handler))

    date_string = tweet.get("created_at")
    date_format = "%a %b %d %H:%M:%S %z %Y"
    parsed_date = datetime.datetime.strptime(date_string, date_format)
    assert(str(type(parsed_date)) == "<class 'datetime.datetime'>")

    image_path = []
    if 'extended_entities' in tweet:
        for media in tweet['extended_entities']['media']:
            media_path = TWEETS_MEDIA_PATH+tweet['id']+"-"+os.path.basename(media['media_url'])
            if os.path.isfile(media_path):
                image_path.append(media_path)

    # print(text)
    # print(image_path)
    # print(facets)
    # print(cardurl)
    return None

    waittime = 1
    complete = False
    while not complete:
        try:
            resp = bs.postPost(text, image_path, parsed_date, reply_to, facets, cardurl)
            complete = True
        except requests.exceptions.ReadTimeout:
            logging.warning("Upload blob timeout... waiting {} seconds".format(waittime))
            time.sleep(waittime)
            #waittime = 2 * waittime

    logging.info("Posted: "+str(resp.content))
    return resp


def post_thread_on_bs(twdict, first_tweet_id, root_id=None, parent_id=None):

    # print(first_tweet_id)
    # print(root_id)
    # print(parent_id)
    # return None

    tweet = twdict[first_tweet_id]
    if not root_id:
        resp = post_tweet_on_bs(tweet)
        resp.raise_for_status()
        parent_id = json.loads(resp.content)
        root_id = parent_id
    else:
        resp = post_tweet_on_bs(tweet, {'root':root_id,'parent':parent_id})
        resp.raise_for_status()
        parent_id = json.loads(resp.content)

    while('next_id' in tweet):
        tweet = twdict[tweet['next_id']]
        resp = post_tweet_on_bs(tweet, {'root':root_id,'parent':parent_id})
        resp.raise_for_status()
        parent_id = json.loads(resp.content)
        time.sleep(.1)


# def get_skoot_text_from_feed(skoot):
#     return skoot.get('feed')[0].get('post').get('record').get('text')
#
# def wipe_profile():
#     testpost_question_mark = atpt.get_latest_skoot(USERNAME)
#     text = testpost_question_mark.json().get('feed')[0].get('post').get('record').get('text')
#
#     while (text != "testpoast"):
#         skoot = atpt.get_latest_skoot(USERNAME).json()
#         text = get_skoot_text_from_feed(skoot)
#         if (text == "testpoast"): continue
#         rkey = skoot.get('feed')[0].get('post').get('uri').split('/')[-1]
#         print("attempting to delete {}".format(text))
#         resp = atpt.delete_skoot(atpt.DID, rkey)
#         print(resp)
#         # import pdb; pdb.set_trace()




def main():

    parser = argparse.ArgumentParser(
                    prog='twitter-to-bsky',
                    description='Post twitter data on bluesky',
                    epilog='')

    parser.add_argument("--post", action="store_true", help='post archive on bluesky')
    parser.add_argument("--tags", nargs='+', default=[], help='post only tweets with hastags')
    parser.add_argument("--minthreadlength", nargs=1, default=[5], type =int, help='post only thread with minimum length')
    parser.add_argument("first_thread_index", type=int, default=-1, nargs="?", help='number of threads to ignore')
    parser.add_argument("first_tweet_id", default=None, nargs="?", help='id of the first tweet to post')
    parser.add_argument("root_id", default=None, nargs="?", help='root_id on bluesky')
    parser.add_argument("parent_id", default=None, nargs="?", help='parent_id on bluesky')


    args = parser.parse_args()

    if args.first_tweet_id and ( not args.root_id or not args.parent_id):
        raise ValueError("root_id and parent_id must be set when using first_tweet_id")

    #warning()
    logging.info("Parse archive")
    twdict = twitterarchive.get_twdict()
    logging.info("{} tweets in archive".format(len(twdict)))
    threads = twitterarchive.get_threads(twdict, args.minthreadlength[0], args.tags)
    logging.info("{} threads in archive, for {} tweets, will be posted".format(len(threads), sum([tweet['thread_length'] for tweet in threads])))

    # post_thread_on_bs(twdict,threads[3])

    if args.post:

        logging.info("Open bluesky session")
        bs = atpt.Session(USERNAME, PASSWORD)
        logging.info("Sessions remainings:" + bs.RateLimitRemaining)

        if args.first_tweet_id:
            first_tweet_id = args.first_tweet_id
            root_id = json.loads(args.root_id)
            parent_id = json.loads(args.parent_id)
            logging.info("\n# Continue Thread "+str(args.first_thread_index)+": "+first_tweet_id)
            post_thread_on_bs(twdict,first_tweet_id,root_id,parent_id)

        auto = False
        for i,thread in enumerate(threads):
            if i<=args.first_thread_index : continue
            logging.info("\n# Upload Thread "+str(i)+": "+thread['id'])
            post_thread_on_bs(twdict,thread['id'])
            root_id=None
            parent_id=None
            if auto:
                time.sleep(5)
            else:
                logging.info("# Thread uploaded: "+str(i)+": "+thread['id'])
                mode = input("Type 'AUTO' to switch to auto mode or press [ENTER] to continue: ")
                auto = ( mode == "AUTO" )

main()
