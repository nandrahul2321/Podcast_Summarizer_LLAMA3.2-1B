# db.py
from pymongo import MongoClient, ASCENDING

client = MongoClient('mongodb://localhost:27017/')
db = client['Podcast_Summarizer_llama3']
users_collection = db['users']
summaries_collection = db['summaries']
history_collection = db['history']
comments_collection = db['comments']
chat_history_collection = db['chat_history']
password_resets_collection = db['password_resets']  # stores OTP + token with TTL expiry

# -------------------- Indexes --------------------
# Drop stale multilanguage index if it exists from prior runs
try:
    summaries_collection.drop_index('idx_video_lang')
except Exception:
    pass

# Simple index on video_id for fast lookups
summaries_collection.create_index(
    [('video_id', ASCENDING)],
    name='idx_video_id'
)

# Index for fast comment retrieval by video
comments_collection.create_index(
    [('video_id', ASCENDING), ('created_at', ASCENDING)],
    name='idx_comments_video'
)

# Index for chat history retrieval
chat_history_collection.create_index(
    [('user_id', ASCENDING), ('video_id', ASCENDING), ('timestamp', ASCENDING)],
    name='idx_chat_history'
)

# TTL index: MongoDB auto-deletes password reset records 5 minutes after expires_at
password_resets_collection.create_index(
    [('expires_at', ASCENDING)],
    expireAfterSeconds=0,
    name='idx_password_resets_ttl'
)
# Fast lookup by email
password_resets_collection.create_index(
    [('email', ASCENDING)],
    name='idx_password_resets_email'
)
# Fast lookup by token (for reset-password route)
password_resets_collection.create_index(
    [('token', ASCENDING)],
    name='idx_password_resets_token'
)