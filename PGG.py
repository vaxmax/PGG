import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import sys
import os
import numpy as np
import colorsys


class PaletteGradientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Palette Gradient Generator")
        self.geometry("900x600")
        self.minsize(700, 400)
        self.iconbitmap(self.resource_path("icon.ico"))

        self.init_state()
        self.create_menu()
        self.create_widgets()
        self.bind_events()

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def init_state(self):
        self.original_image = None
        self.result_image = None
        self.display_image = None
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.drag_start = None

    def create_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load Image...", command=self.load_image)
        filemenu.add_command(label="Save Image As...", command=self.save_image)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

    def create_widgets(self):
        self.canvas = tk.Canvas(self, bg="gray", cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.slider_frame = ttk.Frame(self)
        self.slider_frame.pack(fill="x", padx=10, pady=10)

        self.hue_shift = tk.DoubleVar(value=0)
        self.saturation = tk.DoubleVar(value=1.0)
        self.brightness = tk.DoubleVar(value=1.0)
        self.contrast = tk.DoubleVar(value=1.0)

        self.hue_slider = self.create_labeled_slider("Hue Shift", self.hue_shift, -60, 60)
        self.sat_slider = self.create_labeled_slider("Saturation", self.saturation, 0.0, 2.0, 0.01)
        self.bright_slider = self.create_labeled_slider("Brightness", self.brightness, 0.0, 2.0, 0.01)
        self.contrast_slider = self.create_labeled_slider("Contrast", self.contrast, 0.0, 2.0, 0.01)

        self.hue_slider.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.sat_slider.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.bright_slider.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.contrast_slider.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self.slider_frame.columnconfigure((0, 1), weight=1)

    def create_labeled_slider(self, text, variable, minval, maxval, resolution=1.0):
        frame = ttk.Frame(self.slider_frame)
        ttk.Label(frame, text=text).pack(side="left")
        slider = ttk.Scale(frame, from_=minval, to=maxval, variable=variable, orient="horizontal", length=150)
        slider.pack(side="left", fill="x", expand=True)
        value_label = ttk.Label(frame, text=f"{variable.get():.2f}")
        value_label.pack(side="left", padx=5)

        def update_value(event=None):
            value_label.config(text=f"{variable.get():.2f}")
            self.process_image()

        slider.config(command=lambda e: update_value())
        return frame

    def bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        self.canvas.bind("<Button-4>", self.zoom_image)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom_image)  # Linux scroll down

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png"), ("All files", "*.*")])
        if not path:
            return
        try:
            self.original_image = Image.open(path).convert("RGBA")
            self.zoom, self.pan_x, self.pan_y = 1.0, 0, 0
            self.process_image()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image:\n{e}")

    def save_image(self):
        if not self.result_image:
            messagebox.showwarning("Warning", "No generated image to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if path:
            try:
                self.result_image.save(path)
                messagebox.showinfo("Saved", "Image saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save image:\n{e}")

    def start_pan(self, event):
        self.drag_start = (event.x, event.y)

    def do_pan(self, event):
        if not self.drag_start:
            return
        dx, dy = event.x - self.drag_start[0], event.y - self.drag_start[1]
        self.pan_x += dx
        self.pan_y += dy
        self.drag_start = (event.x, event.y)
        self.show_image()

    def zoom_image(self, event):
        delta = event.delta if hasattr(event, 'delta') else (120 if event.num == 4 else -120)
        factor = 1.0 + (delta / 1200.0)
        new_zoom = self.zoom * factor
        if 0.1 < new_zoom < 10:
            self.zoom = new_zoom
            self.show_image()

    def show_image(self):
        if not self.result_image:
            return
        zoomed = self.result_image.resize((int(self.result_image.width * self.zoom),
                                           int(self.result_image.height * self.zoom)), Image.Resampling.LANCZOS)
        self.display_image = ImageTk.PhotoImage(zoomed)
        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, anchor="nw", image=self.display_image)

    def process_image(self):
        if not self.original_image:
            return

        img_w, img_h = self.original_image.size
        block_w, block_h = 32, img_h
        gradient_depth = 10

        result_h = block_h * (gradient_depth + 1)
        result_img = Image.new("RGBA", (img_w, result_h), (0, 0, 0, 0))

        for i in range(img_w // block_w):
            box = (i * block_w, 0, (i + 1) * block_w, block_h)
            base_color = self.original_image.crop(box).resize((1, 1), Image.Resampling.LANCZOS).getpixel((0, 0))
            base_color = (*base_color[:3], 255)
            target_color = self.adjust_color(base_color)
            gradient = self.create_vertical_gradient(base_color, target_color, result_h, block_w)
            result_img.paste(gradient, (i * block_w, 0))

        self.result_image = result_img
        self.show_image()

    def adjust_color(self, color):
        r, g, b, a = color
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

        h = (h + self.hue_shift.get() / 360.0) % 1.0
        s = np.clip(s * self.saturation.get(), 0, 1)
        v = np.clip(v * self.brightness.get(), 0, 1)

        mean_v = 0.5
        v = np.clip((v - mean_v) * self.contrast.get() + mean_v, 0, 1)

        r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
        return (int(r2 * 255), int(g2 * 255), int(b2 * 255), a)

    def create_vertical_gradient(self, start_color, end_color, height, width):
        start, end = np.array(start_color, dtype=np.float32), np.array(end_color, dtype=np.float32)
        gradient = np.linspace(start, end, height, axis=0).astype(np.uint8)
        gradient = np.tile(gradient[:, None, :], (1, width, 1))
        return Image.fromarray(gradient, "RGBA")


if __name__ == "__main__":
    app = PaletteGradientApp()
    app.mainloop()
