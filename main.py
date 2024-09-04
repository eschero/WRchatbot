import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import asyncio

# Inizializziamo l'app FastAPI
app = FastAPI()

# Impostiamo la chiave API e l'organizzazione
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.organization = os.getenv('OPENAI_ORG_ID')

# Carichiamo l'ID dell'assistente dalle variabili di ambiente
assistant_id = os.getenv('ASSISTANT_ID')

# Definiamo il modello di richiesta per la chat
class ChatRequest(BaseModel):
    thread_id: str
    message: str

# Inizializziamo una conversazione
@app.get('/start')
async def start_conversation():
    print("Starting a new conversation...")
    # Crea un nuovo thread con l'intestazione per usare Assistants v2
    thread = openai.Thread.create(headers={"OpenAI-Beta": "assistants=v2"})
    print(f"New thread created with ID: {thread['id']}")
    return {"thread_id": thread['id']}

# Gestiamo il messaggio di chat
@app.post('/chat')
async def chat(chat_request: ChatRequest):
    thread_id = chat_request.thread_id
    user_input = chat_request.message

    # Controlliamo che l'ID della conversazione sia stato fornito
    if not thread_id:
        raise HTTPException(status_code=400, detail="Missing thread_id")

    print(f"Received message: {user_input} for thread ID: {thread_id}")

    # Inseriamo il messaggio dell'utente nella conversazione
    openai.ThreadMessage.create(
        thread_id=thread_id,
        role="user",
        content=user_input,
        headers={"OpenAI-Beta": "assistants=v2"}
    )

    # Creiamo la run per l'assistente
    run = openai.ThreadRun.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        headers={"OpenAI-Beta": "assistants=v2"}
    )
  
    end = False

    # Loop per controllare lo stato della run
    while not end:
        run_status = openai.ThreadRun.retrieve(
            thread_id=thread_id,
            run_id=run['id'],
            headers={"OpenAI-Beta": "assistants=v2"}
        )
        print(f"Run status: {run_status['status']}")

        # Gestione dello stato della run
        if run_status['status'] in ['completed', 'cancelling', 'requires_action', 'cancelled', 'expired', 'failed']:
            end = True

        await asyncio.sleep(1)

    # Recuperiamo i messaggi della conversazione
    messages = openai.ThreadMessage.list(
        thread_id=thread_id,
        headers={"OpenAI-Beta": "assistants=v2"}
    )
    response = messages['data'][0]['content'][0]['text']['value']
  
    print(f"Assistant response: {response}")

    return {"response": response}
