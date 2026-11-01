#!/usr/bin/env python3
"""Open a pcap in the Wireshark GUI (WSLg) with the TLS key log and a display filter, grab the window, save a PNG.
usage: wireshark_screenshot.py capture.pcap "display filter" out.png [width height]
Needs: Wireshark, WSLg (DISPLAY=:0), pip install python-xlib pillow. Closes the window it opened."""
import os, subprocess, sys, time
from Xlib import display, X
from PIL import Image
pcap, flt, out = sys.argv[1:4]
w, h = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1500, 820)
keys = os.path.join(os.path.dirname(os.path.abspath(pcap)), "keys.log")
p = subprocess.Popen(["wireshark", "-o", f"tls.keylog_file:{keys}", "-t", "r", "-r", pcap, "-Y", flt],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = display.Display(os.environ.get("DISPLAY", ":0")); root = d.screen().root
def find(wn, name, depth=0):
    try: kids = wn.query_tree().children
    except Exception: return None
    for c in kids:
        try:
            if c.get_wm_name() == name and c.get_attributes().map_state == 2: return c
        except Exception: pass
        r = find(c, name, depth + 1) if depth < 4 else None
        if r: return r
win = None
for _ in range(40):
    win = find(root, os.path.basename(pcap))
    if win: break
    time.sleep(0.5)
try:
    if not win: sys.exit("Wireshark window not found")
    win.configure(width=w, height=h); d.sync(); time.sleep(4)
    g = win.get_geometry()
    raw = win.get_image(0, 0, g.width, g.height, X.ZPixmap, 0xffffffff)
    Image.frombytes("RGB", (g.width, g.height), raw.data, "raw", "BGRX").save(out); print("saved", out, g.width, g.height)
finally:
    p.terminate()
