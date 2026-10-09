# Datos

Se usa el conjunto público **OpenNeuro ds003490** (*EEG: 3-Stim Auditory Oddball and Rest in Parkinson's*, J. F. Cavanagh, v1.1.0, DOI 10.18112/openneuro.ds003490.v1.1.0). Los EEG **no se redistribuyen** en este repositorio; su uso se rige por la licencia publicada en OpenNeuro.

## Descarga

```bash
bash scripts/download_openneuro.sh        # requiere: pip install awscli
```

Destino por defecto: `data/openneuro/ds003490/`; se cambia con `PARKINSON_EEG_DATA`.

En Windows sin `bash`, ejecute directamente en PowerShell:

```powershell
aws s3 sync --no-sign-request s3://openneuro.org/ds003490 data/openneuro/ds003490 `
  --exclude "*" --include "*.set" --include "*.fdt" --include "*.json" `
  --include "*.tsv" --include "participants.tsv" --include "README"
```

También puede descargarse manualmente desde https://openneuro.org/datasets/ds003490.

## Cohorte utilizada

Solo se analizan los segmentos de ojos cerrados de los 25 controles y de la sesión OFF de medicación de los 25 pacientes. `participants.tsv` debe incluir `participant_id`, `Group`, `sess1_Med` y `sess2_Med`. Tras el control de calidad (mínimo 6 épocas válidas) quedan 24 HC y 24 PD-OFF.

## Datos derivados

Las épocas preprocesadas (`.npy`) y las representaciones funcionales (`.npz`) se generan en `artifacts/` y están excluidas de Git (`.gitignore`).
