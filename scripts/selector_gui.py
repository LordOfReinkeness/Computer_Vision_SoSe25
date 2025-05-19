import sys
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import numpy as np
from skimage.io import imread

try:
    RESAMPLE_NEAREST = Image.Resampling.NEAREST
except AttributeError:
    RESAMPLE_NEAREST = Image.NEAREST

class ImageSelector:
    def __init__(self, image_array, zoom=4, zoom_area=40, crosshair=True):
        self.root = tk.Tk()
        self.root.title("Select Corner Points")
        self.img = Image.fromarray(image_array)
        self.photo = ImageTk.PhotoImage(self.img, master=self.root)

        self.points = []
        self.point_items = []
        self.outline = None
        self.preview_line = None
        self._result = None

        self.canvas = tk.Canvas(self.root, width=self.img.width, height=self.img.height)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        self.canvas.pack()

        tk.Button(self.root, text="Done", command=self._finish).pack(fill='x')

        self.zoom = zoom
        self.zoom_area = zoom_area
        self.crosshair = crosshair

        if self.crosshair:
            self.zoom_win = tk.Toplevel(self.root)
            self.zoom_win.overrideredirect(True)
            self.zoom_win.attributes('-topmost', True)
            self.zoom_label = tk.Label(self.zoom_win)
            self.zoom_label.pack()
            self.canvas.bind("<Motion>", self._on_motion)
            self.zoom_win.protocol("WM_DELETE_WINDOW", self._finish)

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.tag_bind("point", "<ButtonPress-1>", self._on_press)
        self.canvas.tag_bind("point", "<B1-Motion>", self._on_drag)
        self.canvas.tag_bind("point", "<ButtonRelease-1>", self._on_release)

        self.root.protocol("WM_DELETE_WINDOW", self._finish)
        self._drag_data = {"item": None, "x": 0, "y": 0}

    def _on_motion(self, event):
        x, y = event.x, event.y

        if 1 <= len(self.points) < 4:
            if self.preview_line:
                self.canvas.delete(self.preview_line)
            x0, y0 = self.points[-1]
            self.preview_line = self.canvas.create_line(x0, y0, x, y, fill='yellow', dash=(4,2))

        r = self.zoom_area // 2
        left = max(0, x - r)
        upper = max(0, y - r)
        right = min(self.img.width, x + r)
        lower = min(self.img.height, y + r)
        patch = self.img.crop((left, upper, right, lower))
        zoomed = patch.resize((patch.width * self.zoom, patch.height * self.zoom), RESAMPLE_NEAREST)

        if self.crosshair:
            draw = ImageDraw.Draw(zoomed)
            w, h = zoomed.size
            draw.line((0, h//2, w, h//2), fill='white')
            draw.line((w//2, 0, w//2, h), fill='white')

        zp = ImageTk.PhotoImage(zoomed, master=self.zoom_win)
        self.zoom_label.configure(image=zp)
        self.zoom_label.image = zp

        gx = self.root.winfo_rootx() + x + 20
        gy = self.root.winfo_rooty() + y + 20
        self.zoom_win.geometry(f"+{gx}+{gy}")
        self.zoom_win.lift()

    def _on_click(self, event):
        if len(self.points) < 4:
            self._add_point(event.x, event.y)
            if self.preview_line:
                self.canvas.delete(self.preview_line)
                self.preview_line = None

    def _add_point(self, x, y):
        r = 5
        item = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill='red', tags="point")
        self.points.append([x, y])
        self.point_items.append(item)
        self._update_outline()

    def _on_press(self, event):
        self._drag_data["item"] = self.canvas.find_withtag('current')[0]
        self._drag_data["x"], self._drag_data["y"] = event.x, event.y

    def _on_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        item = self._drag_data["item"]
        self.canvas.move(item, dx, dy)
        self._drag_data["x"], self._drag_data["y"] = event.x, event.y

    def _on_release(self, event):
        item = self._drag_data["item"]
        coords = self.canvas.coords(item)
        x = (coords[0] + coords[2]) / 2
        y = (coords[1] + coords[3]) / 2
        idx = self.point_items.index(item)
        self.points[idx] = [x, y]
        self._drag_data["item"] = None
        self._update_outline()

    def _update_outline(self):
        if self.outline:
            self.canvas.delete(self.outline)
        if len(self.points) >= 2:
            pts = self.points + ([self.points[0]] if len(self.points) == 4 else [])
            flat = [c for p in pts for c in p]
            self.outline = self.canvas.create_line(flat, fill='yellow', width=2)
            for item in self.point_items:
                self.canvas.tag_raise(item)

    def _finish(self):
        if len(self.points) == 4:
            pts = np.array(self.points)
            cx, cy = pts.mean(axis=0)
            angles = np.arctan2(pts[:,1] - cy, pts[:,0] - cx)
            order = np.argsort(angles)
            self._result = pts[order]
        else:
            self._result = np.zeros((4, 2), dtype=float)
        if self.crosshair and self.zoom_win.winfo_exists():
            self.zoom_win.destroy()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self._result


if __name__ == "__main__":
    img = imread('../data/schraegbild_tempelhof.jpg')
    corners = ImageSelector(img).run()
    print(f"b_n = np.array({corners.tolist()}, dtype=int)")
