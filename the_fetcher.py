import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp
import threading
import os
from pathlib import Path

class MediaDownloader:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("The Fetcher")
        self.app.geometry("800x600")
        
        # Set dark mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Download control
        self.download_thread = None
        self.cancel_download = False
        self.paused = False
        self.current_downloader = None
        
        # Default download path
        self.download_path = str(Path.home() / "Downloads")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ctk.CTkFrame(self.app)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title/Dashboard
        title_label = ctk.CTkLabel(
            main_frame, 
            text="🎬 The Fetcher", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # URL Input Section
        url_frame = ctk.CTkFrame(main_frame)
        url_frame.pack(fill="x", pady=10)
        
        url_label = ctk.CTkLabel(url_frame, text="Media URL:", font=ctk.CTkFont(size=14))
        url_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.url_entry = ctk.CTkEntry(
            url_frame, 
            placeholder_text="Paste YouTube, Instagram, TikTok, or Facebook URL here...",
            height=40
        )
        self.url_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        # Options Section
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)
        
        # Quality dropdown
        quality_label = ctk.CTkLabel(options_frame, text="Quality:", font=ctk.CTkFont(size=14))
        quality_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.quality_var = ctk.StringVar(value="Best")
        self.quality_dropdown = ctk.CTkOptionMenu(
            options_frame,
            values=["Best", "1080p", "720p", "480p", "360p", "Audio Only"],
            variable=self.quality_var,
            width=150
        )
        self.quality_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Format dropdown
        format_label = ctk.CTkLabel(options_frame, text="Format:", font=ctk.CTkFont(size=14))
        format_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        
        self.format_var = ctk.StringVar(value="MP4")
        self.format_dropdown = ctk.CTkOptionMenu(
            options_frame,
            values=["MP4", "MKV", "WebM", "MP3", "M4A"],
            variable=self.format_var,
            width=150
        )
        self.format_dropdown.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        
        # Download path
        path_label = ctk.CTkLabel(options_frame, text="Save to:", font=ctk.CTkFont(size=14))
        path_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.path_entry = ctk.CTkEntry(options_frame, width=400)
        self.path_entry.insert(0, self.download_path)
        self.path_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        browse_btn = ctk.CTkButton(
            options_frame,
            text="Browse",
            command=self.browse_folder,
            width=100
        )
        browse_btn.grid(row=1, column=3, padx=10, pady=10)
        
        options_frame.columnconfigure(1, weight=1)
        
        # Progress Section
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", pady=10)
        
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to download",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=(0, 10))
        
        # Control Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        self.download_btn = ctk.CTkButton(
            button_frame,
            text="📥 Download",
            command=self.start_download,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#144870"
        )
        self.download_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        self.pause_btn = ctk.CTkButton(
            button_frame,
            text="⏸ Pause",
            command=self.pause_download,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#d68910",
            hover_color="#8f5d07",
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=self.cancel_download_func,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#c41e3a",
            hover_color="#8b1529",
            state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        # Info footer
        info_label = ctk.CTkLabel(
            main_frame,
            text="Supports: YouTube, Instagram, TikTok, Facebook, Twitter, and 1000+ sites",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info_label.pack(pady=(10, 0))
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path = folder
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)
    
    def progress_hook(self, d):
        if self.cancel_download:
            raise Exception("Download cancelled by user")
            
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0%').strip()
                percent = float(percent_str.replace('%', ''))
                
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                
                self.app.after(0, lambda: self.progress_bar.set(percent / 100))
                self.app.after(0, lambda: self.progress_label.configure(
                    text=f"{percent:.1f}% | Speed: {speed} | ETA: {eta}"
                ))
                self.app.after(0, lambda: self.status_label.configure(
                    text="Downloading..."
                ))
            except:
                pass
                
        elif d['status'] == 'finished':
            self.app.after(0, lambda: self.progress_bar.set(1))
            self.app.after(0, lambda: self.progress_label.configure(text="100%"))
            self.app.after(0, lambda: self.status_label.configure(
                text="Processing... (Converting format)"
            ))
    
    def download_media(self, url):
        try:
            self.cancel_download = False
            self.paused = False
            
            # Configure options based on selections
            quality = self.quality_var.get()
            format_choice = self.format_var.get().lower()
            
            # Build format string
            if quality == "Audio Only":
                format_string = 'bestaudio/best'
            elif quality == "Best":
                format_string = 'bestvideo+bestaudio/best'
            else:
                height = quality.replace('p', '')
                format_string = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
            
            # Set output template and options
            ydl_opts = {
                'format': format_string,
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'merge_output_format': format_choice if format_choice in ['mp4', 'mkv', 'webm'] else None,
            }
            
            # Handle audio-only downloads
            if quality == "Audio Only" or format_choice in ['mp3', 'm4a']:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format_choice,
                    'preferredquality': '192',
                }]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.current_downloader = ydl
                ydl.download([url])
            
            self.app.after(0, lambda: self.status_label.configure(
                text="✅ Download completed successfully!"
            ))
            self.app.after(0, lambda: messagebox.showinfo(
                "Success", 
                f"Media downloaded successfully!\nSaved to: {self.download_path}"
            ))
            
        except Exception as e:
            error_msg = str(e)
            if "cancelled by user" in error_msg.lower():
                self.app.after(0, lambda: self.status_label.configure(
                    text="❌ Download cancelled"
                ))
            else:
                self.app.after(0, lambda: self.status_label.configure(
                    text=f"❌ Error: {error_msg}"
                ))
                self.app.after(0, lambda: messagebox.showerror("Error", f"Download failed:\n{error_msg}"))
        
        finally:
            self.app.after(0, self.reset_buttons)
    
    def start_download(self):
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a valid URL")
            return
        
        self.download_path = self.path_entry.get().strip()
        
        if not os.path.exists(self.download_path):
            try:
                os.makedirs(self.download_path)
            except:
                messagebox.showerror("Error", "Invalid download path")
                return
        
        # Update button states
        self.download_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.cancel_btn.configure(state="normal")
        
        # Start download in separate thread
        self.download_thread = threading.Thread(target=self.download_media, args=(url,))
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def pause_download(self):
        # Note: yt-dlp doesn't support pause/resume natively
        # This is a placeholder for future implementation
        if not self.paused:
            self.paused = True
            self.pause_btn.configure(text="▶ Resume")
            self.status_label.configure(text="⏸ Paused (Note: Pause/Resume not fully supported)")
        else:
            self.paused = False
            self.pause_btn.configure(text="⏸ Pause")
            self.status_label.configure(text="Downloading...")
    
    def cancel_download_func(self):
        self.cancel_download = True
        self.status_label.configure(text="Cancelling download...")
        self.cancel_btn.configure(state="disabled")
    
    def reset_buttons(self):
        self.download_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="⏸ Pause")
        self.cancel_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
    
    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    app = MediaDownloader()
    app.run()