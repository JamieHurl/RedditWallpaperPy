import ctypes
import requests
import random
import os
import time
import logging
import json
from os.path import exists


cwd = os.getcwd() + "\\"
settings_file = "Settings.json"
if not exists(settings_file):
    new_file = open(settings_file, "w")
    new_file.write('{\n"subreddits": [\n"wallpaper",\n"wallpapers"\n],\n"resolutions": [\n"1920x1080",\n"2560x1440",\n"3840x2160"\n],\n"recent_wallpapers": [\n]\n}')
    new_file.close()
if not exists("info.log"):
    info_file = open("info.log", "w")
    info_file.close()

with open(settings_file, "r") as f:
    data = f.read()
    settings = json.loads(data)
logging.basicConfig(filename="info.log", filemode="a", format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def main():
    posts = search_reddit()
    random_post = posts[random.randint(0, len(posts)-1)] # pick random post from list returned from reddit
    while random_post["url"] in settings["recent_wallpapers"]: # if random post is one of last 10 used wallpapers, pick another
        logging.info(f"Image is in recent wallpapers. Searching for a new one. {random_post['url']} - {random_post['title']}")
        random_post = posts[random.randint(0, len(posts) - 1)]
    set_wallpaper_from_url(random_post["url"])
    settings["recent_wallpapers"].append(random_post["url"]) # add wallpaper to recent wallpapers
    if len(settings["recent_wallpapers"]) >= 11:
        settings["recent_wallpapers"] = settings["recent_wallpapers"][1:] # remove oldest "recent" wallpaper from recent list
    write_json(settings["recent_wallpapers"], settings_file) # re-save to settings json file
    logging.info(f"Image downloaded & set: {random_post['url']} - {random_post['title']}")


def set_wallpaper_local(path):
    ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 0)


def set_wallpaper_from_url(url): #downloads image, sets wallpaper, deletes image
    picture_path = download_image(url)
    ctypes.windll.user32.SystemParametersInfoW(20, 0, picture_path, 0)
    time.sleep(5)
    os.remove(picture_path)


def download_image(url):
    filename = url.split("/")[-1] # get filename from url
    logging.info(f"Trying to download image {filename}")
    with open(filename, "wb") as x:
        x.write(requests.get(url).content)
    logging.info(f"Downloaded image {filename}")
    return cwd+filename


def get_subreddits(): # gets subreddit list from json file, creates string using formatting required for reddit url
    subreddits = settings["subreddits"]
    srlist = ""
    for sr in subreddits:
        srlist += sr + "+"
    return srlist[:-1]


def write_json(input_data, output_file): #re-writes settings file with updated recent wallpaper list after new one has been set
    with open(output_file, "r") as file:
        file_data = json.load(file)
        file_data["recent_wallpapers"] = input_data
    with open(output_file, "w") as file:
        json.dump(file_data, file, indent=4)


def search_reddit():
    img_exts = ["JPG", "JPEG", "PNG"]
    url = f"https://www.reddit.com/r/{get_subreddits()}/search.json?limit=30&t=month&q={' OR '.join(settings['resolutions'])}&restrict_sr=on"
    logging.info(f"Searched the following subreddits:\n {get_subreddits()}\n for the following resolutions:\n {settings['resolutions']}")
    reddit_json = requests.get(url, headers={'User-agent': 'yourbot'}).json()['data']['children']
    posts = []
    for post in reddit_json:
        if post['data']['url'].split(".")[-1].upper() in img_exts: # only add post to list if file type is one of the image extensions specified
            posts.append(post['data'])
    return posts


if __name__ == '__main__':
    main()
