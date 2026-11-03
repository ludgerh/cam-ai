# CLAUDE.md

Anweisungen für Claude Code in diesem Repository.

## Sprache

- Code, Kommentare, Docstrings, Commit-Messages und Release Notes auf Englisch.
- PR-Beschreibungen auf Deutsch.

## Umgebung und Tests

- `manage.py` (Tests, Commands) nur im Conda-Env `tf` ausführen:
  `source ~/miniconda3/etc/profile.d/conda.sh && conda activate tf`.
  Im Basis-Env fehlen Abhängigkeiten, die Plugin-Tests werden dann stillschweigend übersprungen.
- Trainer-Tests: `python manage.py test trainers`. Echte Trainingsläufe mit `--tag slow`,
  dafür vorher `python manage.py export_school 8 --frames 200`.

## Code-Stil

- Code im Stil der umgebenden Dateien schreiben.
- Einrückung mit 2 Leerzeichen, in Python und in Django-Templates. Keine Tabs.
- Maximale Zeilenlänge: 90 Zeichen.
- String-Konstanten in einfachen Anführungszeichen: `'text'`, nicht `"text"`.
- `return` immer mit Klammern: `return(x)`.
- Klassendefinitionen immer mit Klammern, auch ohne Basisklasse: `class model_buffer():`.
- Benennung wie im umgebenden Code; Klassen meist klein geschrieben (z. B. `tf_worker`, `trainer`).

## Dateikopf

Bei jeder Änderung an einer Datei den Kopf prüfen und bei Bedarf anpassen:

- **Pfad**: Ganz am Anfang des ersten Kommentars steht der Pfad der Datei relativ zum
  Repo-Root (bei Plugins relativ zum Plugin-Repo). Fehlt er oder stimmt er nicht mehr
  (z. B. nach Verschieben), korrigieren.
  - Python: eigene Zeile `# pfad/datei.py` vor dem Lizenz-Docstring
    (nach einer Shebang-Zeile, falls vorhanden).
  - JS/CSS: erste Zeile innerhalb des `/* ... */`.
  - Django-Templates: erste Zeile innerhalb des `{% comment %}`.
  - Dateien ohne Kopfkommentar bekommen nur die Pfadzeile im passenden Kommentarstil.
- **Jahreszahl**: Enthält die Copyright-Zeile (`by the CAM-AI team` oder
  `Ludger Hellerhoff`) das aktuelle Jahr nicht, auf einen Bereich bis zum aktuellen
  Jahr erweitern: `2024` → `2024-2026`, `2024-2025` → `2024-2026`.
  Fremde Copyrights (z. B. in `LICENSE`) nie ändern.
- Nur Dateien anfassen, die ohnehin geändert werden. Keine Massenaktualisierung.

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
  `plugins/detectors/det_seagate_0001` → `ludgerh/det_seagate_0001`,
  `plugins/alarms/alarm_seagate_0001` → `ludgerh/alarm_seagate_0001` und
  `plugins/views/view_seagate_0001` → `ludgerh/view_seagate_0001`.
- Für Plugin-Repos immer `git -C <plugin-pfad>` und `gh --repo ludgerh/<plugin>` verwenden,
  nie `cd plugins/... && git ...` (Gefahr, im Hauptrepo zu committen).
- In Plugin-Verzeichnissen liegt oft uncommittete Arbeit des Benutzers. Nie mit stagen;
  hängt ein Fix davon ab, nachfragen.
- Tests für das GPU-Plugin liegen im Hauptrepo (`trainers/tests/`). Änderung und Test kommen
  daher als zwei PRs; der Test-PR wird nach dem Plugin-PR gemergt.
- Plugins haben keine Releases und werden auf den Zielrechnern von Hand aktualisiert.

## View-Plugins erstellen

View-Plugins (Typ `'V'`) liefern eigene Seiten, erreichbar über das Menü **Views**.
Anders als Detector und Alarm haben sie keinen Default, und es können 0 bis beliebig
viele gleichzeitig aktiv sein. Vorlage ist `plugins/views/view_seagate_0001`.

1. **Repo anlegen:** privates Repo `ludgerh/<name>` (`gh repo create --private`), lokal
   unter `plugins/views/<name>` mit Branch `main` und Remote `origin`. `.gitignore` wie
   bei den anderen Plugins (`__pycache__/`, `*~`, `*.c`, `*.so`). Das Repo in die
   Plugin-Liste oben eintragen. `plugins/views/` ist im Hauptrepo komplett ignoriert.
