import os
import libtorrent as lt
import threading
import time
import hashlib

class TorrentEngine:
    def __init__(self, download_dir):
        """
        Initialize the torrent engine with download directory.
        :param download_dir: Directory where downloaded files will be saved
        """
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Create libtorrent session
        self.session = lt.session()
        
        # Set session settings
        settings = {
            'listen_interfaces': '0.0.0.0:6881',
            'enable_dht': True,
            'enable_lsd': True,  # Local Service Discovery
            'enable_upnp': True,
            'enable_natpmp': True,
            'announce_to_all_tiers': True,
            'announce_to_all_trackers': True,
        }
        self.session.apply_settings(settings)
        
        # Start DHT, UPnP, and LSD
        self.session.start_dht()
        self.session.start_upnp()
        self.session.start_lsd()
        
        # Track active torrents
        self.torrents = []
        self.running = True
        
        # Start alert handler thread
        self.alert_thread = threading.Thread(target=self._handle_alerts, daemon=True)
        self.alert_thread.start()
        
        print("Torrent engine initialized successfully")

    def create_torrent(self, file_path, tracker_url="udp://tracker.openbittorrent.com:80/announce"):
        """
        Create a .torrent file from a given file.
        :param file_path: Path to the file to create torrent for
        :param tracker_url: Tracker URL to include in torrent
        :return: Path to created .torrent file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Create file storage
        fs = lt.file_storage()
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        fs.add_file(filename, file_size)
        
        # Create torrent
        t = lt.create_torrent(fs)
        t.set_creator("P2P Notes Sharing App v1.0")
        t.add_tracker(tracker_url)
        
        # Add additional popular trackers for better peer discovery
        additional_trackers = [
            "udp://tracker.opentrackr.org:1337/announce",
            "udp://9.rarbg.to:2710/announce",
            "udp://exodus.desync.com:6969/announce",
            "udp://tracker.torrent.eu.org:451/announce"
        ]
        for tracker in additional_trackers:
            t.add_tracker(tracker)
        
        # Set piece hashes
        lt.set_piece_hashes(t, os.path.dirname(file_path))
        
        # Generate torrent data
        torrent_data = lt.bencode(t.generate())
        
        # Save .torrent file in downloads directory
        torrent_filename = f"{filename}.torrent"
        torrent_path = os.path.join(self.download_dir, torrent_filename)
        
        with open(torrent_path, "wb") as f:
            f.write(torrent_data)
        
        print(f"Torrent created: {torrent_path}")
        return torrent_path

    def add_torrent_file(self, torrent_path):
        """
        Add a .torrent file to the session and start downloading/seeding.
        :param torrent_path: Path to .torrent file
        :return: Torrent handle
        """
        if not os.path.exists(torrent_path):
            raise FileNotFoundError(f"Torrent file not found: {torrent_path}")
        
        # Load torrent info
        info = lt.torrent_info(torrent_path)
        
        # Create add_torrent_params
        params = {
            'ti': info,
            'save_path': self.download_dir,
            'storage_mode': lt.storage_mode_t.storage_mode_sparse,
            'flags': lt.torrent_flags.duplicate_is_error | lt.torrent_flags.auto_managed
        }
        
        # Add torrent to session
        handle = self.session.add_torrent(params)
        self.torrents.append(handle)
        
        print(f"Added torrent: {info.name()}")
        return handle

    def add_magnet_link(self, magnet_uri):
        """
        Add a magnet link to the session.
        :param magnet_uri: Magnet URI string
        :return: Torrent handle
        """
        if not magnet_uri.startswith('magnet:'):
            raise ValueError("Invalid magnet URI")
        
        # Create add_torrent_params for magnet
        params = {
            'save_path': self.download_dir,
            'storage_mode': lt.storage_mode_t.storage_mode_sparse,
            'flags': lt.torrent_flags.duplicate_is_error | lt.torrent_flags.auto_managed
        }
        
        # Add magnet URI
        handle = lt.add_magnet_uri(self.session, magnet_uri, params)
        self.torrents.append(handle)
        
        print(f"Added magnet link")
        return handle

    def get_torrent_status(self):
        """
        Get status of all active torrents.
        :return: List of torrent status dictionaries
        """
        status_list = []
        
        for handle in self.torrents:
            if not handle.is_valid():
                continue
                
            status = handle.status()
            
            # Calculate download/upload speeds
            download_rate = status.download_rate / 1024  # KB/s
            upload_rate = status.upload_rate / 1024      # KB/s
            
            # Get torrent state
            state_str = ['queued', 'checking', 'downloading metadata', 
                        'downloading', 'finished', 'seeding', 'allocating', 
                        'checking fastresume'][status.state]
            
            torrent_info = {
                'name': status.name or "Getting metadata...",
                'progress': status.progress,
                'state': state_str,
                'download_rate': download_rate,
                'upload_rate': upload_rate,
                'num_seeds': status.num_seeds,
                'num_peers': status.num_peers,
                'total_size': status.total_wanted,
                'downloaded': status.total_wanted_done,
                'uploaded': status.all_time_upload,
                'is_seeding': status.is_seeding,
                'is_finished': status.is_finished,
                'error': status.error if status.error else None,
                'info_hash': str(status.info_hash)
            }
            
            status_list.append(torrent_info)
        
        return status_list

    def remove_torrent(self, info_hash, delete_files=False):
        """
        Remove a torrent from the session.
        :param info_hash: Info hash of the torrent to remove
        :param delete_files: Whether to delete downloaded files
        """
        for handle in self.torrents:
            if str(handle.status().info_hash) == info_hash:
                if delete_files:
                    self.session.remove_torrent(handle, lt.options_t.delete_files)
                else:
                    self.session.remove_torrent(handle)
                self.torrents.remove(handle)
                print(f"Removed torrent: {info_hash}")
                break

    def pause_torrent(self, info_hash):
        """
        Pause a specific torrent.
        :param info_hash: Info hash of the torrent to pause
        """
        for handle in self.torrents:
            if str(handle.status().info_hash) == info_hash:
                handle.pause()
                print(f"Paused torrent: {info_hash}")
                break

    def resume_torrent(self, info_hash):
        """
        Resume a specific torrent.
        :param info_hash: Info hash of the torrent to resume
        """
        for handle in self.torrents:
            if str(handle.status().info_hash) == info_hash:
                handle.resume()
                print(f"Resumed torrent: {info_hash}")
                break

    def _handle_alerts(self):
        """
        Handle libtorrent alerts in a separate thread.
        """
        while self.running:
            alerts = self.session.pop_alerts()
            for alert in alerts:
                alert_type = type(alert).__name__
                
                # Handle different types of alerts
                if alert_type == 'torrent_finished_alert':
                    print(f"Download completed: {alert.torrent_name}")
                elif alert_type == 'torrent_error_alert':
                    print(f"Torrent error: {alert.error_message}")
                elif alert_type == 'metadata_received_alert':
                    print(f"Metadata received for: {alert.torrent_name}")
                elif alert_type == 'state_changed_alert':
                    state_str = ['queued', 'checking', 'downloading metadata', 
                               'downloading', 'finished', 'seeding', 'allocating', 
                               'checking fastresume'][alert.state]
                    print(f"State changed to {state_str}: {alert.torrent_name}")
            
            time.sleep(1)  # Check for alerts every second

    def get_session_stats(self):
        """
        Get overall session statistics.
        :return: Dictionary with session stats
        """
        stats = self.session.get_stats()
        return {
            'total_download': stats.get('net.recv_bytes', 0),
            'total_upload': stats.get('net.sent_bytes', 0),
            'download_rate': stats.get('net.recv_rate', 0),
            'upload_rate': stats.get('net.sent_rate', 0),
            'num_torrents': len(self.torrents),
            'dht_nodes': stats.get('dht.dht_nodes', 0)
        }

    def stop_all(self):
        """
        Stop all torrents and cleanup the session.
        """
        print("Stopping torrent engine...")
        self.running = False
        
        # Pause all torrents
        for handle in self.torrents:
            if handle.is_valid():
                handle.pause()
        
        # Stop session services
        self.session.stop_dht()
        self.session.stop_lsd()
        self.session.stop_upnp()
        
        # Remove all torrents
        for handle in self.torrents:
            if handle.is_valid():
                self.session.remove_torrent(handle)
        
        self.torrents.clear()
        print("Torrent engine stopped successfully")

    def is_running(self):
        """
        Check if the torrent engine is running.
        :return: Boolean indicating if engine is running
        """
        return self.running

    def get_torrent_files(self, info_hash):
        """
        Get list of files in a specific torrent.
        :param info_hash: Info hash of the torrent
        :return: List of file information
        """
        for handle in self.torrents:
            if str(handle.status().info_hash) == info_hash:
                if handle.torrent_file():
                    files = []
                    torrent_info = handle.torrent_file()
                    for i in range(torrent_info.num_files()):
                        file_info = torrent_info.file_at(i)
                        files.append({
                            'index': i,
                            'path': file_info.path,
                            'size': file_info.size
                        })
                    return files
        return []

# Example usage and testing
if __name__ == "__main__":
    # Test the torrent engine
    engine = TorrentEngine("./test_downloads")
    
    try:
        # Keep the engine running for testing
        while True:
            status = engine.get_torrent_status()
            if status:
                for torrent in status:
                    print(f"Torrent: {torrent['name']} - Progress: {torrent['progress']*100:.1f}%")
            time.sleep(5)
    except KeyboardInterrupt:
        print("Shutting down...")
        engine.stop_all()