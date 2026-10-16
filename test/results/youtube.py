# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import youtube


__tests__ = (
{
    "#url"     : "https://www.youtube.com/@Kamitsurugi/posts",
    "#category": ("", "youtube", "posts"),
    "#class"   : youtube.YoutubePostsExtractor,
    "#count"   : ">= 10",
    "#pattern" : r"https://yt3\.ggpht\.com/.+=s\d+",
    "#metadata": {
        "post_id"    : str,
        "url"        : r"https://www\.youtube\.com/post/Ug[\w-]+",
        "content"    : str,
        "channel"    : "Kamitsurugi",
        "channel_id" : r"UC[\w-]{22}",
        "channel_url": "https://www.youtube.com/@Kamitsurugi",
        "author"     : str,
        "likes"      : int,
        "count"      : range(1, 10),
        "num"        : range(1, 10),
        "date"       : "type:datetime",
    },
},
{
    "#url"     : "https://www.youtube.com/channel/UCUErrriX4EM3BXXZNPKW4Sw/posts",
    "#class"   : youtube.YoutubePostsExtractor,
},
{
    "#url"     : "https://www.youtube.com/@Kamitsurugi/community",
    "#class"   : youtube.YoutubePostsExtractor,
},
{
    "#url"     : "https://www.youtube.com/c/Kamitsurugi/posts",
    "#class"   : youtube.YoutubePostsExtractor,
},
{
    "#url"     : "https://www.youtube.com/@Kamitsurugi/posts?view=0&sort=dd",
    "#class"   : youtube.YoutubePostsExtractor,
},
{
    "#url"     : "https://m.youtube.com/@Kamitsurugi/posts",
    "#class"   : youtube.YoutubePostsExtractor,
},
{
    "#url"     : "https://www.youtube.com/post/Ugkxpv_8h5GobN41v5dstclyeNs_zi1zPffr",
    "#category": ("", "youtube", "post"),
    "#class"   : youtube.YoutubePostExtractor,
    "#count"   : range(1, 10),
    "#pattern" : r"https://yt3\.ggpht\.com/.+=s\d+",
    "#metadata": {
        "post_id"    : "Ugkxpv_8h5GobN41v5dstclyeNs_zi1zPffr",
        "url"        : "https://www.youtube.com/post/Ugkxpv_8h5GobN41v5dstclyeNs_zi1zPffr",
        "content"    : "This is what I saw at the store today, should I buy them? 👀",
        "channel"    : "Kamitsurugi",
        "channel_id" : r"UC[\w-]{22}",
        "channel_url": r"https://www\.youtube\.com/@Kamitsurugi",
        "author"     : str,
        "likes"      : int,
        "count"      : range(1, 10),
        "date"       : "dt:2025-06-15 06:08:46",
    },
},
{
    "#url"     : "https://www.youtube.com/post/UgkxZusu9I1Z-VuU5PGZNA2gclHi8V9CJVZk",
    "#class"   : youtube.YoutubePostExtractor,
    "#count"   : 0,
    "#log"     : "Skipping post UgkxZusu9I1Z-VuU5PGZNA2gclHi8V9CJVZk (no images)",
},
)
