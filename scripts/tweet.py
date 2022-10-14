
import os
import re
import sys

import yaml
from twython import Twython

from utils import REPO_FOLDER


dir_path = os.path.dirname(os.path.realpath(__file__))
SINGLE_TWEET = os.path.join(dir_path, "tweet_templates", "single.txt")
MULTI_TWEET = os.path.join(dir_path, "tweet_templates", "multi.txt")

# read the Twitter authentication tokens
APP_KEY = os.environ.get("TW_APP_KEY")
APP_SECRET = os.environ.get("TW_APP_SECRET")
OAUTH_TOKEN = os.environ.get("TW_OAUTH_TOKEN")
OAUTH_TOKEN_SECRET = os.environ.get("TW_OAUTH_TOKEN_SECRET")


def tweet(text: str):
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    twitter.update_status(status=text)


def _combine_dicts(dicts):
    combined = {}
    for d in dicts:
        for key in d:
            if d[key]:
                if key in combined:
                    combined[key].append(d[key])
                else:
                    combined[key] = [d[key]]
    return combined


def _create_explore_url(file):
    path_split = os.path.normpath(file).split(os.sep)
    org, name = path_split[-2], path_split[-1].split(".")[0]
    return f"https://adapterhub.ml/adapters/{org}/{name}/"


def _create_names(tasks, label="task"):
    tasks = list(set(tasks))
    s = label
    if len(tasks) > 1:
        s+= "s"
    s += " "
    s += ", ".join(tasks[:3])
    if len(tasks) > 3:
        s += " and more!"
    return s


def _prep_twitter(handle):
    handle = re.sub(r"https?://twitter\.com/", "", handle)
    if not handle.startswith("@"):
        handle = "@" + handle
    return handle


def create_message(files):
    dicts = []
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            dicts.append(yaml.load(f, Loader=yaml.FullLoader))
    config = _combine_dicts(dicts)
    # tweeting is triggered by given twitter handles
    if len(config["twitter"]) < 1:
        return None
    # add "@" to every twitter handle
    config["twitter"] = " ".join(set(map(lambda s: _prep_twitter(s), config["twitter"])))
    # add new config items
    config["count"] = len(files)
    if "description" in config:
        config["description_trunc"] = [s.split(".")[0] for s in config["description"]]
    else:
        config["description_trunc"] = None
    config["explore_url"] = [_create_explore_url(file) for file in files]
    config["task_names"] = _create_names([t+"/"+st for t,st in zip(config["task"], config["subtask"])])
    config["model_names"] = _create_names([m for m in config["model_name"]], label="model")
    # we have different msgs for the case of one adapter and mult. adapters
    if len(files) == 1 and config["description_trunc"]:
        tweet_file = SINGLE_TWEET
    else:
        tweet_file = MULTI_TWEET
    with open(tweet_file, 'r', encoding='utf-8') as f:
        template = f.read()
    return template.format(**config)


if __name__ == "__main__":
    files = [f for f in sys.argv[1:] if f.startswith(REPO_FOLDER)]
    if len(files) > 0:
        msg = create_message(files)
        print("=== Message to be tweeted ===")
        print(msg)
        print(f"=== len: {len(msg)} ===")
        tweet(msg)
