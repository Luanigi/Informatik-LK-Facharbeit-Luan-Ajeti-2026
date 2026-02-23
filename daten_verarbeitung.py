import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# --Konfiguration--
csv_datei = "daten.csv"
diagramm_groesse = (12, 6)
speicher_pfad = "."

# --Daten einlesen--
print("Lese Daten aus CSV-Datei...")

try:
    daten = pd.read_csv(csv_datei)
    print(f"Daten erfolgreich eingelesen. {len(daten)} Zeilen gefunden.")
except FileNotFoundError:
    print(f"Fehler: Die Datei '{csv_datei}' wurde nicht gefunden.")
    exit()

daten["Zeitstempel"] = pd.to_datetime(daten["Zeitstempel"]) # Zeitstempel in datetime-Objekt umwandeln

# Action wird nochmal geteilt in Buy und Sell
kaeufe = daten[daten['Action'] == 'BUY'].copy()
verkaeufe = daten[daten['Action'] == 'SELL'].copy()

# Anzahl Roundtrips = Anzahl SELL-Zeilen (angenommen jeder BUY hat einen SELL)
n_roundtrips = len(verkaeufe)

print("\n" + "="*60)
print("ZUSAMMENFASSUNG DER ARBITRAGE-ERGEBNISSE")
print("="*60)

# --Allgemeine Daten Ausgabe in der Konsole--
print(f"Anzahl ausgeführter Round-Trips (BUY+SELL): {n_roundtrips}")
print(f"Anzahl BUY-Einstiege: {len(kaeufe)}")
print(f"Anzahl SELL-Ausstiege: {len(verkaeufe)}")

if n_roundtrips > 0:
    total_profit = verkaeufe['Netto_Profit'].sum()
    avg_profit = verkaeufe['Netto_Profit'].mean()
    median_profit = verkaeufe['Netto_Profit'].median()
    win_rate = (verkaeufe['Netto_Profit'] > 0).mean() * 100

    print(f"Gesamter Netto-Profit (alle Trades):{total_profit:,.4f} USDT")
    print(f"Durchschnittlicher Profit pro Trade: {avg_profit:,.4f} USDT")
    print(f"Median Profit pro Trade: {median_profit:,.4f} USDT")
    print(f"Gewinnquote (positive Trades): {win_rate:.1f} %")

    # Haltezeiten (nur SELL-Zeilen)
    avg_hold = verkaeufe['Haltezeit'].mean()
    median_hold = verkaeufe['Haltezeit'].median()
    max_hold = verkaeufe['Haltezeit'].max()
    min_hold = verkaeufe['Haltezeit'].min()

    print(f"Durchschnittliche Haltezeit: {avg_hold:.1f} Sekunden")
    print(f"Median Haltezeit: {median_hold:.1f} Sekunden")
    print(f"Längste Haltezeit: {max_hold:.1f} Sekunden")
    print(f"Kürzeste Haltezeit: {min_hold:.1f} Sekunden")

    # Preisdifferenzen beim Einstieg
    avg_entry_diff = kaeufe['Differenz'].mean()
    max_entry_diff = kaeufe['Differenz'].max()
    min_entry_diff = kaeufe['Differenz'].min()
    print(f"Durchschnittliche Diff beim Einstieg: {avg_entry_diff:.3f} %")
    print(f"Maximale Diff beim Einstieg: {max_entry_diff:.3f} %")
    print(f"Minimale Diff beim Einstieg: {min_entry_diff:.3f} %")

else:
    print("Keine abgeschlossenen Trades gefunden (keine SELL-Zeilen).")


# --Diagramme--
sns.set_style("whitegrid")

# Differenz beim Kauf (BUY)
plt.figure(figsize=diagramm_groesse)
sns.histplot(data=kaeufe, x='Differenz', bins=25, kde=True, color='orange')
plt.title('Verteilung der Preisdifferenz beim Einstieg (BUY)', fontsize=14)
plt.xlabel('Diff % (Kraken - Binance)', fontsize=12)
plt.ylabel('Anzahl Trades', fontsize=12)
plt.tight_layout()
plt.savefig(f'{speicher_pfad}/diff_bei_entry.png', dpi=150)
plt.close()

# Haltezeit vs. Netto Profit
if n_roundtrips > 0:
    plt.figure(figsize=diagramm_groesse)
    sns.scatterplot(data=verkaeufe, x='Haltezeit', y='Netto_Profit', 
                    hue='Netto_Profit', palette='RdYlGn', size='Netto_Profit', sizes=(30, 150))
    plt.axhline(0, color='black', linestyle='--', alpha=0.5)
    plt.title('Haltezeit vs. Netto-Profit pro Trade', fontsize=14)
    plt.xlabel('Haltezeit (Sekunden)', fontsize=12)
    plt.ylabel('Netto-Profit (USDT)', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{speicher_pfad}/holdtime_vs_profit.png', dpi=150)
    plt.close()

# Profit pro Trade
if n_roundtrips > 0:
    plt.figure(figsize=diagramm_groesse)
    verkaeufe['Trade_Nr'] = range(1, len(verkaeufe) + 1)
    sns.barplot(data=verkaeufe, x='Trade_Nr', y='Netto_Profit', palette='RdYlGn')
    plt.axhline(0, color='black', linestyle='--', alpha=0.5)
    plt.title('Netto-Profit pro abgeschlossenem Trade', fontsize=14)
    plt.xlabel('Trade-Nummer', fontsize=12)
    plt.ylabel('Netto-Profit (USDT)', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{speicher_pfad}/profit_pro_trade.png', dpi=150)
    plt.close()

print("\nDiagramme wurden gespeichert:")