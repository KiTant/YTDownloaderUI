import customtkinter as ctk
import pytubefix
from CTkListbox import CTkListbox
from CTkMessagebox import CTkMessagebox
from tkinter import Tk, filedialog
import threading

# Set the appearance and theme of the application
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Set up the main window properties
        self.title("Yt Downloader")
        self.geometry("1000x250")
        self.minsize(1000, 250)
        self.maxsize(1350, 400)

        self.video = None
        self.checking_video = False
        self.current_itag = None
        self.available_itags = []

        # Initialize the UI components
        self._initialize_components()

    def _initialize_components(self):
        # Video link entry
        self.video_link = ctk.CTkEntry(self, placeholder_text="Video link here", width=400)
        self.video_link.place(relx=0.01, rely=0.05, relwidth=0.4)

        # Check video button
        self.check_video_button = ctk.CTkButton(self, text="Check video", command=self._on_check_video, width=100,
                                                corner_radius=50, fg_color="#f50c28", hover_color="#b83141")
        self.check_video_button.place(relx=0.42, rely=0.05)

        # Label for video info
        self.video_info = ctk.CTkLabel(self, text=self._get_default_video_info(),
                                       fg_color="transparent", font=ctk.CTkFont(family="Arial", size=16))
        self.video_info.place(relx=0.02, rely=0.35)

        # List of all available versions of video
        self.versions = CTkListbox(self, command=self.set_itag, width=525, font=ctk.CTkFont(family="Arial", size=11),
                                   hover_color="#b83141", highlight_color="#8c0a1a")
        self.versions.place(relx=0.35, rely=0.275, relheight=0.5)
        self.versions.insert("END", "No versions available here")

        # Video title label
        self.video_title = ctk.CTkLabel(self, text="Video title: Nothing to show here now",
                                        fg_color="transparent", font=ctk.CTkFont(family="Arial", size=16))
        self.video_title.place(relx=0.02, rely=0.8)

        # Button to download video with current chosen version of video
        self.download_current_type = ctk.CTkButton(self, text="Download current type", command=self._on_download_type,
                                                   corner_radius=50, fg_color="#f50c28",  hover_color="#b83141")
        self.download_current_type.place(relx=0.54, rely=0.05)

    @staticmethod
    def _get_default_video_info(searching=False):
        if not searching:
            return (
                "Highest resolution: Nothing to show here now \n"
                "Lowest resolution: Nothing to show here now \n"
                "Length: Nothing to show here now \n"
                "Views: Nothing to show here now"
            )
        else:
            return (
                "Highest resolution: Searching... \n"
                "Lowest resolution: Searching... \n"
                "Length: Searching... \n"
                "Views: Searching..."
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

    @staticmethod
    def _when_downloaded_type(stream, path):
        CTkMessagebox(title="Saving video", message=f"Video successfully was saved. \nPath: {path}",
                      option_1="Ok", sound=True)

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
                f"Views: {self.video.views}"
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
        self.video_info.configure(text=self._get_default_video_info(searching), fg_color="transparent",
                                  font=ctk.CTkFont(family="Arial", size=16))
        self.video_title.configure(text="Video title: Nothing to show here now")
        self.versions.insert("END", "No versions available here")
        self.video = None
        self.current_itag = None
        self.available_itags.clear()

    def set_itag(self, choosed_version):
        if self.video is None:
            return
        for stream in self.video.streams:
            version_info = self.get_version_info(stream)
            if f"{version_info['mime_type']} without audio - {version_info['resolution']}, " \
               f"Codec: {version_info['codec'][0]}; Size: {version_info['size']} MB" == choosed_version:
                self.current_itag = stream.itag
                return
            elif f"{version_info['mime_type']} with audio - {version_info['resolution']}, " \
                 f"Codec: {version_info['codec'][0]}; Size: {version_info['size']} MB" == choosed_version:
                self.current_itag = stream.itag
                return
            elif f"{version_info['mime_type']} - {version_info['abr']}, " \
                 f"Codec: {version_info['codec'][1]}; Size: {version_info['size']} MB" == choosed_version:
                self.current_itag = stream.itag
                return

    def download_type(self):
        try:
            root = Tk()
            root.withdraw()
            file_path = filedialog.askdirectory(title="Choose a directory for saving video")
            if not file_path:
                return
            CTkMessagebox(title="Saving video", message="Download started, it may take some time.", option_1="Ok")
            stream = self.video.streams.get_by_itag(self.current_itag)
            stream.download(output_path=file_path)
        except:
            CTkMessagebox(title="Saving video (Error)", message="Unexpected error, please try again or try to use VPN.",
                          icon="cancel", option_1="Ok", sound=True)


if __name__ == '__main__':
    app = App()
    app.mainloop()
