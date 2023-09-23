## twitter-to-bsky importer

Import some of your Twitter archive into a Bluesky account.

This code is designed to import tweets with specific tags and threads with specific length.
It can not post single tweets without tags or threads.

!
!
!

**This code is highly experimental, not fully tested, not packaged at all.**

**Use at your own risks**
See `Known problems` below for details.


!
!
!

Usage:

```bash
git clone git@github.com:juliengossa/twitter-to-bsky.git
cd twitter-to-bsky
# Get an archive from https://twitter.com/settings/download_your_data
# Unzip the archive to a folder named `twitter-archive` in the same directory as main.py

# Convert animation media into jpeg 
./convert_media.sh

export BSKY_USERNAME="yourname.bsky.social"
export BSKY_PASSWORD="yourpassword"

# First check that the archive is correctly parsed (note the use of \ before #)
python main.py --tags \#yourtag1 \#yourtag2 -- minthreadlength 5
# It should print the number of tweets that include #yourtag1 or #yourtag2, and threads that are at least 5 tweets long

# Then post the archive tweets on bluesky
python main.py --tags \#yourtag1 \#yourtag2 -- minthreadlength 5 --post
# It will ask to press [enter] between two threads.
# It is highly recommended to check continiously on bluesky that everything is ok.
# Whenever you are confident, you can type "AUTO" to stop pausing between posts.
```

Everything is logged in the file `ttb.log`.

### Process recovery

It is highly probable that the process will crash at some point.

Let's consider the following log:
```
# Upload Thread 2468: 166928473288498790
INFO:root:Post bs 166928473288498790
INFO:root:Posted: b'{"uri":"at://did:plc:ido6hzdau32ltop6fdhk7s7/app.bsky.feed.post/3k7yqghsnvf2","cid":"bafyreibojvjboyahuk757y6jvbjipokuzi5yknn2ncbstqdqkug6r7jii"}'
INFO:root:Post bs 166928473498214400
INFO:root:Posted: b'{"uri":"at://did:plc:ido6hzdau32ltop6fdhk7s7/app.bsky.feed.post/3k7yqgjgbkh2","cid":"bafyreibdgszibvi7eipjyuh5sojh3jux2mqlok6fevner265qoifdqvo3"}'
INFO:root:Post bs 166928473739387289
INFO:root:Posted: b'{"error":"ExpiredToken","message":"Token has expired"}'
[lots of error message]
```

You can recover from this situation by bypassing all of the threads and start at
the next one. This is done by using the index of thread in the command line.
The index of thread is found in `# Upload Thread 2468: 166928473288498790`.

```
python main.py --tags \#yourtag1 \#yourtag2 -- minthreadlength 5 --post 2468
```

This will start the process at the thread numer 2469.
However, this will not post the remaining tweets in the thread.

To recover at a tweet in the middle of a thread, you need to add more arguments:

- next tweet to post: `166928473739387289` in the example
- root bluesky post id: `'{"uri":"at://did:plc:ido6hzdau32ltop6fdhk7s7/app.bsky.feed.post/3k7yqghsnvf2","cid":"bafyreibojvjboyahuk757y6jvbjipokuzi5yknn2ncbstqdqkug6r7jii"}'` in the example
- parent bluesky post id: `'{"uri":"at://did:plc:ido6hzdau32ltop6fdhk7s7/app.bsky.feed.post/3k7yqgjgbkh2l","cid":"bafyreibdgszibvi7eipjyuh5sojh3jux2mqlok6fevner265qoifdqvo3"}'` in the example

```
python main.py --tags \#yourtag1 \#yourtag2 -- minthreadlength 5 --post 2468 166928473288498790 '{"uri":"at://did:plc:ido6hzdau32ltop6fdhk7s7/app.bsky.feed.post/3k7yqghsnvf2","cid":"bafyreibojvjboyahuk757y6jvbjipokuzi5yknn2ncbstqdqkug6r7jii"}' '{"uri":"at://did:plc:ido6hzdau32ltop6fdhk7s7/app.bsky.feed.post/3k7yqgjgbkh2","cid":"bafyreibdgszibvi7eipjyuh5sojh3jux2mqlok6fevner265qoifdqvo3"}'
```

It will try to resume the process exactly where it failed.

### Known problems

- Whenever the target tags are used in middle of a thread, tweets might be posted multiple times.
- ALT text for media are not supported.

### Thanks to

- Ian Klatzco

### See also

- https://github.com/ianklatzco/twitter-to-bsky
- https://github.com/ianklatzco/atprototools
