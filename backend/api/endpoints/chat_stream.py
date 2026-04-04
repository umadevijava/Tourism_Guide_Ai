from fastapi import APIRouter, Response, WebSocket, WebSocketDisconnect

from backend.api.deps import ChatHistoryDep, LamaCppClientDep, VectorDatabaseDep
from backend.api.services.chat_stream import stream_chat_response, stream_rag_response
from backend.schemas.chat import ChatRequest
from chatbot.helpers.log import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.delete(
    path="/chat/history",
    status_code=204,
)
async def clear_chat_history(chat_history: ChatHistoryDep):
    """Clear the server-side chat history."""
    chat_history.clear()
    return Response(status_code=204)


@router.websocket(
    path="/chat/stream",
)
async def chat_stream(
    websocket: WebSocket
):
    """WebSocket endpoint for streaming chat responses token by token."""
    try:
        await websocket.accept()
        logger.info("✓ WebSocket connection accepted")
        
        while True:
            try:
                data = await websocket.receive_json()
                logger.info(f"Received message: {data}")
                
                # Get dependencies
                from backend.api.deps import get_llm_client, get_chat_history, get_index
                
                llm_gen = get_llm_client()
                llm_client = next(llm_gen)
                
                chat_gen = get_chat_history()
                chat_history = next(chat_gen)
                
                index_gen = get_index()
                index = next(index_gen)
                
                # Process request
                if data.get('rag', False):
                    await stream_rag_response(websocket, llm_client, ChatRequest(**data), chat_history, index)
                else:
                    await stream_chat_response(websocket, llm_client, ChatRequest(**data), chat_history)
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                await websocket.send_json({"error": str(e)})
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
