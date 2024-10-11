from youtube_transcript_api import YouTubeTranscriptApi

def get_combined_transcript(video_id):
    try:
        playlist = ['6itriowPhhM', 'Ln2PevCHEuU', 'Li3EV0YVuSg']
    
        sentences = YouTubeTranscriptApi.get_transcript("6itriowPhhM", languages=['ko'])

        # 모든 텍스트를 하나의 문자열로 결합
        combined_text = " ".join([sentence['text'] for sentence in sentences])
    except Exception as e:
        logger.error(f"Error fetching youTube transcript: {e}")
        return ""