import os
import customtkinter as ctk
from gui.peer_list import PeerList
from gui.file_transfer import FileTransfer
from network.torrent_engine import TorrentEngine

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("P2P Notes Sharing App")
        self.geometry("800x600")
        self.resizable(False, False)

        # --- User Info Section ---
        self.user_frame = ctk.CTkFrame(self, fg_color="#23272e", corner_radius=15)
        self.user_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="ew")

        ctk.CTkLabel(self.user_frame, text="Your Name:", font=("Arial", 13)).pack(side="left", padx=(15, 5), pady=10)
        self.name_var = ctk.StringVar(value="User")
        self.name_entry = ctk.CTkEntry(self.user_frame, textvariable=self.name_var, width=120)
        self.name_entry.pack(side="left", padx=(0, 20))

        ip = get_local_ip()
        self.addr_label = ctk.CTkLabel(
            self.user_frame, 
            text=f"IP: {ip}",
            font=("Arial", 13, "bold"), 
            text_color="#f8148c"
        )
        self.addr_label.pack(side="left", padx=10)

        self.start_button = ctk.CTkButton(
            self.user_frame, text="Start P2P Engine", fg_color="#f8148c", hover_color="#c0126b",
            font=("Arial", 13, "bold"), width=140, command=self.start_torrent_engine
        )
        self.start_button.pack(side="right", padx=15)

        # --- Main layout frames ---
        self.left_frame = PeerList(self)
        self.left_frame.grid(row=1, column=0, padx=(20, 10), pady=20, sticky="ns")

        self.right_frame = FileTransfer(self)
        self.right_frame.grid(row=1, column=1, padx=(10, 20), pady=20, sticky="nsew")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Torrent engine setup
        self.torrent_engine = None
        self.save_dir = os.path.join(os.getcwd(), "files")
        os.makedirs(self.save_dir, exist_ok=True)
        self.engine_started = False

        # Connect callbacks
        self.right_frame.share_callback = self.create_and_share_torrent
        self.right_frame.add_torrent_callback = self.add_torrent_file

    def start_torrent_engine(self):
        if self.engine_started:
            return
        
        self.torrent_engine = TorrentEngine(self.save_dir)
        self.engine_started = True
        self.start_button.configure(state="disabled", text="P2P Engine Running")
        self.right_frame.status_label.configure(text="P2P Engine started successfully!")
        
        # Start updating torrent list
        self.after(2000, self.update_torrent_list)

    def create_and_share_torrent(self, file_path):
        if not self.torrent_engine:
            self.right_frame.status_label.configure(text="Start P2P Engine first!")
            return
        
        try:
            torrent_path = self.torrent_engine.create_torrent(file_path)
            self.torrent_engine.add_torrent_file(torrent_path)
            self.right_frame.status_label.configure(text=f"Sharing: {os.path.basename(file_path)}")
        except Exception as e:
            self.right_frame.status_label.configure(text=f"Error: {e}")

    def add_torrent_file(self, torrent_path):
        if not self.torrent_engine:
            self.right_frame.status_label.configure(text="Start P2P Engine first!")
            return
        
        try:
            self.torrent_engine.add_torrent_file(torrent_path)
            self.right_frame.status_label.configure(text="Download started!")
        except Exception as e:
            self.right_frame.status_label.configure(text=f"Error: {e}")

    def update_torrent_list(self):
        if self.torrent_engine:
            torrents = self.torrent_engine.get_torrent_status()
            self.left_frame.update_torrents(torrents)
        self.after(2000, self.update_torrent_list)

    def on_closing(self):
        if self.torrent_engine:
            self.torrent_engine.stop_all()
        self.destroy()

if __name__ == "__main__":
    app = MainWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()