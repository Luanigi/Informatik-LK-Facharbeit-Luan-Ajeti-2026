import time
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
import websocket
import json
import threading
import csv
from datetime import datetime

# --Konfiguration--
binance_api_key = "..." # Gebe ich raus auf Anfrage, da es sich um sensible Daten handelt
binance_api_secret = "..." # Gebe ich raus auf Anfrage, da es sich um sensible Daten handelt

client = Client(binance_api_key, binance_api_secret, testnet=True)

eingangs_spread = 0.010
profit_ziel = 0.012
exit_differenz = 0.04
min_halte_zeit = 5.0
quantitaet = 0.001
daten_datei = "daten.csv"

# --Globale Variablen--

kraken_preis = None
binance_preis = None
position_offen = False
kauf_preis = 0.0
kauf_zeit = 0.0
kauf_order_id = None
aktueller_profit = 0.0

# --CSV-Datei Header initialisieren--
with open(daten_datei, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([
        "Zeitstempel", "Kraken_Preis", "Binance_Preis", "Differenz", "Action",
        "Quantität", "Netto_Profit", "Haltezeit", "Kauf_Order_ID", "Verkauf_Order_ID"
    ])

def handel_protokollieren(action, netto_profit = 0, halte_zeit = 0, kauf_id = None, verkauf_id = None):
    with open(daten_datei, "a", newline="") as datei:
        writer = csv.writer(datei)
        writer.writerow([
            datetime.now().isoformat(), 
            kraken_preis, 
            binance_preis,
            ((kraken_preis - binance_preis)/binance_preis*100) if binance_preis and kraken_preis else 0,
            action,
            quantitaet if action in ['BUY', 'SELL'] else 0,
            netto_profit,
            halte_zeit,
            kauf_id,
            verkauf_id
        ])


# --Kraken Websocket--     
def bei_nachricht(ws, message):
    global kraken_preis
    try:
        data = json.loads(message)
        if isinstance(data, dict) and data.get('channel') == 'ticker':
            if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                ticker_item = data['data'][0]
                if 'last' in ticker_item:
                    kraken_preis = float(ticker_item['last'])
    except Exception as e:
        pass


def bei_verbindungsaufbau(ws):
    subscribe = {
        "method": "subscribe",
        "params": {
            "channel" : "ticker",
            "symbol" : ["BTC/USDT"]
        }
    }
    ws.send(json.dumps(subscribe))
    print("Mit Kraken Websocket verbunden.")

kraken_ws = websocket.WebSocketApp("wss://ws.kraken.com/v2",
                                   on_message=bei_nachricht,
                                   on_open=bei_verbindungsaufbau)

threading.Thread(target=kraken_ws.run_forever, daemon=True).start()


# --Binance REST--
def get_binance_preis():
    global binance_preis
    try:
        ticker = client.get_symbol_ticker(symbol="BTCUSDT")
        binance_preis = float(ticker['price'])
    except Exception as e:
        print(f"Fehler beim Abrufen des Binance Preises: {e}")
        binance_preis = None


print("Trading Bot gestartet. Warte auf Preisinformationen...")
start_zeit = time.time()

while True:
    try:
        get_binance_preis()

        if kraken_preis is None or binance_preis is None:
            time.sleep(2)
            continue

        preis_differenz = (kraken_preis - binance_preis) / binance_preis * 100
        print(f"Kraken: {kraken_preis:,.2f} | 
              Binance: {binance_preis:,.2f} | 
              Differenz: {preis_differenz:+.3f}% | 
              Position Offen: {position_offen} | 
              Laufzeit: {int((time.time() - start_zeit)/60)}min | 
              Aktueller Profit: {aktueller_profit:+.3f}%")

        if not position_offen:
            if preis_differenz > eingangs_spread:
                print(f"KAUF! Differenz: {preis_differenz:.3f}%")
                order = client.create_order(
                    symbol='BTCUSDT',
                    side=SIDE_BUY,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantitaet
                )
                kauf_preis    = binance_preis
                kauf_zeit     = time.time()
                kauf_order_id = order.get('orderId')
                position_offen = True
                handel_protokollieren('BUY', kauf_id=kauf_order_id)
                print("Kauf platziert:", order)
        else:
            haltedauer = time.time() - kauf_zeit
            aktueller_profit = (binance_preis - kauf_preis) / kauf_preis * 100

            if (aktueller_profit >= profit_ziel) or (preis_differenz <= exit_differenz and haltedauer >= min_halte_zeit):
                print(f"VERKAUF! Profit: {aktueller_profit:.3f}%, gehalten: {haltedauer:.1f}s")
                order = client.create_order(
                    symbol='BTCUSDT',
                    side=SIDE_SELL,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantitaet
                )
                brutto_gewinn = (binance_preis - kauf_preis) * quantitaet
                gebuehren = 0.00075 * (kauf_preis + binance_preis) * quantitaet * 2
                netto_profit = brutto_gewinn - gebuehren

                position_offen = False
                handel_protokollieren('SELL', netto_profit, haltedauer, kauf_order_id, order.get('orderId'))
                print("Verkauf platziert:", order, f"Netto Profit: {netto_profit:.4f} USDT")

        time.sleep(1.2)

        if time.time() - start_zeit > 7200:
            print("2 Stunden erreicht, Bot wird gestoppt.")
            break

    except Exception as e:
        print("Fehler:", e)
        time.sleep(5)
