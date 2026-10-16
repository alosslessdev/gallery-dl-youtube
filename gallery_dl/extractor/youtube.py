# -*- coding: utf-8 -*-

# Copyright 2026 alosslessdev
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.youtube.com/"""

import re
import time

from .common import Extractor, Message
from .. import text, util, exception

BASE_PATTERN = (r"(?:https?://)?(?:www\.|m\.)?"
                r"youtube\.com")
POSTS_PATTERN = (BASE_PATTERN +
                 r"/(?:(?:channel|c|user)/)?@?[\w.-]+"
                 r"/(?:posts|community)/?(?:[?#].*)?$")
POST_PATTERN = BASE_PATTERN + r"/post/[\w-]+(?:[?#].*)?$"

RE_DATE = re.compile(
    r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago",
    re.IGNORECASE,
)
DATE_UNITS = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
    "week": 604800,
    "month": 2592000,
    "year": 31536000,
}


class YoutubeExtractor(Extractor):
    """Base class for youtube community post extractors"""
    category = "youtube"
    directory_fmt = ("{category}", "{channel}")
    filename_fmt = "{post_id}_{num}.{extension}"
    archive_fmt = "{post_id}_{num}"
    root = "https://www.youtube.com"

    def _init(self):
        self.api = YoutubeAPI(self)

    def items(self):
        for post, date in self.api_posts():
            images = extract_images(post)
            if not images:
                self.log.warning("Skipping post %s (no images)",
                                 post.get("postId") or "?")
                continue

            data = self._prepare(post, date)
            data["count"] = len(images)
            yield Message.Directory, "", data

            for data["num"], url in enumerate(images, 1):
                text.nameext_from_url(url, data)
                yield Message.Url, url, data

    def api_posts(self):
        return ()

    def _prepare(self, post, date):
        author = post.get("authorEndpoint") or {}
        browse = author.get("browseEndpoint") or {}
        webcmd = (author.get("commandMetadata") or {}).get(
            "webCommandMetadata") or {}
        path = browse.get("canonicalBaseUrl") or webcmd.get("url") or ""
        channel_id = browse.get("browseId") or ""
        post_id = post.get("postId") or ""

        data = {
            "post_id"    : post_id,
            "url"        : self.root + "/post/" + post_id,
            "content"    : post_text(post),
            "channel"    : path.rpartition("/")[2].lstrip("@") or channel_id,
            "channel_id" : channel_id,
            "channel_url": self.root + path if path else self.root,
            "author"     : ((post.get("authorText") or {}).get("simpleText")
                            or runs_text(post.get("authorText"))),
            "likes"      : parse_count(
                (post.get("voteCount") or {}).get("simpleText")),
        }

        if date:
            data["date"] = self.parse_datetime_iso(date)
        else:
            match = RE_DATE.search(
                "".join(run.get("text", "")
                        for run in ((post.get("publishedTimeText") or {})
                                    .get("runs") or ())))
            if match:
                seconds = (int(match.group(1)) *
                           DATE_UNITS[match.group(2).lower()])
                data["date"] = self.parse_timestamp(time.time() - seconds)

        return data


class YoutubePostsExtractor(YoutubeExtractor):
    """Extractor for all posts of a channel's community tab"""
    subcategory = "posts"
    pattern = POSTS_PATTERN
    example = "https://www.youtube.com/@USER/posts"

    def api_posts(self):
        return self.api.posts_tab(self.url)


class YoutubePostExtractor(YoutubeExtractor):
    """Extractor for a single community post"""
    subcategory = "post"
    pattern = POST_PATTERN
    example = "https://www.youtube.com/post/POSTID"

    def api_posts(self):
        return self.api.post_page(self.url)


