import spacy
from spacy.training.example import Example
import json
from pathlib import Path
from spacy.util import minibatch
import random

# Load data
train_file = Path(r"D:/MonHocKi2_2025/Big_Data/Nhom6_Video_Project_FinalBigData/Nhom6_Final_ProjectBigData/Handel_Data_Windows/CleanData/TrainModel/modeltrain_extracted.json")
train_data = json.loads(train_file.read_text(encoding="utf-8"))

# Convert to spaCy format
TRAIN_DATA = []
for item in train_data:
    TRAIN_DATA.append((item["text"], {"entities": item["entities"]}))


nlp = spacy.blank("vi")  # hoặc "en" nếu tiếng Anh

for i in range(20):  # số epoch
    random.shuffle(TRAIN_DATA)
    losses = {}
    batches = minibatch(TRAIN_DATA, size=2)
    for batch in batches:
        for text, annotations in batch:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            nlp.update([example], losses=losses)
    print(f"Epoch {i + 1}, Losses: {losses}")
    
# Thêm pipeline NER
if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
else:
    ner = nlp.get_pipe("ner")

# Thêm các label
for _, annotations in TRAIN_DATA:
    for ent in annotations["entities"]:
        ner.add_label(ent[2])
        
#  Huấn luyện
nlp.begin_training()
for i in range(20):  # số epoch
    random.shuffle(TRAIN_DATA)
    losses = {}
    batches = minibatch(TRAIN_DATA, size=2)
    for batch in batches:
        for text, annotations in batch:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            nlp.update([example], losses=losses)
    print(f"Epoch {i + 1}, Losses: {losses}")

# Lưu model
output_dir = Path(r"D:/MonHocKi2_2025/Big_Data/Nhom6_Video_Project_FinalBigData/Nhom6_Final_ProjectBigData/Handel_Data_Windows/CleanData/checkpoint")
output_dir.mkdir(exist_ok=True)
nlp.to_disk(output_dir)
print(f"✅ Model saved to {output_dir.resolve()}")