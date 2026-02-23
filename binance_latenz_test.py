import asyncio
import websockets
import time
import json
from datetime import datetime
import requests

# --Konfiguration--
WS_URL = "wss://stream.binance.com:9443/ws"
REST_URL = "https://api.binance.com/api/v3/time"
PING_INTERVAL = 2.0
MAX_MEASUREMENTS = 100
STREAM_NAME = "btcusdt@trade"

# --WebSocket Latenz Messung--
async def measure_binance_websocket_latency():
    measurements = []
    
    print(f"Verbinde mit Binance WebSocket: {WS_URL}")
    print(f"Starte Messung von {MAX_MEASUREMENTS} RTTs via Subscribe/Unsubscribe (Intervall: {PING_INTERVAL}s)\n")  # RTT = Round Trip Time = Paketumlaufzeit
    
    try:
        async with websockets.connect(WS_URL, ping_interval=None) as ws:
            print("Verbunden! Starte Messungen...\n")
            
            for i in range(MAX_MEASUREMENTS):
                send_time = time.perf_counter_ns()
                send_datetime = datetime.utcnow().isoformat()
                
                # Subscribe-Nachricht
                sub_msg = json.dumps({
                    "method": "SUBSCRIBE",
                    "params": [STREAM_NAME],
                    "id": 100 + i
                })
                
                await ws.send(sub_msg)
                
                try:
                    res = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    recv_time = time.perf_counter_ns()
                    
                    rtt_ns = recv_time - send_time
                    rtt_ms = rtt_ns / 1_000_000
                    
                    measurements.append(rtt_ms)
                    
                    print(f"WS [{i+1:2d}] {send_datetime} | RTT: {rtt_ms:8.3f} ms")
                    print(f"Antwort: {res.strip()[:80]}...")
                    print("-" * 60)
                    
                except asyncio.TimeoutError:
                    print(f"WS [{i+1:2d}] Timeout. keine Antwort innerhalb 5s")
                    break
                
                # Sofort unsubscriben, um Streamlimit zu vermeiden
                unsub_msg = json.dumps({
                    "method": "UNSUBSCRIBE",
                    "params": [STREAM_NAME],
                    "id": 200 + i
                })
                await ws.send(unsub_msg)
                await asyncio.sleep(PING_INTERVAL)
                
    except Exception as e:
        print(f"WebSocket Fehler: {e}")
    
    # --Zusammenfassung WebSocket--
    if measurements:
        print("\n" + "="*60)
        print("Binance WebSocket Zusammenfassung:")
        print(f"Anzahl Messungen: {len(measurements)}")
        print(f"Durchschnitt RTT: {sum(measurements)/len(measurements):.3f} ms")
        print(f"Minimum RTT: {min(measurements):.3f} ms")
        print(f"Maximum RTT: {max(measurements):.3f} ms")
        print(f"Median RTT: {sorted(measurements)[len(measurements)//2]:.3f} ms")
        print("="*60 + "\n")
    
    return measurements


# --REST Latenz Messung--
def measure_binance_rest_latency():
    measurements = []
    
    print(f"Starte Binance REST API Messung: {REST_URL}")
    print(f"{MAX_MEASUREMENTS} Anfragen (Intervall: {PING_INTERVAL}s)\n")
    
    session = requests.Session()
    
    for i in range(MAX_MEASUREMENTS):
        send_time = time.perf_counter_ns()
        send_datetime = datetime.utcnow().isoformat()
        
        try:
            response = session.get(REST_URL, timeout=5.0)
            recv_time = time.perf_counter_ns()
            
            rtt_ns = recv_time - send_time
            rtt_ms = rtt_ns / 1_000_000
            
            measurements.append(rtt_ms)
            
            resp_text = response.text[:80] + "..." if len(response.text) > 80 else response.text
            
            print(f"REST[{i+1:2d}] {send_datetime} | RTT: {rtt_ms:8.3f} ms  | HTTP {response.status_code}")
            print(f"    Antwort: {resp_text}")
            print("-" * 60)
            
        except requests.Timeout:
            print(f"REST[{i+1:2d}] Timeout. keine Antwort innerhalb von 5 Sekunden")
            break
        except Exception as e:
            print(f"REST[{i+1:2d}] Fehler: {e}")
            break
        
        time.sleep(PING_INTERVAL)
    
    # --Zusammenfassung REST--
    if measurements:
        print("\n" + "="*60)
        print("Binance REST API Zusammenfassung:")
        print(f"Anzahl Messungen: {len(measurements)}")
        print(f"Durchschnitt RTT: {sum(measurements)/len(measurements):.3f} ms")
        print(f"Minimum RTT: {min(measurements):.3f} ms")
        print(f"Maximum RTT: {max(measurements):.3f} ms")
        print(f"Median RTT: {sorted(measurements)[len(measurements)//2]:.3f} ms")
        print("="*60)
    
    return measurements


if __name__ == "__main__":
    print("WebSocket + REST Latency Messung für Binance\n")
    print("----------------------------------------------------\n")
    
    # --WebSocket Test--
    ws_meas = asyncio.run(measure_binance_websocket_latency())
    
    # --Danach REST Test--
    print("\n\nWechsle nun zum Binance REST API Test...\n")
    rest_meas = measure_binance_rest_latency()
    
    print("\nBeide Tests abgeschlossen.")