class YoutubeAPI():
    """Interface to youtube.com's innertube API"""

    def __init__(self, extractor):
        self.extractor = extractor
        self.key = ""
        self.version = ""

    def posts_tab(self, url):
        """Yield (post, None) for every post on a channel's posts tab"""
        data = self._page(url)

        tab = find_posts_tab(data)
        posts, token = collect_posts(tab if tab is not None else data)
        if not posts:
            self.extractor.log.warning("No community posts found")
            return

        yield from ((post, None) for post in posts)

        while token:
            if not (self.key and self.version):
                self.extractor.log.debug(
                    "Missing innertube credentials; "
                    "unable to fetch additional posts")
                return

            data = self._browse(token)
            posts, token = collect_posts(data)
            for post in posts:
                yield post, None

    def post_page(self, url):
        """Yield a single (post, publishDate) tuple"""
        page = self.extractor.request(url).text
        posts, _ = collect_posts(self._parse(page))
        if not posts:
            raise exception.NotFoundError(url)

        yield posts[0], text.extr(page, '"publishDate":"', '"') or None

    def _page(self, url):
        if "hl=" not in url:
            url += ("&" if "?" in url else "?") + "hl=en"
        page = self.extractor.request(url).text
        return self._parse(page)

    def _parse(self, page):
        if not self.key:
            self.key = text.extr(page, 'INNERTUBE_API_KEY":"', '"')
            self.version = text.extr(
                page, 'INNERTUBE_CONTEXT_CLIENT_VERSION":"', '"')

        raw = text.extr(page, "var ytInitialData = ", ";</script>")
        if not raw:
            raise exception.ExtractionError(
                "Unable to find 'ytInitialData' in response")
        return util.json_loads(raw)

    def _browse(self, token):
        url = "{}/youtubei/v1/browse?key={}".format(
            self.extractor.root, self.key)
        return self.extractor.request_json(
            url, method="POST",
            json={
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": self.version,
                        "hl": "en",
                    },
                },
                "continuation": token,
            })


def find_posts_tab(data):
    """Locate the community posts tab of a channel page"""
    tabs = (((data.get("contents") or {})
             .get("twoColumnBrowseResultsRenderer") or {})
            .get("tabs") or ())
    for tab in tabs:
        renderer = (tab.get("tabRenderer") or
                    tab.get("expandableTabRenderer") or {})
        content = renderer.get("content")
        if content and contains_post(content):
            return content
    return None


def contains_post(value):
    """Determine whether 'value' contains a community post"""
    if isinstance(value, dict):
        if "backstagePostRenderer" in value:
            return True
        return any(contains_post(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_post(item) for item in value)
    return False


def collect_posts(value):
    """Collect all posts and the first continuation token from 'value'"""
    posts = []
    token = []

    def walk(obj):
        if isinstance(obj, dict):
            if "backstagePostRenderer" in obj:
                posts.append(obj["backstagePostRenderer"])

            if not token and "continuationItemRenderer" in obj:
                item = obj["continuationItemRenderer"]
                cmd = item.get("continuationEndpoint") or {}
                nxt = item.get("nextContinuationData") or {}
                found = (((cmd.get("continuationCommand") or {})
                          .get("token")) or nxt.get("continuation"))
                if found:
                    token.append(found)

            for item in obj.values():
                walk(item)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(value)
    return posts, (token[0] if token else None)


def extract_images(post):
    """Extract image URLs from a post's attachment"""
    attachment = post.get("backstageAttachment") or {}

    if "backstageImageRenderer" in attachment:
        renderers = (attachment["backstageImageRenderer"],)
    elif "postMultiImageRenderer" in attachment:
        renderers = [item.get("backstageImageRenderer")
                     for item in
                     (attachment["postMultiImageRenderer"].get("images")
                      or ())]
    else:
        return ()

    urls = []
    for renderer in renderers:
        thumbnails = (((renderer or {}).get("image")) or {}).get(
            "thumbnails") or ()
        if thumbnails:
            largest = max(thumbnails, key=_thumbnail_size)
            urls.append(text.ensure_http_scheme(largest["url"]))
    return tuple(urls)


def _thumbnail_size(thumbnail):
    return thumbnail.get("width", 0) * thumbnail.get("height", 0)


def post_text(post):
    """Extract the text content of a post"""
    return runs_text(post.get("contentText"))


def runs_text(value):
    """Join the text of all runs in a 'text'-like object"""
    runs = (value or {}).get("runs") or ()
    return "".join(run.get("text", "") for run in runs)


def parse_count(value):
    """Convert count values like '1.4K' to an integer"""
    if not value:
        return 0
    value = value.replace("\xa0", "").replace(" ", "").replace(",", "")
    factor = 1
    if value[-1:] in ("K", "M", "B"):
        factor = {"K": 10 ** 3, "M": 10 ** 6, "B": 10 ** 9}[value[-1]]
        value = value[:-1]
    try:
        return int(float(value) * factor)
    except Exception:
        return 0
