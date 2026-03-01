from pathlib import Path
import json

import numpy as np
import torch
import torch.nn.functional as F
import streamlit as st
from PIL import Image

from src.models.bacteria_cnn import create_bacteria_model
from src.utils.image_preprocessing import preprocess_image, detect_rod_shapes

PROJECT_ROOT = Path(__file__).resolve().parent
ARTIFACTS_PATH = PROJECT_ROOT / "artifacts" / "bacteria_classifier.pt"
TAXONOMY_PATH = PROJECT_ROOT / "artifacts" / "taxonomy.json"

@st.cache_resource
def load_model_and_mapping():
    if not ARTIFACTS_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {ARTIFACTS_PATH}")

    checkpoint = torch.load(ARTIFACTS_PATH, map_location="cpu")
    label_mapping = checkpoint.get("label_mapping")
    num_classes = len(label_mapping)

    model = create_bacteria_model(
        num_classes=num_classes,
        backbone="resnet18",
        pretrained=False,
        in_channels=1,
    )
    model.load_state_dict(checkpoint["model_state_dict"]) 
    model.eval()

    inv_mapping = {idx: name for name, idx in label_mapping.items()}
    return model, inv_mapping

@st.cache_data
def load_taxonomy():
    if TAXONOMY_PATH.exists():
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

model, inv_mapping = load_model_and_mapping()
taxonomy = load_taxonomy()

st.title("Bacteria classifier — Streamlit demo")
st.write("Загрузите изображение микроскопа, чтобы увидеть предсказание и простую морфологическую оценку.")

uploaded = st.file_uploader("Выберите изображение", type=["png", "jpg", "jpeg", "tif", "bmp"]) 

if uploaded is not None:
    img = Image.open(uploaded).convert("RGB")
    img_np = np.array(img)[:, :, ::-1]  # RGB -> BGR for OpenCV pipeline

    st.image(img, caption="Загруженное изображение", use_column_width=True)

    with st.spinner("Обрабатываю изображение и выполняю предсказание..."):
        proc = preprocess_image(img_np)
        tensor = torch.from_numpy(proc).float().unsqueeze(0)  # (1, C, H, W)

        with torch.no_grad():
            logits = model(tensor)
            probs = F.softmax(logits, dim=1)
            pred_idx = int(probs.argmax(dim=1).item())
            confidence = float(probs[0, pred_idx].item())
            predicted_class = inv_mapping.get(pred_idx, str(pred_idx))

        shape_info = detect_rod_shapes(proc)

    st.markdown(f"**Предсказанный класс:** `{predicted_class}`  — {confidence:.2%} уверенности")

    st.subheader("Морфология")
    st.write(f"Наличие палочковидных форм: **{shape_info.get('has_rod')}**")
    st.write(f"Оценочное количество палочек: **{shape_info.get('rod_count')}**")

    st.subheader("Таксономия (если есть)")
    cls_key = predicted_class
    tax = taxonomy.get(cls_key) or {}
    if tax:
        st.write(f"**Семейство:** {tax.get('family','-')}")
        st.write(f"**Род:** {tax.get('genus','-')}")
        st.write(f"**Вид:** {tax.get('species','-')}")
    else:
        st.write("Нет информации о таксономии для этого класса.")

    st.success("Готово")

    if st.button("Показать подробности (JSON)"):
        st.json({
            "predicted_class": predicted_class,
            "confidence": confidence,
            "shape": shape_info,
            "taxonomy": tax,
        })
