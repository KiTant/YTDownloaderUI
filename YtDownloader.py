import customtkinter as ctk
import pytubefix
from CTkListbox import CTkListbox
from CTkMenuBar import CTkTitleMenu, CustomDropdownMenu
from CTkMessagebox import CTkMessagebox
from moviepy.editor import VideoFileClip, AudioFileClip
from tkinter import Tk, filedialog
import os
import webbrowser
import json
import threading

# Set the appearance and theme of the application
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

appdata_dir = os.getenv('APPDATA')
settings_file = os.path.join(appdata_dir, 'xzyYtDownloader', 'settings.json')


class TitleMenu(CTkTitleMenu):
    def __init__(self, MainWindow: ctk.CTk, CurrentWindow: ctk.CTkToplevel or ctk.CTk):
        super().__init__(master=CurrentWindow, x_offset=150)
        self.button_1 = self.add_cascade("Settings", hover_color="#b83141")

        self.dropdown1 = CustomDropdownMenu(widget=self.button_1)
        self.dropdown1.add_option(option="Preferences (Ctrl + P)", command=MainWindow.preferences)
        self.dropdown1.add_option(option="Load preferences (Ctrl + L)", command=MainWindow.load_settings)
        self.dropdown1.add_option(option="Save preferences (Ctrl + S)", command=MainWindow.save_settings)


