
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from main import graph_app, ask_question_to_bot

import sqlite3
import uuid


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI()


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# SQLite Database
# ---------------------------------------------------------

conn = sqlite3.connect(
    "Chatbot.db",
    check_same_thread=False
)

cursor = conn.cursor()


# Create table for chat threads

cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_threads (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()


# ---------------------------------------------------------
# Home
# ---------------------------------------------------------

@app.get("/")
async def home_view():

    return {
        "messages": "Welcome to our home view"
    }


# ---------------------------------------------------------
# Create New Chat
# ---------------------------------------------------------

@app.post("/chat/new")
async def create_chat(
    title: str ="New Chat"
):

    thread_id = str(uuid.uuid4())


    cursor.execute(
        """
        INSERT INTO chat_threads (id, title)
        VALUES (?, ?)
        """,
        (
            thread_id,
            title
        )
    )


    conn.commit()


    return {
        "thread_id": thread_id,
        "title": title
    }


# ---------------------------------------------------------
# Get All Chat Threads

@app.get("/chat/threads")
async def get_threads():

    cursor.execute(
        """
        SELECT id, title
        FROM chat_threads
        ORDER BY created_at DESC
        """
    )

    rows = cursor.fetchall()


    return [
        {
            "id": row[0],
            "title": row[1]
        }
        for row in rows
    ]


# ---------------------------------------------------------
# Get Previous Messages
# ---------------------------------------------------------

@app.get("/chat/{thread_id}/messages")
async def get_chat_messages(
    thread_id: str
):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }


    # Get conversation from LangGraph SQLite checkpoint

    state = graph_app.get_state(
        config
    )


    messages = state.values.get(
        "messages",
        []
    )


    result = []


    for message in messages:

        # Only return user and AI messages

        if message.type not in [
            "human",
            "ai"
        ]:
            continue


        result.append({
            "type": message.type,
            "content": message.content
        })


    return {
        "thread_id": thread_id,
        "messages": result
    }


# ---------------------------------------------------------
# Chatbot
# ---------------------------------------------------------

@app.post("/chatbot")
async def chatbot_views(
    question: str = Form(...),
    thread_id: str = Form(...)
):

    return StreamingResponse(

        ask_question_to_bot(
            question,
            thread_id
        ),

        media_type="text/plain"
    )
