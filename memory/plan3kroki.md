
# Plan działania (3 pod-kroki)

## 1. Ujednolicenie formatu wyniku agenta
* Każdy agent będzie zwracał z run() obiekt możliwy do serializacji (np. dict, list, str).
* Jeśli agent nic nie zwraca (np. dotychczasowy HelloAgent), dopisujemy zwrot wartości (np. "Hello, world!") przy jednoczesnym wypisaniu na ekran.
## 2. Opcja CLI --output PATH (JSON)
* Rozszerzamy komendę run w src/main.py o opcję --output PATH.
* Po zakończeniu run(), jeśli wynik jest różny od None i podano --output, zapisujemy go do JSON:
'
with open(output, "w", encoding="utf-8") as f:
         json.dump(result, f, ensure_ascii=False, indent=2)
'
* W razie błędów serializacji (np. obiekt nie-JSON-owalny) informujemy użytkownika.
## 3. Aktualizacja HelloAgent i testu
* HelloAgent.run(): zwraca "Hello, world!" i wciąż wypisuje tekst.
* W tests/test_agents.py dodajemy sprawdzenie, że wynik jest poprawny i że zapis do pliku działa.