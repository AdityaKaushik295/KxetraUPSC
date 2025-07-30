import feedparser
import json
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai


genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash-exp")



def createNotionNotes(text_array):
    page_content =[]

    for item in text_array:
      if len(item)>1 :
        if item.strip()[0:2] == "##":
            block = {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": item.strip()[2:].replace("#", "")}}
                    ]
                }
            }
            page_content.append(block)
        elif item.strip()[0:2] == "**":
          block={
                  "object": "block",
                  "type": "heading_3",
                  "heading_3": {
                      "rich_text": [
                          {"type": "text", "text": {"content": item.strip()[2:].replace("*", "")}}
                      ]
                  }
              }
          page_content.append(block)

        elif item.strip()[0] == "$":
            block = {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": item.strip()[1:].replace("$", "")}}
                         ]
                }
                    }
            page_content.append(block)

        elif item.strip()[0] == "*":
          bullet=item.strip()[1:]
          bullet = bullet.replace("*", "")
          block= {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": bullet
                    }
                }
            ]
        }
    }
          page_content.append(block)

    print(page_content)
    return page_content



def buildvideofeed(feed_url):
    # Parse the RSS feed
    feed = feedparser.parse(feed_url)
    
    # Prepare a list to hold the video details
    videos = []

    # Loop through each entry in the RSS feed
    for entry in feed.entries:
        # Extract title, channel, image (thumbnail), and video link
        title = entry.title
        channel = entry.author
        # Thumbnail is usually in the 'media:thumbnail' tag
        thumbnail_url = entry.media_thumbnail[0]['url'] if 'media_thumbnail' in entry else None
        # Video link is in 'link'
        video_link = entry.link

        # Append the details to the videos list
        videos.append({
            'title': title,
            'channel': channel,
            'image': thumbnail_url,
            'video_link': video_link
        })

    # Return the JSON array of videos
    return videos

#print(buildvideofeed("https://www.youtube.com/feeds/videos.xml?channel_id=UC7Q0EfPzTwtanMVSWuK_QXA"))


def buildvideosummary(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        print(transcript)
    except Exception as e:
        print(f"An error occurred while getting transcript: {e}")
        return None
    transcript_text=""
    for item in transcript:
        transcript_text=transcript_text+" "+item["text"]

    if transcript_text:
        response = model.generate_content(f"Read the youtube video transcript I will be enclosing at the end. Give me a complete hyper detailed yet summarised HALF PAGE notes. Use double hash ## symbols for title, double asterisk ** for subheadings, single asterisks * for bullet points and single dollar $ for paragraphs. (VERY IMPORTANT) Do not use formating for bold or these special symbols inside each of any these blocks in between the lines.Use these symbols only to enclose a line or a heading. (VERY IMPORTANT) Make sure that all blocks which can be headings, paragraphs or bullet points are seperated by newline seperator to put them on different lines. (VERY IMPORTANT) Do not use any special character other than commas (,) and periods (.) inside the blocks. Using special charcters like single or double quotes within the text blocks can break the program. (VERY IMPORTANT) Do not use single quotes or double quotes at any cost anywhere within the text.Do not start a new block on the same line. Use a good ratio of bullet point lines. Now make the notes on the youtube transcript: {transcript} . Make sure you do not include any personal content about the channel or youtuber. These notes are strictly for educational purposes.")

    #print(response.text)
    text = response.text
    text_array = text.split("\n")
    page_blocks=createNotionNotes(text_array)
    return page_blocks



#buildvideosummary("SbzZfk1El9Y")