class PreferencesWindow(ctk.CTkToplevel):
    def __init__(self, MainWindow: ctk.CTk):
        super().__init__()
        self.MainWindow = MainWindow
        self.title("Preferences")
        self.geometry("700x350")

        # Default path for saving selection
        self.default_path_label = ctk.CTkLabel(self, text=f"Default path for saving: {MainWindow.settings['default_path']}")
        self.default_path_label.pack(pady=5)
        self.default_path_selection = ctk.CTkButton(self, text="Choose default path", command=self.choose_default_path,
                                                    corner_radius=50, fg_color="#f50c28", hover_color="#b83141")
        self.default_path_selection.pack(pady=10)
        self.default_path = MainWindow.settings['default_path']

        # Theme selection
        ctk.CTkLabel(self, text="Theme:").pack(pady=10)
        self.theme_var = ctk.StringVar(value=MainWindow.settings['theme'])
        ctk.CTkRadioButton(self, text="Dark", variable=self.theme_var, value="dark", hover_color="#b83141", border_color="#f50c28", fg_color="#f50c28").pack(pady=5)
        ctk.CTkRadioButton(self, text="Light", variable=self.theme_var, value="light", hover_color="#b83141", border_color="#f50c28", fg_color="#f50c28").pack(pady=5)

        MainWindow.all_children.append(self)

        ctk.CTkButton(self, text="Apply", command=self.apply_preferences, corner_radius=50, fg_color="#f50c28", hover_color="#b83141").pack(pady=20)

        self.protocol("WM_DELETE_WINDOW", lambda: MainWindow.destroy_other_window(self))

        self.after(100, lambda: self.focus_set())

    def choose_default_path(self):
        file_path = filedialog.askdirectory(title="Choose a directory for saving video")
        if not file_path:
            return
        else:
            self.default_path_label.configure(text=f"Default path for saving: {file_path}")
            self.default_path = file_path

    def apply_preferences(self):
        self.MainWindow.settings = {"default_path": self.default_path, "theme": self.theme_var.get()}
        ctk.set_appearance_mode(self.theme_var.get())
        CTkMessagebox(title="Applying preferences", message="Preferences successfully applied.",
                      icon="check", option_1="Ok")
        self.after(100, lambda: self.focus_set())


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Set up the main window properties
        self.title("Yt Downloader")
        self.geometry("1000x250")

        self.maxsize(1300, 500)

        self.settings = {"default_path": "None", "theme": "dark"}
        self.video = None
        self.checking_video = False
        self.complete_callback_working = True
        self.current_itag = None
        self.downloading = False
        self.available_itags = []
        self.current_type = "Non-Assigned"
        self.all_children = []

        # Initialize the UI components
        self._initialize_components()

    def _initialize_components(self):
        # Video link entry
        self.video_link = ctk.CTkEntry(self, placeholder_text="Video link here", width=400)
        self.video_link.place(relx=0.01, rely=0.05, relwidth=0.4)

        # Title menu
        self.menu = TitleMenu(self, self)

        # Check video button
        self.check_video_button = ctk.CTkButton(self, text="Check video", command=self._on_check_video, width=100,
                                                corner_radius=50, fg_color="#f50c28", hover_color="#b83141")
        self.check_video_button.place(relx=0.42, rely=0.05)

        # Label for video info
        self.video_info = ctk.CTkLabel(self, text=self._get_default_video_info(),
                                       fg_color="transparent", font=ctk.CTkFont(family="Arial", size=16))
        self.video_info.place(relx=0.02, rely=0.18)

        # List of all available versions of video
        self.versions = CTkListbox(self, command=self.set_itag, width=525, font=ctk.CTkFont(family="Arial", size=11),
                                   hover_color="#b83141", highlight_color="#8c0a1a")
        self.versions.place(relx=0.35, rely=0.275, relheight=0.5)
        self.versions.insert("END", "No versions available here")

        # Video title label
        self.video_title = ctk.CTkLabel(self, text="Video title: Nothing to show here now",
                                        fg_color="transparent", font=ctk.CTkFont(family="Arial", size=16))
        self.video_title.place(relx=0.02, rely=0.8)

        # Open thumbnail of video button
        self.open_thumbnail_button = ctk.CTkButton(self, text="Open video thumbnail", command=lambda: self._open_thumbnail("video"), width=100, height=14,
                                                corner_radius=50, fg_color="#f50c28", hover_color="#b83141")
        self.open_thumbnail_button.place(relx=0.02, rely=0.72)

        # Open author channel button
        self.open_channel_button = ctk.CTkButton(self, text="Open author channel", command=self._open_channel, width=100, height=14,
                                                   corner_radius=50, fg_color="#f50c28", hover_color="#b83141")
        self.open_channel_button.place(relx=0.18, rely=0.72)

        # Open channel thumbnail button
        self.open_channel_thumbnail_button = ctk.CTkButton(self, text="Open channel thumbnail", command=lambda: self._open_thumbnail("channel"), width=100,
                                                 height=14,
                                                 corner_radius=50, fg_color="#f50c28", hover_color="#b83141")
        self.open_channel_thumbnail_button.place(relx=0.095, rely=0.62)

        # Button to download video with current chosen version of video
        self.download_current_type = ctk.CTkButton(self, text="Download current type", command=self._on_download_type,
                                                   corner_radius=50, fg_color="#f50c28",  hover_color="#b83141")
        self.download_current_type.place(relx=0.54, rely=0.05)

        # Button to download video with the best quality and sound of video
        self.download_video_with_audio = ctk.CTkButton(self, text="Download current video type with audio", command=self._on_download_video_with_audio,
                                                   corner_radius=50, fg_color="#f50c28", hover_color="#b83141")
        self.download_video_with_audio.place(relx=0.715, rely=0.05)

        self.bind("<Control-s>", lambda event: self.save_settings())
        self.bind("<Control-p>", lambda event: self.preferences())
        self.bind("<Control-l>", lambda event: self.load_settings())

        self.load_settings()
        self.minsize(1000, 250)

    def _open_thumbnail(self, type):
        if self.video is None:
            CTkMessagebox(title=f"Open {type} thumbnail (Error)", message="Please check some video for using this button.",
                          icon="cancel", option_1="Ok", sound=True)
        else:
            try:
                if type == "video":
                    webbrowser.open(self.video.thumbnail_url)
                else:
                    webbrowser.open(pytubefix.contrib.channel.Channel(self.video.channel_url).thumbnail_url)
            except Exception as e:
                CTkMessagebox(title=f"Open {type} thumbnail (Error)", message=f"Unexpected error: {e}.",
                              icon="cancel", option_1="Ok", sound=True)

    def _open_channel(self):
        if self.video is None:
            CTkMessagebox(title="Open channel (Error)", message="Please check some video for using this button.",
                          icon="cancel", option_1="Ok", sound=True)
        else:
            webbrowser.open(self.video.channel_url)

    @staticmethod
    def _get_default_video_info(searching=False):
        if not searching:
            return (
                "Highest resolution: Nothing to show here now \n"
                "Lowest resolution: Nothing to show here now \n"
                "Length: Nothing to show here now \n"
                "Views: Nothing to show here now \n"
                "Publish date: Nothing to show here now \n"
                "Channel ID: Nothing to show here now"
            )
        else:
            return (
                "Highest resolution: Searching... \n"
                "Lowest resolution: Searching... \n"
                "Length: Searching... \n"
                "Views: Searching... \n"
                "Publish date: Searching... \n"
                "Channel ID: Searching..."
            )

    def _on_check_video(self):
        if self.checking_video is True:
            CTkMessagebox(title="Checking video (Error)", message="Please wait.",
                          icon="cancel", option_1="Ok", sound=True)
            return
        url = self.video_link.get().strip()
        if not url:
            CTkMessagebox(title="Checking video (Error)", message="Please enter a URL.",
                          icon="cancel", option_1="Ok", sound=True)
            return
        threading.Thread(target=self.check_video, args=(url,)).start()

    def _on_download_type(self):
        if not self.current_itag:
            CTkMessagebox(title="Saving video (Error)", message="Please choose a version from the list.",
                          icon="cancel", option_1="Ok", sound=True)
            return
        threading.Thread(target=self.download_type).start()

    def _on_download_video_with_audio(self):
        if self.current_type != "video without audio":
            CTkMessagebox(title="Saving video (Error)",
                          message="Current type is NOT video without audio (or you just not chose it).",
                          icon="cancel", option_1="Ok", sound=True)
            return
        threading.Thread(target=self.download_type_with_audio).start()

    def _when_downloaded_type(self, stream, path):
        self.downloading = False
        if self.complete_callback_working is False:
            return
        msg = CTkMessagebox(title="Saving video", message=f"Video successfully was saved. \nPath: {path}",
                            options=["Ok, open it.", "Ok"], sound=True)
        if msg.get() == "Ok, open it.":
            try:
                os.startfile(path)
            except Exception as e:
                CTkMessagebox(title="Open video (Error)",
                              message=f"Unexpected error: {e}.",
                              icon="cancel", option_1="Ok", sound=True)

    @staticmethod
    def get_version_info(stream):
        info = {
            "mime_type": getattr(stream, "mime_type", "Unknown type"),
            "resolution": getattr(stream, "resolution", "Unknown"),
            "codec": stream.parse_codecs() if hasattr(stream, "parse_codecs") else ["Unknown"],
            "size": getattr(stream, "filesize_mb", 0),
            "abr": getattr(stream, "abr", "Unknown")
        }
        return info

    def check_video(self, url):
        self.checking_video = True
        self._reset_video_info(searching=True)
        try:
            self.video = pytubefix.YouTube(url=url, on_complete_callback=self._when_downloaded_type)
            self._update_video_info()
            self.checking_video = False
        except Exception as e:
            CTkMessagebox(title="Checking video (Error)", message="Unexpected error, check URL, is it correct?",
                          icon="cancel", option_1="Ok", sound=True)
            self._reset_video_info()
            self.checking_video = False
            print(f"Error: {e}")

    def preferences(self):
        for window in self.all_children:
            if window.title() == "Preferences":
                return
        PreferencesWindow(self)

    def destroy_other_window(self, window):
        self.all_children.remove(window)
        window.destroy()

    def _update_video_info(self):
        self.available_itags.clear()
        self.versions.delete(0, "end")

        streams = self.video.streams
        highest_video = streams.get_highest_resolution()
        lowest_video = streams.get_lowest_resolution()

        if lowest_video:
            self._add_stream_to_listbox(lowest_video, "with audio")
        if highest_video and highest_video.itag not in self.available_itags:
            self._add_stream_to_listbox(highest_video, "with audio")

        for stream in streams.filter(only_video=True):
            if stream.itag not in self.available_itags:
                self._add_stream_to_listbox(stream, "without audio")

        for stream in streams.filter(only_audio=True):
            if stream.itag not in self.available_itags:
                self._add_stream_to_listbox(stream)

        highest_resolution = max(int(stream.resolution[:-1]) for stream in streams.filter(only_video=True))
        lowest_resolution = min(int(stream.resolution[:-1]) for stream in streams.filter(only_video=True))

        self.video_info.configure(
            text=(
                f"Highest resolution: {highest_resolution} \n"
                f"Lowest resolution: {lowest_resolution} \n"
                f"Length: {self.video.length} second(s) \n"
                f"Views: {self.video.views} \n"
                f"Publish date: {self.video.publish_date} \n"
                f"Channel ID: {self.video.channel_id}"
            ),
            fg_color="transparent",
            font=ctk.CTkFont(family="Arial", size=16)
        )
        self.video_title.configure(text=f"Video title: {self.video.title}")

    def _add_stream_to_listbox(self, stream, audio_status=""):
        version_info = self.get_version_info(stream)
        self.available_itags.append(stream.itag)
        self.versions.insert("END", f"{version_info['mime_type']} {audio_status} - "
                                    f"{version_info['resolution'] or version_info['abr']}, "
                                    f"Codec: {version_info['codec'][0] or version_info['codec'][1]}; Size: {version_info['size']} MB")

    def _reset_video_info(self, searching=False):
        self.versions.delete(0, "end")
        self.current_type = "Non-Assigned"
        self.video_info.configure(text=self._get_default_video_info(searching), fg_color="transparent",
                                  font=ctk.CTkFont(family="Arial", size=16))
        self.video_title.configure(text="Video title: Nothing to show here now")
        self.versions.insert("END", "No versions available here")
        self.video = None
        self.current_itag = None
        self.available_itags.clear()

    def set_itag(self, choosed_version):
        if self.video is None:
            self.current_type = "Non-Assigned"
            return
        for stream in self.video.streams:
            version_info = self.get_version_info(stream)
            if f"{version_info['mime_type']} without audio - {version_info['resolution']}, " \
               f"Codec: {version_info['codec'][0]}; Size: {version_info['size']} MB" == choosed_version:
                self.current_itag = stream.itag
                self.current_type = "video without audio"
                return
            elif f"{version_info['mime_type']} with audio - {version_info['resolution']}, " \
                 f"Codec: {version_info['codec'][0]}; Size: {version_info['size']} MB" == choosed_version:
                self.current_itag = stream.itag
                self.current_type = "video with audio"
                return
            elif f"{version_info['mime_type']} - {version_info['abr']}, " \
                 f"Codec: {version_info['codec'][1]}; Size: {version_info['size']} MB" == choosed_version:
                self.current_itag = stream.itag
                self.current_type = "audio"
                return

    def _get_download_path(self):
        file_path = self.settings['default_path']
        if file_path == 'None' or not os.path.exists(file_path):
            root = Tk()
            root.withdraw()
            file_path = filedialog.askdirectory(title="Choose a directory for saving video")
            if not file_path:
                return None
        return file_path

    def download_type(self):
        try:
            if self.downloading is False:
                self.downloading = True
                file_path = self._get_download_path()
                if file_path is None:
                    self.downloading = False
                    return
                CTkMessagebox(title="Saving video", message="Download started, it may take some time.", option_1="Ok")
                stream = self.video.streams.get_by_itag(self.current_itag)
                stream.download(output_path=file_path)
            else:
                CTkMessagebox(title="Downloading video (Error)",
                              message="Wait until your previous video download will be finished.",
                              icon="cancel", option_1="Ok", sound=True)
        except Exception as e:
            self.downloading = False
            CTkMessagebox(title="Saving video (Error)",
                          message="Unexpected error, please try again or try to use VPN or goodbyedpi.",
                          icon="cancel", option_1="Ok", sound=True)
            print(f"Error: {e}")

    def download_type_with_audio(self):
        try:
            if self.downloading is True:
                CTkMessagebox(title="Downloading video (Error)",
                              message="Wait until your previous video download will be finished.",
                              icon="cancel", option_1="Ok", sound=True)
            else:
                self.complete_callback_working = False
                self.downloading = True
                file_path = self._get_download_path()
                if file_path is None:
                    self.complete_callback_working = True
                    self.downloading = False
                    return
                CTkMessagebox(title="Saving video", message="Download started, it may take a lot of time (or not).",
                              option_1="Ok")
                video_stream = self.video.streams.get_by_itag(self.current_itag)
                audio_stream = self.video.streams.filter(only_audio=True).order_by('abr').desc().first()
                video_path = os.path.join(file_path, 'YtDownloader_video.mp4')
                audio_path = os.path.join(file_path, 'YtDownloader_audio.mp3')
                video_stream.download(output_path=file_path, filename='YtDownloader_video.mp4')
                audio_stream.download(output_path=file_path, filename='YtDownloader_audio.mp3')
                video_clip = VideoFileClip(video_path)
                audio_clip = AudioFileClip(audio_path)
                final_clip = video_clip.set_audio(audio_clip)
                final_clip.write_videofile(os.path.join(file_path, f"{self.video.title}.mp4"), codec='libx264',
                                           threads=12, preset='superfast', verbose=False, logger=None)
                os.remove(video_path)
                os.remove(audio_path)
                self.complete_callback_working = True
                self.downloading = False
                msg = CTkMessagebox(title="Saving video", message="Video successfully was saved.",
                                    options=["Ok, open it.", "Ok"], sound=True)
                if msg.get() == "Ok, open it.":
                    try:
                        os.startfile(os.path.join(file_path, f"{self.video.title}.mp4"))
                    except Exception as e:
                        CTkMessagebox(title="Open video (Error)",
                                      message=f"Unexpected error: {e}.",
                                      icon="cancel", option_1="Ok", sound=True)
        except Exception as e:
            self.complete_callback_working = True
            self.downloading = False
            CTkMessagebox(title="Saving video (Error)", message="Unexpected error, please try again or try to use VPN or goodbyedpi.",
                          icon="cancel", option_1="Ok", sound=True)
            print(f"Error: {e}")

    def save_settings(self):
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def load_settings(self):
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                self.settings = json.load(f)
                ctk.set_appearance_mode(self.settings['theme'])
                for window in self.all_children:
                    if window.title() == "Preferences":
                        self.destroy_other_window(window)
        else:
            pass

if __name__ == '__main__':
    app = App()
    app.mainloop()
