import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from PIL import Image
import numpy as np
import torch
from sklearn.utils import shuffle
from scipy.ndimage import zoom
from io import BytesIO
import time
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SimpleNodeParser
from dotenv import load_dotenv
import os
import re
from samples import examples, samples
from concepts import pneumonia_concepts, covid19_concepts, normal_concepts, concepts
from utils import simulate_file_upload, transcribe
from rag import load_data as _load_data
from rag import generate_report
from cbm_inference_app import get_image_concept_similarity_vector
from heatmap import get_heatmap
from config import W_F, num_classes, class_mapping, num_concepts

load_dotenv()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-4'

@st.cache_resource(show_spinner=False)
def load_data(files_directory):
    return _load_data(files_directory)

pneumonia_index = load_data('docs_pneumonia')
covid_index = load_data('docs_covid')

st.set_page_config(
    page_title="Demo IML",
    layout="wide"
)

st.subheader('Demonstrating Enhanced Interpretability in Radiology Report Generation with Multi-Agent RAG and Concept Bottleneck Models')

if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False
    st.session_state.report = ""
    st.session_state.uploaded_file = None
    st.session_state.logs = ""
    st.session_state.logs_generated = False
    st.session_state.selected_image = None
    st.session_state.messages = None
    st.session_state.radio = None

selected_sample = st.selectbox("Select a sample image or upload image", ["Upload Image"] + list(examples.keys()))

if "previous_selection" not in st.session_state:
        st.session_state.previous_selection = selected_sample

if 'toggles' not in st.session_state:
    st.session_state.toggles = None

if selected_sample == "Upload Image":
    using_sample = False

if selected_sample != "Upload Image":
    if st.session_state.previous_selection != selected_sample:
        st.session_state.report_generated = False
        st.session_state.report = ""
        st.session_state.logs = ""
        st.session_state.logs_generated = False
        st.session_state.uploaded_file = None
        st.session_state.selected_image = None
        st.session_state.messages = None
        st.session_state.radio = None
        st.session_state.toggles = None
        st.session_state.previous_selection = selected_sample
        st.session_state.sample_delay_done = False
    uploaded_file = simulate_file_upload(examples[selected_sample])
    st.session_state.uploaded_file = uploaded_file
    st.session_state.report_generated = True
    st.session_state.report = samples[examples[selected_sample]]["report"]
    st.session_state.logs = samples[examples[selected_sample]]["logs"]
    st.session_state.logs_generated = True
    st.session_state.radio = 1
    using_sample = True
    if not st.session_state.get("sample_delay_done", False):
        with st.spinner("Loading sample..."):
            time.sleep(2)  
        st.session_state.sample_delay_done = True

