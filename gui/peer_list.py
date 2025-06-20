import customtkinter as ctk

class PeerList(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, width=250, fg_color="#23272e", corner_radius=15)
        self.label = ctk.CTkLabel(self, text="Active Torrents", font=("Arial", 16, "bold"))
        self.label.pack(pady=(15, 10))
        
        # Use a text widget for better formatting
        self.torrent_display = ctk.CTkTextbox(self, width=230, height=400, fg_color="#181a20", text_color="#f1f1f1", font=("Arial", 11))
        self.torrent_display.pack(padx=10, pady=(0, 15))

    def update_torrents(self, torrents):
        """Update the display with current torrent status"""
        self.torrent_display.delete("1.0", "end")
        if not torrents:
            self.torrent_display.insert("end", "No active torrents\n")
            return
        
        for torrent in torrents:
            name = torrent.get('name', 'Unknown')
            progress = torrent.get('progress', 0) * 100
            state = torrent.get('state', 'Unknown')
            num_seeds = torrent.get('num_seeds', 0)
            num_peers = torrent.get('num_peers', 0)
            
            self.torrent_display.insert("end", f"📁 {name}\n")
            self.torrent_display.insert("end", f"   Progress: {progress:.1f}%\n")
            self.torrent_display.insert("end", f"   Status: {state}\n")
            self.torrent_display.insert("end", f"   Seeds: {num_seeds} | Peers: {num_peers}\n")
            self.torrent_display.insert("end", "─" * 30 + "\n")

    # Keep the old method for backward compatibility (if needed)
    def update_peers(self, peers):
        """Legacy method - now shows message about torrent mode"""
        self.torrent_display.delete("1.0", "end")
        self.torrent_display.insert("end", "Now using torrent-based P2P\n")
        self.torrent_display.insert("end", "Add torrents to see activity here\n")