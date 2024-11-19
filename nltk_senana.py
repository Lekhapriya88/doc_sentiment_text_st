import nltk

def sentiment(text):
    nltk.download('vader_lexicon')
    from nltk.sentiment import SentimentIntensityAnalyzer
    text = str(text)
    sia = SentimentIntensityAnalyzer()
    sent = sia.polarity_scores(text)
    if sent['pos'] > 0.15 and (sent['pos'] > sent['neg']):
        sentiment_label = 'Positive'
    elif (sent['neg'] > 0.15) and (sent['neg'] > sent['pos']):
        sentiment_label = 'Negative'
    elif sent['neu'] > 0.8:
        sentiment_label = 'Neutral'
    else:
        sentiment_label = 'Neutral'
    return sentiment_label
