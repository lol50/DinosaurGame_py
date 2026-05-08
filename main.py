import tkinter as tk
from PIL import Image, ImageTk
import random, os, json, sys
import time

BASE_W, BASE_H = 1200, 600
BASE_GROUND = BASE_H - 85
BASE_SPEED = 28
MIN_SPAWN_DELAY = 1800
MAX_SPAWN_DELAY = 3200