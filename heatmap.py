from typing import List
from typing import Tuple
import tempfile
from pathlib import Path
import torch
from IPython.display import display
from IPython.display import Markdown
from health_multimodal.common.visualization import plot_phrase_grounding_similarity_map
from health_multimodal.text import get_bert_inference
from health_multimodal.text.utils import BertEncoderType
from health_multimodal.image import get_image_inference
from health_multimodal.image.utils import ImageModelType
from health_multimodal.vlp import ImageTextInferenceEngine

text_inference = get_bert_inference(BertEncoderType.BIOVIL_T_BERT)
image_inference = get_image_inference(ImageModelType.BIOVIL_T)

image_text_inference = ImageTextInferenceEngine(
    image_inference_engine=image_inference,
    text_inference_engine=text_inference,
)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
image_text_inference.to(device)

def get_heatmap(uploaded_file, concept):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_path = temp_file.name
    image_embedding, size = image_inference.get_projected_patch_embeddings(temp_path)
    text_embedding = image_text_inference.text_inference_engine.get_embeddings_from_prompt(concept)
    similarity_map = image_text_inference._get_similarity_map_from_embeddings(image_embedding, text_embedding)
    return similarity_map