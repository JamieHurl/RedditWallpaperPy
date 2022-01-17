import ctypes
import random
import os
import time
import logging
import json
from os.path import exists
import requests


def main():
    settings_file = "Settings.json"
    if not exists(settings_file): # create a standard settings file if one does not already exist
        new_file = open(settings_file, "w")
        new_file.write('{\n"subreddits": [\n"wallpaper",\n"wallpapers"\n],\n"resolutions": [\n"1920x1080",\n"2560x1440",\n"3840x2160"\n],\n"recent_wallpapers": [\n]\n}')
        new_file.close()
    if not exists("info.log"): # create a blank log file is one does not already exist
        info_file = open("info.log", "w")
        info_file.close()

    logging.basicConfig(filename="info.log", filemode="a", format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

    settings = read_json(settings_file)
    posts = search_reddit(settings["subreddits"], settings["resolutions"])

    random_post = posts[random.randint(0, len(posts)-1)] # pick random post from list returned from reddit
    while random_post["url"] in settings["recent_wallpapers"]: # if random post is one of last 10 used wallpapers, pick another
        logging.info(f"Image is in recent wallpapers. Searching for a new one. {random_post['url']} - {random_post['title']}")
        random_post = posts[random.randint(0, len(posts) - 1)]

    set_wallpaper_from_url(random_post["url"])
    settings["recent_wallpapers"].append(random_post["url"]) # add wallpaper to recent wallpapers
    if len(settings["recent_wallpapers"]) >= 11:
        settings["recent_wallpapers"] = settings["recent_wallpapers"][1:] # remove oldest "recent" wallpaper from recent list
    write_json(settings, settings_file) # re-save to settings json file

    logging.info(f"Image downloaded & set: {random_post['url']} - {random_post['title']}")


def set_wallpaper_local(path):  # set wallpaper when passed local image file path
    ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 0)


def set_wallpaper_from_url(url): # sets wallpaper when passed a URL, deletes image after set
    picture_path = download_file(url)
    ctypes.windll.user32.SystemParametersInfoW(20, 0, picture_path, 0)
    time.sleep(5)
    os.remove(picture_path)


def download_file(url): # downloads file when passed URL, returns file name
    filename = url.split("/")[-1] # get filename from url
    logging.info(f"Trying to download image {filename}")
    with open(filename, "wb") as x:
        x.write(requests.get(url).content)
    logging.info(f"Downloaded file {filename}")
    return filename


def get_subreddits(subreddits): # gets subreddit list from json file, creates string using formatting required for reddit url
    sr_list = ""
    for sr in subreddits:
        sr_list += sr + "+"
    return sr_list[:-1]


def write_json(file_data, output_file): #re-writes settings file with updated recent wallpaper list after new one has been set
    with open(output_file, "w") as file:
        json.dump(file_data, file, indent=4)


def read_json(file): # returns json data from provided json file
    with open(file, "r") as f:
        data = f.read()
        return json.loads(data)


def search_reddit(subreddits, resolutions):
    img_exts = ["JPG", "JPEG", "PNG"]
    url = f"https://www.reddit.com/r/{get_subreddits(subreddits)}/search.json?limit=30&t=month&q={' OR '.join(resolutions)}&restrict_sr=on"
    logging.info(f"Searched the following subreddits:\n {subreddits}\n for the following resolutions:\n {resolutions}")
    reddit_json = requests.get(url, headers={'User-agent': 'yourbot'}).json()['data']['children']
    posts = []
    for post in reddit_json:
        if post['data']['url'].split(".")[-1].upper() in img_exts: # only add post to list if file type is one of the image extensions specified
            posts.append(post['data'])
    return posts


if __name__ == '__main__':
    main()
