# DORA Metrics Scripts — Logiche, Ipotesi e Conteggi

Questo documento spiega **come funziona ogni script**, quali ipotesi applica e come vengono calcolati i numeri. Utile prima di presentare i risultati a un team o a un cliente.

---

## Prerequisiti comuni

Tutti gli script condividono lo stesso pattern di autenticazione e gli stessi argomenti di base:

```text
--org       https://dev.azure.com/<organizzazione>
--project   <nome progetto>
--pat       <Personal Access Token>
--from-date YYYY-MM-DD  (opzionale)
--to-date   YYYY-MM-DD  (opzionale)
```

**Autenticazione:** PAT base64-encoded nell'header `Authorization: Basic`. Il PAT deve avere i permessi `Read` su Environments, Build e Work Items.

**Finestra temporale:** `--from-date` e `--to-date` definiscono il periodo. Se omessi, gli script non filtrano per data. Il rate usa 30 giorni come finestra di default se le date non sono specificate.

**API version:** tutti gli endpoint usano `api-version: 7.1`.

---

## Metric 1 — Deployment Frequency (`dora_deployment_frequency.py`)

Misura quante volte il team porta codice in produzione nell'unità di tempo (giorno / settimana). Parametro aggiuntivo: `--env-keyword` (default: `production`).

### Definizione di deployment

Un deployment è un record nel registro dell'**Azure DevOps Environment** il cui nome contiene il keyword configurato, con `result = succeeded`. Vengono contati solo i successi per il rate DORA; i tentativi totali (succeeded + failed) sono esposti separatamente per il CFR.

La fonte di verità è l'API degli Environments di Azure DevOps, non il nome delle pipeline:

```text
GET {org}/{project}/_apis/distributedtask/environments
GET {org}/{project}/_apis/distributedtask/environments/{id}/environmentdeploymentrecords
```

Questa API registra ogni esecuzione di un `deployment` job YAML che referenzia quell'environment. Esempio di YAML che genera un record:

```yaml
stages:
  - stage: deploy_prod
    jobs:
      - deployment: deploy
        environment: production   # matchato con --env-keyword
        strategy:
          runOnce:
            deploy:
              steps: [...]
```

Il filtro è case-insensitive sul nome dell'environment. Con keyword `production`: `production`, `production-eu`, `api-production`. Con keyword `prod`: `prod`, `prod-us`, `production`.

### Conteggio e rate

Record esclusi: `result in {canceled, skipped, abandoned}` — non rappresentano un tentativo reale.

```text
total_deployments = count(result == "succeeded")
total_attempted   = count(result in {"succeeded", "failed"})

per_day  = total_deployments / period_days
per_week = per_day * 7
```

`period_days` è la differenza in giorni tra `--to-date` (23:59:59) e `--from-date` (00:00:00), minimo 1 giorno. Il timestamp usato è `record.finishTime`.

### Classificazione DORA — Deployment Frequency

| Livello | Soglia (deploy/giorno) |
| --- | --- |
| Elite | >= 1 |
| High | >= 1/7 (almeno uno a settimana) |
| Medium | >= 1/30 (almeno uno al mese) |
| Low | < 1/30 |

### Ipotesi e limitazioni — Deployment Frequency

- Il deployment job YAML deve referenziare un `environment:` con il keyword nel nome. Pipeline classiche o job normali (non `deployment`) non generano record in questa API.
- Se l'environment non esiste o non ha record, lo script stampa gli environment disponibili su stderr.
- La paginazione usa il `continuationToken` restituito nel body della risposta.

---

## Metric 2 — Lead Time for Changes (`dora_lead_time.py`)

Misura il tempo medio tra il primo commit incluso in un deployment e il momento in cui il deployment termina in produzione. Parametro aggiuntivo: `--env-keyword` (default: `production`).

### Fonte dei dati — Lead Time

I deployment di produzione vengono identificati con lo stesso meccanismo del Metric 1 (Environments API). Per ogni deployment `succeeded`, il `build_id` viene estratto dal campo `record.owner.id`. Quel `build_id` è l'ID del pipeline run e viene usato per recuperare i commit:

```text
GET {org}/{project}/_apis/build/builds/{build_id}/changes
```

Azure DevOps restituisce i commit inclusi in quel build che non erano presenti nel build precedente della stessa definition. Il campo `timestamp` di ogni commit corrisponde alla author date Git.

### Formula — Lead Time

```text
lead_time_per_deploy = record.finishTime - min(commit.timestamp)

avg_lead_time = mean(lead_time_per_deploy) su tutti i deploy nel periodo
```

**Calcolo step-by-step:**

