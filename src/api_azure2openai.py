import os
import requests
import json
import openai

openai.api_key = "APIKEY"
openai.api_base = "https://cog-r64zdcyjshwjk.openai.azure.com/"
openai.api_type =  'azure'
openai.api_version = '2023-05-15'
model_name = ['gpt-35-turbo-mic', 'davinci','embedding','chat']

class API():
    
    def __init__(self, model, entry, tokens, temperatura):
        
        super().__init__()
        self.model = model
        self.prompt = entry
        self.entry = entry
        self.token = tokens
        self.temperature = temperatura

    def response_code(self):

        response = openai.Completion.create(
            engine = self.model,
            prompt = self.entry,
            max_tokens = self.token,
            n = 1,
            stop = None,
            temperature = self.temperature,
        )
        return response


if __name__ == '__main__':

    api = API('davinci', "Donut", 100, 0.5)
    t = api.response_code()
    print(t)