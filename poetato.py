import configparser
import sys
import os
import shelve
import tempfile
import urllib.request
import multiprocessing as mp

import chat
from overlay import Overlay


def fetch_and_persist_emotes(msg, cache_path, out):
    url = "http://static-cdn.jtvnw.net/emoticons/v1/{0}/1.0"
    cache = shelve.open(cache_path)
    e_to_p = {}
    for e in msg.emotes.keys():
        if e not in cache:
            path, headers = urllib.request.urlretrieve(url.format(e))
            cache[e] = path
        e_to_p[e] = cache[e]
    cache.close()
    msg.localemotes = e_to_p
    out.put(msg)


def update_loop(chat_i, emote_cache, messages):
    while True:
        msg = chat.parse(chat_i.recv())
        fetch_and_persist_emotes(msg, emote_cache, messages)


if __name__ == '__main__':
    mp.freeze_support()
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    config = configparser.ConfigParser()
    config.read(os.path.abspath(os.path.join(base_dir, 'poetato.ini')))
    emote_cache = os.path.abspath(
        os.path.join(tempfile.gettempdir(), 'poetato_emotes'))
    messages = mp.Queue()

    chat_i, chat_o = mp.Pipe()
    incoming = mp.Process(target=chat.listen,
                          args=(config['twitch']['username'],
                                config['twitch']['token'],
                                config['twitch']['channel'],
                                chat_o),
                          daemon=True)
    incoming.start()

    d_opts = config['overlay']

    close = mp.Queue()
    display = Overlay(int(d_opts['width']), int(d_opts['height']),
                      int(d_opts['xpos']), int(d_opts['ypos']),
                      d_opts['background'], d_opts['foreground'],
                      int(d_opts['font_size']), float(d_opts['opacity'])/100,
                      messages, close)

    # this is a crappy hack to let us make sure display is initialized ...
    while True:
        if hasattr(display, 'text'):
            break

    ul = mp.Process(target=update_loop, args=(chat_i, emote_cache, messages))
    ul.start()

    close.get()
    incoming.terminate()
    ul.terminate()