1. Recupera gli environment deployment records per gli environment che matchano il keyword
2. Filtra solo i record con `result = succeeded` e `finishTime` nel periodo
3. Per ogni record: estrae `owner.id` come `build_id`, chiama `builds/{build_id}/changes`, prende `min(commit.timestamp)`
4. Calcola `delta = finishTime - min_commit_date` in ore; scarta se `delta < 0`
5. Calcola media e mediana sui campioni validi

### Classificazione DORA — Lead Time

| Livello | Soglia |
| --- | --- |
| Elite | < 1 ora |
| High | < 168 ore (1 settimana) |
| Medium | < 720 ore (1 mese) |
| Low | >= 720 ore |

La classificazione avviene sulla **media**. La **mediana** è fornita come dato aggiuntivo — con outlier (commit dimenticati per mesi) è più rappresentativa.

### Ipotesi e limitazioni — Lead Time

- **Author date vs committer date:** la `timestamp` del commit è la author date. Con squash merge o rebase può essere molto più vecchia della data di merge — questo gonfia il lead time. Se il team usa squash merge sistematicamente, preferire la mediana.
- **Granularità per deployment:** il punto di partenza è il commit più vecchio del batch, non la data media. Con build che accumulano commit di più sprint, il valore è sovrastimato.
- **Deployment senza commit:** pipeline avviati manualmente senza source code changes non hanno commit e vengono esclusi dal campione.
- **Una chiamata API per deployment:** con 100 deployment, lo script fa 100 chiamate HTTP aggiuntive.

---

## Metric 3 — Change Failure Rate (`dora_change_failure_rate.py`)

Misura la percentuale di deployment di produzione che hanno causato un incidente nelle 24 ore successive. Parametri aggiuntivi: `--env-keyword` (default: `production`), `--incident-tag` (default: `production-incident`).

### Definizione di incidente — CFR

Un incidente è un Work Item di tipo `Bug` o `Incident` con il tag `production-incident`, creato durante la finestra temporale (estesa di 24 ore).

### Definizione di deployment per il CFR

Per il CFR si contano **tutti i tentativi non-annullati** (succeeded + failed). La logica è che anche un deployment fallito può aver causato un'interruzione parziale. Il denominatore è `total_attempted`, non `total_succeeded`.

### Formula — CFR

```text
CFR = incidents_linked / total_deployment_attempts
```

**Query WIQL:**

```sql
SELECT [System.Id], [System.CreatedDate]
FROM WorkItems
WHERE [System.WorkItemType] IN ('Bug', 'Incident')
AND [System.Tags] CONTAINS 'production-incident'
AND [System.CreatedDate] >= '<from_date>'
AND [System.CreatedDate] <= '<to_date + 24h>'
```

### Algoritmo di linking — CFR

Per ogni deployment (ordinato per `finishTime`), lo script cerca incidenti con `CreatedDate` in `[deployment.finishTime, deployment.finishTime + 24h]`. Ogni incidente viene linkato al primo deployment che lo cattura (deduplicazione).

Il CFR conta il **numero di incidenti linkati** (non il numero di deployment con almeno un incidente). Un deployment con 3 incidenti contribuisce 3 al numeratore — più conservativo.

### Classificazione DORA — CFR

| Livello | Soglia CFR |
| --- | --- |
| Elite | <= 15% |
| High | <= 30% |
| Low | > 30% |

DORA 2023 collassa Medium e Low nella stessa fascia (>30%). Lo script usa "Low" per entrambi.

### Ipotesi e limitazioni — CFR

- **Correlazione temporale ≠ causalità:** un incidente aperto il giorno dopo un deployment è *assunto* come causato da quel deployment. La finestra di 24h è configurabile nel codice (`timedelta(hours=24)`).
- **Dipende dalla disciplina di tagging:** senza `production-incident` applicato sistematicamente, il CFR sarà artificialmente basso.
- **Tipi di work item:** cerca solo `Bug` e `Incident`. Tipi custom non vengono inclusi — modificare la WIQL nel codice se necessario.
- **Cap a 200 work items:** il batch per i dettagli gestisce al massimo 200 items. Limite noto per progetti molto attivi.

---

## Metric 4 — MTTR (`dora_mttr.py`)

Misura il tempo medio necessario al team per ripristinare il servizio dopo un incidente in produzione. Parametro aggiuntivo: `--incident-tag` (default: `production-incident`).

### Definizione di ripristino

Il ripristino è identificato dalla chiusura (`State = 'Closed'`) del Work Item. `CreatedDate` = momento della segnalazione, `ClosedDate` = momento del ripristino dichiarato.

### Formula — MTTR

```text
restore_time = incident.ClosedDate - incident.CreatedDate  (in ore)

avg_mttr    = mean(restore_time) su tutti gli incidenti chiusi nel periodo
median_mttr = median(restore_time)
```

**Query WIQL:**

