import sys
import googleapiclient.discovery
import pandas as pd 
import spacy 
import webbrowser

def YT_API_connect(DEVELOPER_KEY):

    # Youtube API connection

    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

    return youtube

def most_popular_videos(conn, channel_id, max_results):

    # Get the video id of most popular videos on the channel

    request = conn.search().list(
        part="snippet",
        maxResults=max_results,
        type = 'video',
        channelId = channel_id,
        order = 'viewCount'
    )

    response = request.execute()

    return [video_id['id']['videoId'] for video_id in response['items']]

def comments_per_video(conn, video_ids, max_results):

    # Get the comment thread for all the videos
    comments = []
    for video_id in video_ids:
        request = conn.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults = max_results
        )

        response = request.execute()
        comments.append(response)

    return comments

def entity_recognition(comments):

    # Use spacy to identify entities in all the comments

    nlp = spacy.load("en_core_web_sm")

    all_comments = ''
    entities = []

    # Concatenate for faster processing
    for response in comments:
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textOriginal']
            all_comments += comment + ' '

    doc = nlp(all_comments)

    for ent in doc.ents:
        entities.append(list((ent.text, ent.label_, ent.lemma_, ent.sentiment)))

    df = pd.DataFrame(entities, columns=['text', 'label', 'lemma', 'sentiment'])
    return df


if __name__ == "__main__":
    
    channel_id="UCGHZpIpAWJQ-Jy_CeCdXhMA"
    wikipedia_base_url = 'https://en.wikipedia.org/wiki/'
    DEVELOPER_KEY = "#####"

    if len(sys.argv) > 1:
        channel_id = sys.argv[1]

    try:
        conn = YT_API_connect(DEVELOPER_KEY)
        print('Connection established to channel with id: ', channel_id)
        video_ids = most_popular_videos(conn, channel_id, 35)
        comments = comments_per_video(conn, video_ids, 100)
        print('Channel information gathered...')
        print('Entitiy recognition starting...')
        final = entity_recognition(comments)
        print('Entitiy recognition finished...')

        # Filter to get proper full names
        persons = final[(final['label'] == 'PERSON') & (final['text'].str.count(' ') > 1)]
        # Determine the most mentioned person across the most popular videos on the channel
        most_mentioned = persons.groupby(by=['lemma']).count().sort_values(['label','text'], ascending=False).index[0]

        print('The most mentioned person in this channels comment is: ', most_mentioned)
        print('Opening wiki article...')
        # Open articel about most mentioned person
        webbrowser.open(wikipedia_base_url+most_mentioned)
    except:
        print('Something went wrong!')
