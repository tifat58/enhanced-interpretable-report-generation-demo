# Demonstrating Enhanced Interpretability in Radiology Report Generation with Multi-Agent RAG and Concept Bottleneck Models



## Overview
This is the official repository for the paper titled **'CBM-RAG: Demonstrating Enhanced Interpretability in Radiology Report Generation with Multi-Agent RAG and Concept Bottleneck Models'**, accepted in the **17th ACM SIGCHI Symposium on Engineering Interactive Computing Systems (EICS 2025)**

- Paper Link: https://dl.acm.org/doi/10.1145/3731406.3731970
- preprint: https://arxiv.org/abs/2504.20898


This project implements a system for generating interpretable radiology reports using a combination of Multi-Agent Retrieval-Augmented Generation (RAG) and Concept Bottleneck Models (CBM). The application focuses on chest X-ray (CXR) analysis and classification into three categories: Pneumonia, COVID-19, and Normal, providing concept-level interpretability and heatmaps for enhanced understanding of classification results.

## Key Features

- **Concept Bottleneck Mechanism:** Extracts and normalizes concept vectors to classify CXR images.
- **Heatmap Generation:** Uses BioViL for spatial similarity heatmaps, highlighting critical regions in CXR images.
- **Multi-Agent RAG System:** Includes specialized agents for pneumonia, COVID-19, and normal conditions, with additional agents for radiology interpretation and report writing.
- **Integration with Clinical Context:** Supports ingestion of additional documentation and multimedia files, enabling enhanced and context-aware report generation.

## Approach

1. **Concept Bottleneck Mechanism:**

   - Extracts image embeddings from CheXAgent.
   - Uses Mistral to embed concepts into high-dimensional text vectors.
   - Calculates cosine similarity to form a concept vector, normalized for interpretability.
   - Classifies images into one of three categories using a fully connected layer.
   - Generates contribution scores to quantify each concept's impact on classification.

2. **Heatmap Visualization:**

   - Employs BioViL to generate spatial similarity maps, converted into interpretable heatmaps.
   - Highlights regions of interest corresponding to specific medical concepts.

3. **Radiology Report Generation:**

   - Utilizes a multi-agent RAG system for structured and interpretable report creation.
   - Integrates clinical documentation using a vector database and OpenAI Whisper for multimedia transcription.

## System Requirements

- **Python:** 3.9+
- **Dependencies:** See `requirements.txt` for a complete list of required packages.
- **Hardware:** GPU recommended for faster image and text embedding computation.

## Setup

Set up environment variables in `.env` file:
   ```plaintext
   OPENAI_API_KEY=
   MISTRAL_API_KEY=
   ```

## Usage

### Launch the Application

Run the Streamlit app:

```bash
streamlit run app.py
```

## Workflow

1. **Upload an Image:**
   - Select a sample image or upload your own chest X-ray image.
2. **View Predictions:**
   - The model predicts the classification and highlights the most significant concepts contributing to the decision.
3. **Generate Heatmaps:**
   - Visualize heatmaps for specific concepts to understand localized areas of interest.
4. **Enhance Report Context:**
   - Upload additional clinical files or media for richer context in the generated report.
5. **Radiology Report:**
   - View the detailed, context-aware radiology report created by the multi-agent RAG system.

## Directory Structure

- **`app.py`**: Main application script.
- **`cbm_data_prep.py`**: Prepares data for the concept bottleneck model.
- **`cbm_inference_app.py`**: Handles concept similarity vector inference.
- **`cbm_linear_layer.py`**: Defines and trains the classification model.
- **`concepts.py`**: Contains predefined medical concepts.
- **`heatmap.py`**: Generates heatmaps for selected concepts.
- **`rag.py`**: Implements the multi-agent RAG system for report generation.
- **`utils.py`**: Utility functions for file simulation and transcription.
- **`config.py`**: Configuration settings for the classification model.

## Citation
If you are using the code or the results in your research, please cite"
```
@inproceedings{alam2025cbm,
  title={CBM-RAG: Demonstrating Enhanced Interpretability in Radiology Report Generation with Multi-Agent RAG and Concept Bottleneck Models},
  author={Alam, Hasan Md Tusfiqur and Srivastav, Devansh and Mohamed Selim, Abdulrahman and Kadir, Md Abdul and Shuvo, Md Moktadirul Hoque and Sonntag, Daniel},
  booktitle={Companion Proceedings of the 17th ACM SIGCHI Symposium on Engineering Interactive Computing Systems},
  pages={59--61},
  year={2025}
}
```

## Acknowledgements

- **[CheXAgent](https://huggingface.co/StanfordAIMI/CheXagent-8b)**: Used for extracting CXR image embeddings.
- **[BioViL](https://huggingface.co/microsoft/BiomedVLP-BioViL-T)**: Employed for spatial heatmap visualization.