```sql
SELECT [System.Id], [System.CreatedDate], [Microsoft.VSTS.Common.ClosedDate]
FROM WorkItems
WHERE [System.WorkItemType] IN ('Bug', 'Incident')
AND [System.Tags] CONTAINS 'production-incident'
AND [System.State] = 'Closed'
AND [Microsoft.VSTS.Common.ClosedDate] >= '<from_date>'
AND [Microsoft.VSTS.Common.ClosedDate] <= '<to_date>'
```

Il filtro è su `ClosedDate` — si misurano gli incidenti **risolti** nel periodo. Un incidente aperto prima del `--from-date` ma chiuso nel periodo viene incluso.

### Classificazione DORA — MTTR

| Livello | Soglia |
| --- | --- |
| Elite | < 1 ora |
| High | < 24 ore (1 giorno) |
| Medium | < 168 ore (1 settimana) |
| Low | >= 168 ore |

### Ipotesi e limitazioni — MTTR

- **`CreatedDate` come proxy per "inizio incidente":** se il team apre il ticket ore dopo il verificarsi del problema, il MTTR risulta sottostimato.
- **`ClosedDate` come proxy per "ripristino":** se il team chiude il ticket giorni dopo la risoluzione, il MTTR risulta sovrastimato.
- **Solo incidenti chiusi:** in un periodo di crisi con molti incidenti aperti, il MTTR misurato può essere artificialmente basso (si vedono solo quelli risolti rapidamente).
- **Cap a 200 work items:** stesso limite del Metric 3.

---

## `dora_report.py` — Report aggregato

Importa i 4 moduli come librerie Python e chiama le rispettive funzioni `compute_*`. Ogni funzione fa le sue chiamate HTTP indipendentemente (nessuna cache condivisa). Con molti deployment, il report può impiegare diversi minuti.

### Calcolo del livello complessivo

Il livello overall del team è il **livello peggiore** tra i 4:

```text
overall = worst(df.level, lt.level, cfr.level, mttr.level)
          ordinamento: Elite < High < Medium < Low
```

Le metriche con livello `N/A` vengono escluse. Se tutte sono `N/A`, il livello overall è `N/A`.

### Esempio output JSON

```json
{
  "meta": { "org": "...", "project": "...", "env_keyword": "production" },
  "deployment_frequency": {
    "total_deployments": 12,
    "total_attempted": 14,
    "per_day": 0.4,
    "dora_level": "High"
  },
  "lead_time_for_changes": { "samples": 10, "avg_hours": 4.2, "dora_level": "Elite" },
  "change_failure_rate": {
    "total_deployments": 14,
    "linked_incidents": 2,
    "cfr_percent": 14.29,
    "dora_level": "Elite"
  },
  "mttr": { "samples": 2, "avg_hours": 3.1, "dora_level": "High" },
  "overall_dora_level": "High"
}
```

---

## Riepilogo delle ipotesi critiche

| Script | Ipotesi critica | Rischio se non rispettata |
| --- | --- | --- |
| Deployment Frequency | Il deployment job YAML usa `environment:` con il keyword | Deploy non contati → frequenza sottostimata |
| Deployment Frequency | Solo pipeline multi-stage YAML con Environments | Pipeline classiche non vengono rilevate |
| Lead Time | `record.owner.id` corrisponde al build ID | Disallineamento con pipeline retry |
| Lead Time | Author date del commit riflette l'inizio del lavoro | Squash merge / rebase gonfiano il lead time |
| Change Failure Rate | Gli incidenti vengono taggati `production-incident` | Incidenti non contati → CFR artificialmente basso |
| Change Failure Rate | La causa si manifesta entro 24h dal deploy | Incidenti latenti non vengono linkati |
| MTTR | Il ticket viene aperto al momento del rilevamento | Apertura ritardata → MTTR sottostimato |
| MTTR | Il ticket viene chiuso al momento del ripristino | Chiusura ritardata → MTTR sovrastimato |

---

## Come interpretare risultati a zero

| Risultato | Causa più probabile | Azione |
| --- | --- | --- |
| `total_deployments: 0` | Nessun environment con il keyword | Controllare nomi environment su AzDO; provare `--env-keyword prod` |
| `total_deployments: 0` | Pipeline classiche senza Environments | Migrare a deployment jobs YAML con `environment:` |
| `samples: 0` (Lead Time) | Deployment senza commit associati | Pipeline trigger manuali o senza source changes |
| `linked_incidents: 0` (CFR) | Tag `production-incident` non applicato | Applicare il tag ai bug/incidenti di produzione |
| `samples: 0` (MTTR) | Nessun incidente chiuso nel periodo | O nessun incidente reale, o tickets non ancora chiusi |
| `dora_level: N/A` | Campione vuoto | Vedi righe sopra |