else:
    uploaded_file = st.file_uploader("Upload the chest x-ray image", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    if uploaded_file != st.session_state.uploaded_file:
        # Reset the session state for a new upload
        st.session_state.report_generated = False
        st.session_state.report = ""
        st.session_state.logs = ""
        st.session_state.logs_generated = False
        st.session_state.uploaded_file = uploaded_file
        st.session_state.nodes = False
        st.session_state.selected_image = None
        st.session_state.messages = None
        st.session_state.radio = None
        st.session_state.toggles = None

    r = get_image_concept_similarity_vector(uploaded_file)
    predicted_class = torch.argmax(torch.nn.functional.softmax(torch.matmul(r, W_F.T), dim=0)).item()
    contribution = W_F * r
    contribution = contribution.detach().numpy()
    conc, cont = shuffle(concepts, contribution[predicted_class])
    paired_lists = list(zip(conc, cont))
    sorted_paired_lists = sorted(paired_lists, key=lambda x: abs(x[1]), reverse=True)
    sorted_concepts, sorted_contributions = zip(*sorted_paired_lists)
    sorted_concepts = list(sorted_concepts)
    sorted_contributions = list(sorted_contributions)
    st.session_state.contributions = sorted_contributions
    st.session_state.toggles = {concept: False for concept in sorted_concepts}

    col1, col2, col3 = st.columns([0.2, 0.5, 0.3])

    with col1:
        if predicted_class != 2:
            st.subheader(":blue[Prediction:] :red[{}]".format(class_mapping[predicted_class]))
        else:
            st.subheader(":blue[Prediction:] :green[{}]".format(class_mapping[predicted_class]))
        img = Image.open(uploaded_file)
        img = np.array(img)
        if st.session_state.selected_image is None:
            st.session_state.selected_image = img
        st.image(st.session_state.selected_image, width=300)

        if not np.array_equal(st.session_state.selected_image, img):
            opacity = st.slider('Overlay Opacity', 0.0, 1.0, 0.3)

        top_k = st.slider('Top K Concepts', 1, len(conc), 5)

        if 'editable' not in st.session_state:
            st.session_state.editable = False

        subcol1, subcol2 = st.columns([0.65, 0.35])

        with subcol1:
            if st.button('Edit Contribution'):
                st.session_state.editable = not st.session_state.editable
        
        with subcol2:
            if st.button("Reset Image"):
                st.session_state.selected_image = img

        st.markdown(":blue[<b>Concepts Scores</b>]", unsafe_allow_html=True)

        with st.container(height=500):
            updated_values = []
            for i in range(top_k):
                concept_name = sorted_concepts[i]
                is_active = st.session_state.toggles[concept_name]
                if st.session_state.contributions[i] <=0:
                    disable_toggle = True
                else:
                    disable_toggle = False
                toggle = st.toggle(concept_name, disabled = disable_toggle)
                if toggle:
                    for other_concept in sorted_concepts:
                        if other_concept != concept_name:
                            st.session_state.toggles[other_concept] = False
                    st.session_state.toggles[concept_name] = True
                    heat_map = get_heatmap(uploaded_file, concept_name)
                    upsampled_similarity_map = zoom(heat_map, (256 / 14, 256 / 14), order=1)
                    normalized_similarity_map = (upsampled_similarity_map - upsampled_similarity_map.min()) / \
                                                (upsampled_similarity_map.max() - upsampled_similarity_map.min())
                    threshold = 0.75
                    normalized_similarity_map = np.where(normalized_similarity_map > threshold, normalized_similarity_map, np.nan)
                    alpha_value = opacity if 'opacity' in locals() or 'opacity' in globals() else 0.3
                    plt.figure(figsize=(8, 8))
                    plt.imshow(img, cmap='gray') 
                    plt.imshow(normalized_similarity_map, cmap='jet', alpha=alpha_value)
                    plt.colorbar(label="Similarity")
                    plt.axis('off')
                    buf = BytesIO()
                    plt.savefig(buf, format='png', bbox_inches='tight')
                    buf.seek(0)
                    st.session_state.selected_image = Image.open(buf)
                value = st.slider(concept_name, -0.5, 0.5, st.session_state.contributions[i], disabled=not st.session_state.editable, label_visibility='collapsed')
                updated_values.append(value)

        if st.button('Confirm Contribution Score'):
            st.session_state.editable = False
            st.session_state.contributions[:top_k] = updated_values.copy()
            with open(f'updated_contributions/{uploaded_file.name.split(".")[0]}.txt', 'w') as f:
                for concept, value in zip(sorted_concepts, st.session_state.contributions):
                    f.write(f"{concept}: {value}\n")

    with col2:
        st.write()
        if using_sample:
            st.session_state.llama_index_agent = generate_report(class_mapping, predicted_class, sorted_concepts, sorted_contributions, None, return_tool=using_sample)
        more_docs = st.radio("Do you want to add more clinical information about {} for report generation?".format(class_mapping[predicted_class]),
                            ('Yes', 'No'), index=st.session_state.radio)
        
        if more_docs == 'No':
            if not st.session_state.report_generated:
                with st.spinner("Generating report..."):
                    _, st.session_state.llama_index_agent, report, logs = generate_report(pneumonia_index, covid_index, class_mapping, predicted_class, sorted_concepts, sorted_contributions, None)
                    st.session_state.report = report
                    st.session_state.report_generated = True
                    st.session_state.logs = logs
                    st.session_state.logs_generated = True
            st.session_state.logs = re.sub(r'\x1b\[[0-9;]*m', '', st.session_state.logs)
            with st.expander("See logs for intermediate steps"):
                html = "<div style='height: 300px; overflow-y: scroll; padding: 10px'>"
                for log in st.session_state.logs.split("\n"):
                    if "[DEBUG]" in log:
                        html += f'<p style="color:blue">{log}</p>'
                    elif ">" in log:
                        html += f'<p style="color:red">{log}</p>'
                    else:
                        html += f'<p style="color:green">{log}</p>'
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
            st.markdown(":blue[<b>Generated Report</b>]", unsafe_allow_html=True)
            with st.container(height=800):
                st.markdown(st.session_state.report)
            st.markdown(":blue[<i>The report is generated based on the predicted concept contribution scores and using available clinical documentations.</i>]", unsafe_allow_html=True)

        if more_docs == 'Yes':
            uploaded_files = st.file_uploader("Choose a file", accept_multiple_files=True)
            if len(uploaded_files) != 0:
                additional_logs = ""
                transcription_bool = False
                if st.session_state.nodes == False:

                    for uploaded_file in uploaded_files:
                        if class_mapping[predicted_class] == 'Covid':
                            temp_dir = "tmp_covid"
                        if class_mapping[predicted_class] == 'Pneumonia':
                            temp_dir = "tmp_pneumonia"
                        if class_mapping[predicted_class] == 'Normal':
                            temp_dir = "tmp_normal"
                        if uploaded_file.name.endswith(('.mp3', '.mp4')):
                            transcription_bool = True
                            temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(temp_file_path, 'wb') as f:
                                f.write(uploaded_file.getbuffer())
                            
                            transcription = transcribe(temp_file_path)
                            
                            txt_filename = uploaded_file.name.rsplit('.', 1)[0] + '.txt'
                            txt_file_path = os.path.join(temp_dir, txt_filename)
                            with open(txt_file_path, 'w') as txt_file:
                                txt_file.write(transcription)
                        else:
                            file_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(file_path, 'wb') as f:
                                f.write(uploaded_file.getbuffer())

                
                    new_docs = SimpleDirectoryReader(input_dir=temp_dir, recursive=True).load_data()
                    parser = SimpleNodeParser()
                    new_nodes = parser.get_nodes_from_documents(new_docs)
                    st.session_state.nodes = True

                    if transcription_bool:
                        additional_logs += "Transcribed the media file using Whisper.\n"
                    additional_logs += "Parsed the additional documents and indexed them in the vector store.\n"

                # if st.button("Generate Report"):
                if not st.session_state.report_generated:
                    with st.spinner("Generating report..."):
                        _, st.session_state.llama_index_agent, report, logs = generate_report(pneumonia_index, covid_index, class_mapping, predicted_class, sorted_concepts, sorted_contributions, new_nodes)
                        st.session_state.report = report
                        st.session_state.report_generated = True
                        st.session_state.logs = logs
                        st.session_state.logs_generated = True

                st.session_state.logs = re.sub(r'\x1b\[[0-9;]*m', '', st.session_state.logs)
                st.session_state.logs = additional_logs + st.session_state.logs

                with st.expander("See logs for intermediate steps"):
                    html = "<div style='height: 300px; overflow-y: scroll; padding: 10px'>"
                    for log in st.session_state.logs.split("\n"):
                        if "[DEBUG]" in log:
                            html += f'<p style="color:blue">{log}</p>'
                        elif ">" in log:
                            html += f'<p style="color:red">{log}</p>'
                        else:
                            html += f'<p style="color:green">{log}</p>'
                    html += "</div>"
                    st.markdown(html, unsafe_allow_html=True)
                st.markdown(":blue[<b>Generated Report</b>]", unsafe_allow_html=True)
                with st.container(height=800):
                    st.markdown(st.session_state.report)
                st.markdown(":blue[<i>The report is generated based on the predicted concept contribution scores and using available clinical documentations.</i>]", unsafe_allow_html=True)

    with col3:
        if st.session_state.report_generated:
            with st.container(height=1100):
                if st.session_state.messages is None:
                    st.session_state.messages = [
                        {"role": "system", "content": f"You are a radiologist. The detected disease is {class_mapping[predicted_class]}. The concepts and their contributions to the classification are as follows: {sorted_concepts} and {sorted_contributions}. The higher values of contributions indicate the importance of the concepts in the classification of the disease. Negative values of contribution means the concept does not contribute for the classification. The disease has been detected based on the presence of these concepts. The radiology report for this patient has been generated as follows: {st.session_state.report}"},
                        {"role": "assistant", "content": "Ask me anything about the chest x-ray report or the disease detected."}]

                if prompt := st.chat_input("Your question"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                for message in st.session_state.messages:
                    if message["role"] == "system":
                        continue
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

                if st.session_state.messages[-1]["role"] != "assistant":
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            response = st.session_state.llama_index_agent.run(f"Question: prompt \n Previous messages: {st.session_state.messages}")
                            st.write(response)
                            message = {"role": "assistant", "content": response}
                            st.session_state.messages.append(message)