import torch
from torch.utils.data import Dataset, DataLoader
import torchaudio
from load_data import *
from transformers import Wav2Vec2Model, Wav2Vec2Processor
from icecream import ic
from transformers import AutoTokenizer, DistilBertModel

raw_data = load_all_ipus("Dataset/transcr")
filepath = "Dataset/audio/2_channels/"

wave2vec_model = "facebook/wav2vec2-base-960h"
processor = Wav2Vec2Processor.from_pretrained(wave2vec_model)
wave2vec_model = Wav2Vec2Model.from_pretrained(wave2vec_model)

bert_model = 'distilbert-base-uncased'
tokenizer = AutoTokenizer.from_pretrained(bert_model)
bert_model = DistilBertModel.from_pretrained(bert_model)

def get_audio(i, raw_data, filepath):
    audio_file_path =  filepath + raw_data["dyad"][i].replace("transcr\\","") + ".wav"
    audio_tensor, frame_rate = torchaudio.load(audio_file_path)
    stop = int(frame_rate*raw_data["stop"][i])
    start = stop-frame_rate*1
    if start < 0:
        sample_tensor = audio_tensor[:,0:stop]
        sample_tensor = torch.cat((torch.zeros((2,abs(start))),sample_tensor),dim=1)
    else:
        sample_tensor = audio_tensor[:,start:stop]
    return sample_tensor

def get_text(i, raw_data):
    text = raw_data["text"][i]
    text_tokenized = tokenizer(text, return_tensors="pt")['input_ids']
    text_tokenized = torch.cat((torch.tensor([[1026, 11687,  1028]*7]),text_tokenized),dim=1)
    text_tokenized = text_tokenized[:,-20:]
    return text_tokenized.squeeze(0)

def get_label(i, raw_data):
    return raw_data["turn_after"].astype("float32")[i]

class DataGenerator(Dataset):
    
    def __init__(self, raw_data, filepath):
        self.raw_data = raw_data
        self.filepath = filepath
    
    def __getitem__(self, i):
        return {"audio" : get_audio(i, self.raw_data, self.filepath),
                "text" : get_text(i, self.raw_data),
                "label" : get_label(i, self.raw_data)}
        
    def __len__(self):
        return len(self.raw_data)
    
def create_dataloader(raw_data, filepath):
    
    generator = DataGenerator(raw_data, 
                              filepath)
    
    dataloader = DataLoader(generator,
                            batch_size=32,
                            shuffle=True,
                            drop_last=True,)
    
    return dataloader

