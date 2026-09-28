# Optional AI pre-annotation model

Model weights are excluded from Git.

Place a trained binary 2-D segmentation checkpoint here:

```text
backend/models/medannotate.pt
```

Then configure:

```env
MEDANNOTATE_MODEL_PATH=backend/models/medannotate.pt
```

The provided deployment adapter is a generic MONAI 2-D U-Net. Replace
`build_model()` and/or `predict_checkpoint()` in:

```text
backend/app/services/preannotation.py
```

when connecting your own architecture.

The pre-annotation endpoint returns an editable polygon suggestion. The user
must still review and explicitly save the annotation.
