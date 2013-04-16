#!/usr/bin/env python

####################################################################
#
# Using a list of video URL from Khan Academy figure out if
# Bulgarian subtitles are available and complete. Print the
# results in CSV format.
#
# Copyright (c) 2013, Alexander Todorov <atodorov@REMOVE-ME.otb.bg>
# http://opensource.org/licenses/MIT
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
####################################################################

import sys
import json
from httplib2 import Http
from urllib import urlencode
from bs4 import BeautifulSoup

in_data = open('videos.csv', 'r').read()
h = Http()
i = 0

# print CSV header
print "I,PERCENT,VIDEO,CANONICAL,YOUTUBE,SUBTITLES"

#loop over all URLs
for video_url in in_data.split("\n"):
    try:
        i += 1
        resp, content = h.request(video_url, "GET")
        if resp.status != 200:
            raise Exception("HTTP error %d - %s" % (resp.status, video_url))

        canonical_url = resp['content-location']

        soup = BeautifulSoup(content)

        # YouTube widget is in iframe b/c we don't have JavaScript
        for iframe in soup.find_all('iframe'):
            youtube_url = iframe['src'].split("?")[0].replace('embed/', 'watch?v=')
            params = { 'video_url' : '"%s"' % youtube_url}
            widget_url = 'http://www.amara.org/widget/rpc/jsonp/show_widget?%s&is_remote=true' % urlencode(params)
            # ^^^ Amara JavaScript widget used in the page

            # fetch JSONP from Amara
            resp, content = h.request(widget_url, "GET")
            if resp.status != 200:
                raise Exception("HTTP error %d - %s" % (resp.status, widget_url))

            # content is JSONP callback so get only the JSON data structure
            content = content[9:-2]
            amara_data = json.loads(content)

            # loop over all languages
            for lang in amara_data['drop_down_contents']:
                # we care only about Bulgarian
                if lang['language'] == 'bg':
                    percent_done = 0

                    # All of these keys may be present or may not.
                    # Play clever and try to figure out if translation is complete
                    if lang.has_key('is_complete') and lang['is_complete']:
                        percent_done = 100

                    if lang.has_key('in_progress') and not lang['in_progress']:
                        percent_done = 100

                    if lang.has_key('percent_done'):
                        percent_done = lang['percent_done']


                    # different output based on completion
                    subs_url = ""
                    if percent_done < 97:
                        subs_url = "http://www.amara.org/en/videos/%s" % amara_data['video_id']
                    else:
                        subs_url = "http://www.amara.org/en/videos/%s/bg/%d/#revisions" % (amara_data['video_id'], lang['pk'])

                    # print the results
                    print "%d,%d,%s,%s,%s,%s" % (i, percent_done, video_url, canonical_url, youtube_url, subs_url)

                    # break the for lang loop
                    break
    except:
        print >> sys.stderr, "FAILED:", video_url
        continue