2. **Dateien:** leere `__init__.py` und `plugin.py` mit der Klasse `plugin`:

   ```python
   # plugin.py
   """
   Copyright (C) 2026 by CAM-AI Soluvis GmbH, info@cam-ai.de
   All rights reserved
   """

   from camai.version import version
   from core.plugin_templates import view_plugin

   class plugin(view_plugin):
     type = 'V'
     name = 'Seagate Custom View Plugin #1'
     version = version
     maker = 'CAM-AI Soluvis GmbH'
     copyright = 'All rights reserved'

     def view(self, request):
       return(self.render(request, 'templates/view.html', {'plugin' : self}))
   ```

   `type`, `name`, `version`, `maker`, `copyright` und `description` landen bei der
   Registrierung in der Datenbank (`core.models.plugin`); `description` erbt sonst den
   Platzhalter aus `temp_plugin`.
3. **View:** `view(self, request)` gibt eine `HttpResponse` zurück. Ohne eigene Methode
   antwortet die Seite mit 404. Der View läuft synchron, Datenbankzugriffe sind dort
   erlaubt. Zugriff nur für angemeldete Benutzer (URL `/views/<plugin_id>/`).
4. **Templates:** `self.render(request, template_file, context)` rendert eine Datei
   relativ zum Plugin-Verzeichnis mit dem Kontext des Hauptmenüs
   (`view_plugin.menu_context`). Das Template erweitert `main/basis.html` und füllt
   `{% block content %}`. `{% extends %}`/`{% include %}` finden nur Templates des
   Hauptrepos, keine weiteren Plugin-Dateien. Kopf: `{% comment %}` mit Pfad
   (`templates/view.html`) und Copyright.
5. **Registrierung:** `core/plugin_conf.py` liest `plugins/views/*/plugin.py` (oder eine
   kompilierte `.so`) beim Serverstart ein; Verzeichnisse ohne Plugin werden übersprungen.
   Das Menü **Views** erscheint, sobald mindestens ein View-Plugin registriert ist.
   Neue Plugins und Code-Änderungen wirken erst nach einem Neustart (Menüliste und
   geladene Module werden beim Start gebildet bzw. gecacht).
6. **Achtung Plugin-ID:** Fehlt das Verzeichnis bei einem Start, löscht `remove_missing`
   den Datenbankeintrag. Taucht es wieder auf, bekommt es eine neue ID, alte Links auf
   `/views/<id>/` sind dann ungültig.
7. **Testen** ohne laufenden Server: URLs werden nur unter `runserver`/`gunicorn` geladen
   und `access` nur dort initialisiert. Im `manage.py shell` daher
   `from access.c_access import initialize; initialize()`, dann `core.views.plugin_view`
   mit einer `RequestFactory`-Anfrage (gültigen `HTTP_HOST` aus `ALLOWED_HOSTS` setzen)
   und einem angemeldeten Benutzer aufrufen.

## Releases

Nur das Hauptrepo bekommt GitHub-Releases. Ablauf, selbständig inklusive Wahl der Nummer:

1. Versions-PR: `camai/version.py` anpassen (`version = 'X.Y.Z'`, ohne `v`).
2. Nach dem Merge den Tag `vX.Y.Z` auf den Merge-Commit setzen und das GitHub-Release anlegen.

Zwei Arten von Versionen:

- **Vollversion** `vX.Y.Z` (z. B. `v2.2.2`): normales Release, „Latest“, ausführliche englische
  Release Notes (Hinweise zum Update und zu Migrationen zuerst).
- **Zwischenversion**: letzte Vollversion plus Kleinbuchstabe als Zähler (`v2.2.2a`, `v2.2.2b`, …),
  als GitHub-**Pre-release**. Die nächste Vollversion beendet die Buchstabenreihe.

Pre-releases bietet die Upgrade-Routine nicht automatisch an (sie fragt `releases/latest` ab).
Installiert werden sie über das Feld „Special version tag“ auf der Upgrade-Seite oder mit
`python cam-ai-setup.py --version vX.Y.Za`.

## Rechner

- **bequiet**: Testrechner mit guter GPU, bekommt Zwischenversionen für Trainingsläufe
  (z. B. `tune_school`). Interessante School dort: Nr. 25.
