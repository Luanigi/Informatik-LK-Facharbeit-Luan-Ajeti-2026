import asyncio
import websockets
import time
import json
from datetime import datetime
import requests

# --Konfiguration--
WS_URL = "wss://ws.kraken.com/v2"
REST_URL = "https://api.kraken.com/0/public/Time"
PING_INTERVAL = 2.0
MAX_MEASUREMENTS = 100

# --WebSocket Latenz Messung--
async def measure_websocket_latency():
    measurements = []
    
    print(f"Verbinde mit WebSocket: {WS_URL}")
    print(f"Starte Messung von {MAX_MEASUREMENTS} Pings (Intervall: {PING_INTERVAL}s)\n")
    
    try:
        async with websockets.connect(WS_URL, ping_interval=None) as ws:
            print("Verbunden! Warte auf erste Antwort...\n")
            
            for i in range(MAX_MEASUREMENTS):
                send_time = time.perf_counter_ns()
                send_datetime = datetime.utcnow().isoformat()
                
                # Kraken Ping-Format
                ping_msg = json.dumps({"method": "ping"})
                
                await ws.send(ping_msg)
                
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    recv_time = time.perf_counter_ns()
                    
                    rtt_ns = recv_time - send_time
                    rtt_ms = rtt_ns / 1_000_000
                    
                    measurements.append(rtt_ms)
                    
                    print(f"WS [{i+1:2d}] {send_datetime} | RTT: {rtt_ms:8.3f} ms")
                    print(f"Antwort: {response.strip()[:80]}...")
                    print("-" * 60)
                    
                except asyncio.TimeoutError:
                    print(f"WS [{i+1:2d}] Timeout. keine Antwort innerhalb von 5 Sekunden")
                    break
                
                await asyncio.sleep(PING_INTERVAL)
                
    except Exception as e:
        print(f"WebSocket Fehler: {e}")
    
    # --Zusammenfassung WebSocket--
    if measurements:
        print("\n" + "="*60)
        print("WebSocket Zusammenfassung:")
        print(f"Anzahl Messungen: {len(measurements)}")
        print(f"Durchschnitt RTT: {sum(measurements)/len(measurements):.3f} ms")
        print(f"Minimum RTT: {min(measurements):.3f} ms")
        print(f"Maximum RTT: {max(measurements):.3f} ms")
        print(f"Median RTT: {sorted(measurements)[len(measurements)//2]:.3f} ms")
        print("="*60 + "\n")
    
    return measurements


# --Kraken Latenz Messung--
def measure_rest_latency():
    measurements = []
    
    print(f"Starte REST API Messung gegen: {REST_URL}")
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
            print(f"REST[{i+1:2d}] Timeout – keine Antwort innerhalb von 5 Sekunden")
            break
        except Exception as e:
            print(f"REST[{i+1:2d}] Fehler: {e}")
            break
        
        time.sleep(PING_INTERVAL)
    
    # --Zusammenfassung REST--
    if measurements:
        print("\n" + "="*60)
        print("REST API Zusammenfassung:")
        print(f"Anzahl Messungen: {len(measurements)}")
        print(f"Durchschnittliche Paketumlaufzeit: {sum(measurements)/len(measurements):.3f} ms")
        print(f"Minimum Paketumlaufzeit: {min(measurements):.3f} ms")
        print(f"Maximum Paketumlaufzeit: {max(measurements):.3f} ms")
        print(f"Median Paketumlaufzeit:  {sorted(measurements)[len(measurements)//2]:.3f} ms")
        print("="*60)
    
    return measurements


if __name__ == "__main__":
    print("WebSocket + REST Latency Messung für Kraken\n")
    print("-----------------------------------------\n")
    
    # WebSocket Test
    ws_measurements = asyncio.run(measure_websocket_latency())
    
    # Direkt danach REST Test
    print("\n\nWechsle nun zum REST API Test...\n")
    rest_measurements = measure_rest_latency()
    
    print("\nBeide Tests abgeschlossen.")
