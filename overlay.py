from collections import defaultdict
from tkinter import Tk, Text, PhotoImage, RAISED
import threading
import random
import win32api
import win32con
import pywintypes

class MyRoot(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.attributes('-alpha', 0.0)

class Overlay(threading.Thread):
    def __init__(self,
                 width, height,
                 xpos, ypos,
                 bgcolor, fgcolor,
                 fontsize, opacity,
                 messages, close):
        threading.Thread.__init__(self, daemon=True)

        self.width = width
        self.height = height
        self.xpos = xpos
        self.ypos = ypos
        self.bgcolor = bgcolor
        self.fgcolor = fgcolor
        self.fontsize = fontsize
        self.opacity = opacity
        self.messages = messages
        self.close = close

        username_colors = [
            '#0000ff',
            '#ff7f50',
            '#1e90ff',
            '#00ff7f',
            '#9acd32',
            '#00ff00',
            '#ff4500',
            '#ff0000',
            '#daa520',
            '#ff69b4',
            '#5f9ea0',
            '#2e8b57',
            '#d2691e',
            '#8a2be2',
            '#b22222',
        ]
        self.color_for = defaultdict(lambda: random.choice(username_colors))
        self.start()
        self.images = []

    def die(self):
        self.close.put('killme')
        self.root.destroy()

    def run(self):
        self.root = MyRoot()
        self.root.lower()
        self.root.iconify()
        self.root.title('poetato overlay')
        self.root.protocol('WM_DELETE_WINDOW', self.die)

        self.app = Toplevel(self.root)
        self.app.geometry("%dx%d+%d+%d" % (self.width, self.height,
                                            self.xpos, self.ypos))
        self.app.resizable(width=False, height=False)
        self.app.overrideredirect(1)
        self.app.minsize(width=self.width, height=self.height)
        self.app.maxsize(width=self.width, height=self.height)
        self.app.attributes(
            '-alpha', self.opacity,
            '-topmost', True,
            '-disabled', True,
        )

        self.text = Text(self.app,
                         bg=self.bgcolor, fg=self.fgcolor,
                         wrap='word', state='disabled')
        self.text.configure(font=('Helvetica', self.fontsize, 'bold'))
        self.text.pack()
        self.app.lift()

        # tell Windows(tm) to allow clicks to pass through our overlay.
        hWindow = pywintypes.HANDLE(int(self.root.frame(), 16))
        exStyle = (win32con.WS_EX_LAYERED |
                   win32con.WS_EX_TRANSPARENT |
                   win32con.WS_EX_NOACTIVATE)
        win32api.SetWindowLong(hWindow, win32con.GWL_EXSTYLE, exStyle)

        self.app.after(100, self.update)
        self.app.mainloop()

    def update(self):
        if self.messages.empty():
            self.app.after(100, self.update)
            return
        msg = self.messages.get_nowait()

        self.text['state'] = 'normal'

        if self.text.index('end-1c') != '1.0':
            self.text.insert('end', '\n')

        self.text.insert('end', "{0}: ".format(msg.display_name))
        emote_insertions = {}
        for eid, pos in msg.emotes.items():
            for p in pos:
                emote_insertions[p[0]] = (msg.localemotes[eid], p[1]+1)

        cur_pos = 0
        for i in sorted(emote_insertions.keys()):
            if cur_pos < i:
                self.text.insert('end', msg.message[cur_pos:i])
            img = PhotoImage(file=emote_insertions[i][0])
            self.text.image_create('end', image=img)

            # tkinter *needs* us to save a reference to a displayed image :(
            self.images.append(img)
            cur_pos = emote_insertions[i][1]
        if cur_pos < len(msg.message):
            self.text.insert('end', msg.message[cur_pos:])

        color = self.color_for[msg.display_name]
        self.text.tag_config(msg.display_name, foreground=color, relief=RAISED)
        self.text.tag_add(msg.display_name, 'end-1l', 'end-1l wordend')

        self.text.see('end')
        self.text['state'] = 'disabled'
        self.app.after(100, self.update)
