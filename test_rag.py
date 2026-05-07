import asyncio
import websockets
import json

async def test_rag():
    uri = "ws://localhost:8000/chat/stream"
    async with websockets.connect(uri) as websocket:
        # Send RAG query
        message = {
            "text": "What does the document say about persistence and testing?",
            "rag": True
        }
        await websocket.send(json.dumps(message))
        
        # Receive response
        response = ""
        try:
            while True:
                token = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                response += token
                print(token, end='', flush=True)
        except asyncio.TimeoutError:
            pass
        
        print("\n\n--- Full Response ---")
        print(response[:500])
        
        # Check if document was retrieved
        if "Retrieving Documents" in response or "test_persist.md" in response:
            print("\n✓ Document was RETRIEVED and used in RAG!")
        else:
            print("\n✗ Document was NOT retrieved")

asyncio.run(test_rag())
