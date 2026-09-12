"""WebSocket Live Test Script

Connects to ws://localhost:8000/ws/inbox, triggers a sample webhook,
and streams the live broadcast events to your console.
"""

import asyncio
import json
import httpx
import websockets

WS_URL = "ws://localhost:8000/ws/inbox"
API_URL = "http://localhost:8000/api/webhooks/meta"


async def trigger_sample_event():
    """Waits 1 second and then sends a simulated Instagram webhook."""
    await asyncio.sleep(1.0)
    print("\n[Simulator] Triggering simulated Instagram DM webhook...")
    async with httpx.AsyncClient() as client:
        res = await client.post(
            API_URL,
            json={
                "account_id": "acc_instagram_01",
                "sender_name": "Marcus Vance",
                "message_body": "Hello! How much is shipping for the vegan leather desk mat to Chicago?",
                "interaction_type": "DM"
            }
        )
        print(f"[Simulator] Webhook Ingested: HTTP {res.status_code} -> {res.json()['status']}\n")


async def listen_websocket():
    """Connects to the WebSocket and displays live broadcast frames."""
    print(f"[WebSocket] Connecting to {WS_URL}...")
    async with websockets.connect(WS_URL) as ws:
        print("[WebSocket] Connected successfully! Listening for live pipeline events...\n")

        # Start trigger in the background
        asyncio.create_task(trigger_sample_event())

        received_count = 0
        while received_count < 3:
            raw_msg = await ws.recv()
            data = json.loads(raw_msg)
            event_type = data.get("event")
            event_data = data.get("data", {})

            print(f"==================================================")
            print(f" EVENT RECEIVED: {event_type}")
            print(f" Status:  {event_data.get('status')}")
            if event_data.get("ai_reply"):
                print(f" AI Reply: {event_data.get('ai_reply')}")
                print(f" Sources:  {event_data.get('rag_sources')}")
            print(f"==================================================\n")

            received_count += 1
            if event_type == "INTERACTION_COMPLETED":
                break

        print("[WebSocket] Verification complete! All real-time events streamed successfully.")


if __name__ == "__main__":
    asyncio.run(listen_websocket())
