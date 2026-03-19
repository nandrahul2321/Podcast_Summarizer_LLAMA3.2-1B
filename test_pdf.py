from home import generate_pdf
from io import BytesIO

# create sample record
rec={'video_url':'http://example.com','summary':'This is a test.\n\nNew paragraph.','transcript_sentiment':{'sentiment':'Neutral','sentiment_score':50,'emotion':'Neutral'},'summary_sentiment':{},'transcription_confidence':80,'summary_confidence':90}
pdf=generate_pdf('vid',rec)
print('pdf bytes',len(pdf.getvalue()) if pdf else 'none')
