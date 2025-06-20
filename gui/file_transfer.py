import customtkinter as ctk
from tkinter import filedialog

BUTTON_COLOR = "#f8148c"

class FileTransfer(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#23272e", corner_radius=15)
        self.selected_file = None
        self.share_callback = None  # To be set by MainWindow
        self.add_torrent_callback = None  # To be set by MainWindow

        self.label = ctk.CTkLabel(self, text="File Transfer", font=("Arial", 16, "bold"))
        self.label.pack(pady=(20, 15))

        # File selection section
        self.select_button = ctk.CTkButton(
            self, text="Select File to Share", fg_color=BUTTON_COLOR, hover_color="#c0126b",
            font=("Arial", 14, "bold"), command=self.select_file, width=200, height=40, corner_radius=10
        )
        self.select_button.pack(pady=(0, 10))

        # Share file section
        self.share_button = ctk.CTkButton(
            self, text="Create & Share Torrent", fg_color=BUTTON_COLOR, hover_color="#c0126b",
            font=("Arial", 14, "bold"), command=self.share_file, width=200, height=40, corner_radius=10
        )
        self.share_button.pack(pady=(0, 20))

        # Add torrent section
        self.add_torrent_button = ctk.CTkButton(
            self, text="Add Torrent File", fg_color="#4a9eff", hover_color="#3578cc",
            font=("Arial", 14, "bold"), command=self.add_torrent, width=200, height=40, corner_radius=10
        )
        self.add_torrent_button.pack(pady=(0, 10))

        # Magnet link section
        self.magnet_entry = ctk.CTkEntry(self, placeholder_text="Paste magnet link here...", width=300)
        self.magnet_entry.pack(pady=(0, 10))

        self.add_magnet_button = ctk.CTkButton(
            self, text="Add Magnet Link", fg_color="#4a9eff", hover_color="#3578cc",
            font=("Arial", 14, "bold"), command=self.add_magnet, width=200, height=40, corner_radius=10
        )
        self.add_magnet_button.pack(pady=(0, 20))

        # Progress bar
        self.progress = ctk.CTkProgressBar(self, width=350, height=12, progress_color=BUTTON_COLOR)
        self.progress.set(0)
        self.progress.pack(pady=(0, 20))

        # Status label
        self.status_label = ctk.CTkLabel(self, text="Ready to share files via P2P", font=("Arial", 12), text_color="#f1f1f1")
        self.status_label.pack()

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.selected_file = file_path
            self.status_label.configure(text=f"Selected: {file_path.split('/')[-1]}")
            self.progress.set(0)

    def share_file(self):
        if self.selected_file and self.share_callback:
            self.status_label.configure(text="Creating torrent and starting share...")
            self.progress.set(0.1)
            self.share_callback(self.selected_file)
        else:
            self.status_label.configure(text="Please select a file first.")

    def add_torrent(self):
        torrent_path = filedialog.askopenfilename(filetypes=[("Torrent files", "*.torrent")])
        if torrent_path and self.add_torrent_callback:
            self.add_torrent_callback(torrent_path)

    def add_magnet(self):
        magnet_uri = self.magnet_entry.get().strip()
        if magnet_uri and self.add_torrent_callback:
            # For magnet links, we can pass them to the same callback
            self.add_torrent_callback(magnet_uri)
            self.magnet_entry.delete(0, "end")
        else:
            self.status_label.configure(text="Please enter a magnet link.")