# CLAUDE.md

Anweisungen für Claude Code in diesem Repository.

## Sprache

- Code, Kommentare und Commit-Messages auf Englisch.
- PR-Beschreibungen und Release Notes auf Deutsch.

## Umgebung und Tests

- `manage.py` (Tests, Commands) nur im Conda-Env `tf` ausführen:
  `source ~/miniconda3/etc/profile.d/conda.sh && conda activate tf`.
  Im Basis-Env fehlen Abhängigkeiten, die Plugin-Tests werden dann stillschweigend übersprungen.
- Trainer-Tests: `python manage.py test trainers`. Echte Trainingsläufe mit `--tag slow`,
  dafür vorher `python manage.py export_school 8 --frames 200`.
- Code im Stil der umgebenden Dateien schreiben (2 Leerzeichen Einrückung, `return(x)`).

## Git und Pull Requests

- Jede Änderung auf einem Feature-Branch von `main`, dann PR mit `gh`.
- Der Benutzer merged die PRs selbst. Nicht selbst mergen.
- Auf „aufräumen“ nach dem Merge: `fetch --prune`, `main` per Fast-Forward aktualisieren,
  den gemergten Branch mit `git branch -d` löschen (vorher prüfen, dass er in `origin/main` ist).
  Remote-Branches löscht GitHub beim Merge automatisch.

## Plugins

- `plugins/*` ist im Hauptrepo ignoriert. Die Plugins sind eigene Repos unter github.com/ludgerh:
  `plugins/<name>` → `ludgerh/<name>` für `train_worker_gpu`, `cam_ai_hue`, `cam_ai_shelly`,
  `cam_ai_tasmota`, `cam_ai_proxy`, `cam_ai_proxy_agent`; außerdem
  `plugins/detectors/det_seagate_0001` → `ludgerh/det_seagate_0001` und
  `plugins/alarms/alarm_seagate_0001` → `ludgerh/alarm_seagate_0001`.
- Für Plugin-Repos immer `git -C <plugin-pfad>` und `gh --repo ludgerh/<plugin>` verwenden,
  nie `cd plugins/... && git ...` (Gefahr, im Hauptrepo zu committen).
- In Plugin-Verzeichnissen liegt oft uncommittete Arbeit des Benutzers. Nie mit stagen;
  hängt ein Fix davon ab, nachfragen.
- Tests für das GPU-Plugin liegen im Hauptrepo (`trainers/tests/`). Änderung und Test kommen
  daher als zwei PRs; der Test-PR wird nach dem Plugin-PR gemergt.
- Plugins haben keine Releases und werden auf den Zielrechnern von Hand aktualisiert.

## Releases

Nur das Hauptrepo bekommt GitHub-Releases. Ablauf, selbständig inklusive Wahl der Nummer:

1. Versions-PR: `camai/version.py` anpassen (`version = 'X.Y.Z'`, ohne `v`).
2. Nach dem Merge den Tag `vX.Y.Z` auf den Merge-Commit setzen und das GitHub-Release anlegen.

Zwei Arten von Versionen:

- **Vollversion** `vX.Y.Z` (z. B. `v2.2.2`): normales Release, „Latest“, ausführliche deutsche
  Release Notes (Hinweise zum Update und zu Migrationen zuerst).
- **Zwischenversion**: letzte Vollversion plus Kleinbuchstabe als Zähler (`v2.2.2a`, `v2.2.2b`, …),
  als GitHub-**Pre-release**. Die nächste Vollversion beendet die Buchstabenreihe.

Pre-releases bietet die Upgrade-Routine nicht automatisch an (sie fragt `releases/latest` ab).
Installiert werden sie über das Feld „Special version tag“ auf der Upgrade-Seite oder mit
`python cam-ai-setup.py --version vX.Y.Za`.

## Rechner

- **bequiet**: Testrechner mit guter GPU, bekommt Zwischenversionen für Trainingsläufe
  (z. B. `tune_school`). Interessante School dort: Nr. 25.
