from youtube_transcript_api import YouTubeTranscriptApi

def get_combined_transcript(playlist):
    subscribes = []
    try:
        for video_id in playlist:
            sentences = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
            # 각 비디오의 텍스트를 하나의 문자열로 결합하여 리스트에 추가
            combined_text = " ".join([sentence['text'] for sentence in sentences])
            subscribes.append(combined_text)
    except Exception as e:
        print(f"Error fetching YouTube transcript for video {video_id}: {e}")
    
    return subscribes

# 사용 예시
playlist = ['6itriowPhhM', 'Ln2PevCHEuU', 'Li3EV0YVuSg', '3XbtEX3jUv4']
transcripts = get_combined_transcript(playlist)