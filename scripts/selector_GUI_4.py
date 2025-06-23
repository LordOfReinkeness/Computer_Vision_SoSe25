import tkinter as tk
from tkinter import ttk
import sys
import os
from PIL import Image, ImageTk
import argparse


class PointSelectionGUI:
    def __init__(self, image_paths):
        self.root = tk.Tk()
        self.root.title("Point Selection")
        self.root.state('zoomed')

        self.image_paths = image_paths
        self.images = []
        self.thumbnail_images = []
        self.current_image_idx = 0
        self.points = {}

        self.load_images()
        self.setup_gui()

    def load_images(self):
        for i, path in enumerate(self.image_paths):
            img = Image.open(path)
            self.images.append(img)
            self.points[i] = []

            thumbnail = img.copy()
            thumbnail.thumbnail((200, 150), Image.Resampling.LANCZOS)
            self.thumbnail_images.append(ImageTk.PhotoImage(thumbnail))

        self.update_main_image()

    def update_main_image(self):
        main_img = self.images[self.current_image_idx].copy()
        main_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
        self.main_photo = ImageTk.PhotoImage(main_img)
        self.main_scale_x = main_img.width / self.images[self.current_image_idx].width
        self.main_scale_y = main_img.height / self.images[self.current_image_idx].height

    def setup_gui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        thumbnail_frame = ttk.Frame(main_frame)
        thumbnail_frame.pack(fill=tk.X, pady=(0, 10))

        self.thumb_buttons = []
        for i, thumb in enumerate(self.thumbnail_images):
            btn = tk.Button(thumbnail_frame, image=thumb,
                            command=lambda idx=i: self.select_image(idx),
                            relief=tk.SUNKEN if i == 0 else tk.RAISED)
            btn.pack(side=tk.LEFT, padx=5)
            self.thumb_buttons.append(btn)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(control_frame, text="Click on image to place points").pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Close", command=self.close_app).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(control_frame, text="Copy Output", command=self.print_coordinates).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(control_frame, text="Clear Points", command=self.clear_points).pack(side=tk.RIGHT, padx=(5, 0))

        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.canvas.create_image(400, 300, image=self.main_photo, tags="main_image")

        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))

        self.info_label = ttk.Label(info_frame, text="")
        self.info_label.pack(side=tk.LEFT)

        self.update_info()

    def select_image(self, idx):
        self.current_image_idx = idx

        for i, btn in enumerate(self.thumb_buttons):
            btn.config(relief=tk.SUNKEN if i == idx else tk.RAISED)

        self.update_main_image()

        self.canvas.delete("main_image")
        self.canvas.create_image(400, 300, image=self.main_photo, tags="main_image")

        self.redraw_points()
        self.update_info()

    def on_canvas_click(self, event):
        canvas_x = event.x
        canvas_y = event.y

        img_bounds = self.canvas.bbox("main_image")
        if not img_bounds:
            return

        img_x1, img_y1, img_x2, img_y2 = img_bounds

        if img_x1 <= canvas_x <= img_x2 and img_y1 <= canvas_y <= img_y2:
            rel_x = (canvas_x - img_x1) / self.main_scale_x
            rel_y = (canvas_y - img_y1) / self.main_scale_y

            self.points[self.current_image_idx].append([rel_x, rel_y])
            self.redraw_points()
            self.update_info()

    def redraw_points(self):
        self.canvas.delete("point")

        for i, point in enumerate(self.points[self.current_image_idx]):
            x = point[0] * self.main_scale_x + (400 - self.main_photo.width() // 2)
            y = point[1] * self.main_scale_y + (300 - self.main_photo.height() // 2)

            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="red", outline="black", tags="point")
            self.canvas.create_text(x + 12, y - 12, text=str(i + 1), fill="red", font=("Arial", 10, "bold"),
                                    tags="point")

    def clear_points(self):
        self.points[self.current_image_idx] = []
        self.redraw_points()
        self.update_info()

    def update_info(self):
        current_points = len(self.points[self.current_image_idx])
        total_points = sum(len(pts) for pts in self.points.values())
        filename = os.path.basename(self.image_paths[self.current_image_idx])
        self.info_label.config(
            text=f"{filename}: {current_points} points | Total: {total_points} points")

    def format_output(self):
        output_lines = []
        for img_idx, points in self.points.items():
            if points:
                filename = os.path.splitext(os.path.basename(self.image_paths[img_idx]))[0]
                formatted_points = [[round(p[0]), round(p[1])] for p in points]
                output_lines.append(f"{filename} = {formatted_points}")
        return "\n".join(output_lines)

    def print_coordinates(self):
        output = self.format_output()

        if not output:
            print("No points placed on any images")
            return

        print("\n=== COORDINATES ===")
        print(output)
        print("==================\n")

        self.show_output_popup(output)

    def show_output_popup(self, output):
        popup = tk.Toplevel(self.root)
        popup.title("Coordinates Output")
        popup.geometry("600x400")
        popup.transient(self.root)
        popup.grab_set()

        frame = ttk.Frame(popup)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Copy this output to your Jupyter notebook:").pack(anchor=tk.W, pady=(0, 5))

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert(tk.END, output)
        text_widget.config(state=tk.DISABLED)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        def copy_to_clipboard():
            popup.clipboard_clear()
            popup.clipboard_append(output)
            copy_btn.config(text="Copied!")
            popup.after(1000, lambda: copy_btn.config(text="Copy to Clipboard"))

        copy_btn = ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard)
        copy_btn.pack(side=tk.LEFT)

        ttk.Button(button_frame, text="Close", command=popup.destroy).pack(side=tk.RIGHT)

    def close_app(self):
        output = self.format_output()
        if output:
            print("\n=== FINAL COORDINATES ===")
            print(output)
            print("========================\n")
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description='Simple point selection GUI')
    parser.add_argument('directory', help='Directory containing image files')

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        sys.exit(1)

    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
    image_files = []

    for filename in sorted(os.listdir(args.directory)):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            image_files.append(os.path.join(args.directory, filename))

    if len(image_files) < 1:
        print(f"Error: No image files found in {args.directory}")
        sys.exit(1)

    try:
        app = PointSelectionGUI(image_files)
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()