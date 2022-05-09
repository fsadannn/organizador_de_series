import os
from typing import Set

subs_formats: Set[str] = set([".srt", ".idx", ".sub", ".ssa", ".ass"])
video_formats: Set[str] = set([".3g2",
                               ".3gp",
                               ".3gp2",
                               ".asf",
                               ".avi",
                               ".divx",
                               ".flv",
                               ".mk3d",
                               ".m4v",
                               ".mk2",
                               ".mka",
                               ".mkv",
                               ".mov",
                               ".mp4",
                               ".mp4a",
                               ".mpeg",
                               ".mpg",
                               ".ogg",
                               ".ogm",
                               ".ogv",
                               ".ra",
                               ".ram",
                               ".rm",
                               ".rmvb",
                               ".ts",
                               ".wav",
                               ".webm",
                               ".wma",
                               ".wmv",
                               ".vob"])


def get_ext(name: str):
    _, ext = os.path.splitext(name)
    ext = ext.lower()

    return ext


def is_video(name: str):
    _, ext = os.path.splitext(name)
    ext = ext.lower()

    return ext in video_formats
