# Run MedAnnotate AI

## Recommended: Docker

```bash
docker compose up --build
```

Open:

```text
http://localhost:5173
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

## Create synthetic demo images

If running locally:

```bash
python scripts/generate_demo_images.py
```

Then:

1. Create a project named **Breast Ultrasound Demo**
2. Use classes: `lesion,cyst,mass`
3. Upload images from `data/demo_images`
4. Draw a box or polygon
5. Click **AI pre-annotate**
6. Review the suggested polygon
7. Click **Save annotation**
8. Export the project as COCO or YOLO
