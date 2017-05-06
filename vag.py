import twitter
from functools import reduce
import re
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

OSTEEN_TWEETS_MAX = 200
MAX_PAST_TWEETS = 200
LOOKBACK_DAYS = 2974
LINK_PATTERN = r"/(\S+\.(com|net|org|edu|gov|co)(\/\S+)?)"

# do a regex replace using a dictionary, pretty much from
# http://stackoverflow.com/questions/6116978/python-replace-multiple-strings
def multi_replace(str, find_replace):
    return reduce(lambda a, kv: re.sub(*kv, a), find_replace.items(), str)


# take any block of osteen tweets and our recent tweets,
# determine which, if any, we haven't said and aren't too long
# then return just those texts for us to do tweeting on
def vagify_tweets(osteen_tweets, recent_vag_tweets):
    texts_to_vagify = [tweet.text for tweet in osteen_tweets if
                          'god' in tweet.text.lower()]

    # Transforms:
    #    God  ==>  Your Vag
    #    He   ==>  She
    #    His  ==>  Hers
    #
    # (don't transform lower case because it could be referring to someone else who is not LORD)

    replacements = {r"God(\W)": r"Your Vag\1",
                    r"He(\W)": r"She\1",
                    r"His ": r"Her ",
                    r"His(\W)": r"Hers\1",
                    r"Him(\W)": r"Her\1"
                    }

    vagified_texts = [multi_replace(text, replacements) for text in texts_to_vagify]
    # filter out anything we've already said recently from our vagified texts so we don't repeat ourselves
    # filter out anything that's too long!
    return [text for text in vagified_texts if
            re.sub(LINK_PATTERN, "", text) not in [re.sub(LINK_PATTERN, "", extant.text) for extant in recent_vag_tweets] and
            len(text) < 141]




read_api = twitter.Api(consumer_key=os.environ['READ_CONSUMER_KEY'],
                      consumer_secret=os.environ['READ_CONSUMER_SECRET'],
                      access_token_key=os.environ['READ_ACCESS_TOKEN_KEY'],
                      access_token_secret=os.environ['READ_ACCESS_TOKEN_SECRET'])

#print(read_api.VerifyCredentials())


write_api = twitter.Api(consumer_key=os.environ['WRITE_CONSUMER_KEY'],
                      consumer_secret=os.environ['WRITE_CONSUMER_SECRET'],
                      access_token_key=os.environ['WRITE_ACCESS_TOKEN_KEY'],
                      access_token_secret=os.environ['WRITE_ACCESS_TOKEN_SECRET'])

#print(write_api.VerifyCredentials())


osteen_recent = read_api.GetUserTimeline(screen_name="JoelOsteen", count=OSTEEN_TWEETS_MAX, exclude_replies=True, include_rts=False)
vag_recents = write_api.GetUserTimeline(count=MAX_PAST_TWEETS)


vagified = vagify_tweets(osteen_recent, vag_recents)

if len(vagified):
    target=vagified[-1]
    print(target)
    write_api.PostUpdate(vagified[-1])