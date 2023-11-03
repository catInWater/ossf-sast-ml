import os
import json
import random
import numpy as np
import torch
import tensorflow as tf
from transformers import AutoTokenizer, AutoModel
from keras import backend as K
from keras.layers import Lambda

# set random values for reproducibility
seed_value = 1337
os.environ['PYTHONHASHSEED'] = str(seed_value)
random.seed(seed_value)
np.random.seed(seed_value)
tf.random.set_seed(seed_value)
tf.compat.v1.set_random_seed(seed_value)
session_conf = tf.compat.v1.ConfigProto(intra_op_parallelism_threads=1, inter_op_parallelism_threads=1)
sess = tf.compat.v1.Session(graph=tf.compat.v1.get_default_graph(), config=session_conf)
tf.compat.v1.keras.backend.set_session(sess)


MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ensemble_models')


def _custom_f1(y_true, y_pred):
    def recall_m(y_true, y_pred):
        TP = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        Positives = K.sum(K.round(K.clip(y_true, 0, 1)))

        recall = TP / (Positives + K.epsilon())
        return recall

    def precision_m(y_true, y_pred):
        TP = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        Pred_Positives = K.sum(K.round(K.clip(y_pred, 0, 1)))

        precision = TP / (Pred_Positives + K.epsilon())
        return precision

    precision, recall = precision_m(y_true, y_pred), recall_m(y_true, y_pred)

    return 2 * ((precision * recall) / (precision + recall + K.epsilon()))


def _embed_function(model, function_string):
    tokenizer, device, tokenizer_model = model
    code_tokens = tokenizer.tokenize(function_string)
    if len(code_tokens) > 510:
        code_tokens = code_tokens[0:510]

    tokens = [tokenizer.cls_token] + code_tokens + [tokenizer.sep_token]
    tokens_ids = tokenizer.convert_tokens_to_ids(tokens)
    context_embeddings = tokenizer_model(torch.tensor(tokens_ids)[None, :].to(device))[0][0][0]
    return context_embeddings.tolist()


def _get_tokenizer_model():
    tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AutoModel.from_pretrained("microsoft/codebert-base")
    model.to(device)

    return tokenizer, device, model


def _get_inference_model(model_path=None):
    if not model_path:
        dir_name = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(dir_name, 'models/model.h5')

    model = tf.keras.models.load_model(model_path, custom_objects={"custom_f1": _custom_f1})
    model.add(Lambda(lambda x: K.cast(K.argmax(x), dtype='float32'), name='y_pred'))
    return model


def _get_inference_models(dir_name=None):
    if not dir_name:
        dir_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ensemble_models')

    models = []
    for model_file in [os.path.join(dir_name, f) for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))]:
        models.append(_get_inference_model(model_path=model_file))

    return models


def _get_prediction(models, embeddings):
    # the embeddings parameter is always a list with exactly one element, but
    # this is the format that keras expects for inference, so we need to run
    # the prediction on the list, then get the first element of the result
    model_predictions = [m.predict(embeddings)[0] for m in models]
    return int(round(sum(model_predictions)/len(model_predictions)))


def predict(function_body):
    tokenizer_model = _get_tokenizer_model()
    inference_models = _get_inference_models(MODELS_DIR)

    vector = _embed_function(model=tokenizer_model, function_string=function_body)
    prediction = _get_prediction(models=inference_models, embeddings=[vector])

    return prediction


if __name__ == "__main__":
    with open("test.json", 'r', encoding='utf-8') as f:
        test_function_body = json.load(f)[0]["messages"][0]["functionBody"]

    result = predict(test_function_body)
    print(result)
