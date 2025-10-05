import spacy
from spacy.training.example import Example
import json
from pathlib import Path
from spacy.util import minibatch
import random

def remove_overlaps(entities):
    """Loại bỏ các entity trùng hoặc chồng nhau"""
    entities = sorted(entities, key=lambda x: (x[0], x[1]))
    cleaned = []
    last_end = -1
    for start, end, label in entities:
        if start >= last_end:  # không overlap
            cleaned.append((start, end, label))
            last_end = end
    return cleaned

# === Load training data ===
train_file = Path(r"./CleanData/TrainModel/modeltrain_extracted_label.json")
train_data = json.loads(train_file.read_text(encoding="utf-8"))

TRAIN_DATA = []
for item in train_data:
    ents = remove_overlaps(item["entities"])
    TRAIN_DATA.append((item["text"], {"entities": ents}))

# === Create blank model ===
nlp = spacy.blank("vi")  # hoặc "en" nếu chủ yếu tiếng Anh

# === Add NER component ===
ner = nlp.add_pipe("ner")

# === Add labels ===
for _, annotations in TRAIN_DATA:
    for start, end, label in annotations["entities"]:
        ner.add_label(label)

# === Train ===
optimizer = nlp.begin_training()
for epoch in range(20):
    random.shuffle(TRAIN_DATA)
    losses = {}
    for batch in minibatch(TRAIN_DATA, size=8):
        for text, annotations in batch:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            try:
                nlp.update([example], sgd=optimizer, losses=losses)
            except ValueError as e:
                print(f"⚠️ Bỏ qua lỗi sample: {e}")
    print(f"Epoch {epoch+1} Losses: {losses}")

# === Save model ===
output_dir = Path(r"./checkpoint")
output_dir.mkdir(exist_ok=True)
nlp.to_disk(output_dir)
print(f"✅ Model saved to {output_dir.resolve()}")
