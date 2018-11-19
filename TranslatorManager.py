import requests as req
import re
import json
from googletrans import Translator

import os, sys
import urllib.request

class TranslatorManager:
    
    def __init__(self):
        self.translator = Translator(service_urls=[
            'translate.google.com',
            'translate.google.co.kr',
        ])
        self.papago_client_id = "CJRg1CXSrfwfElRaLwhm"
        self.papago_client_secret = "Wkz4haCdKk"
        
    def Translate(self, text, dest='en'):
        return self.translator.translate(text, dest)

    def Translate_Papago(self, text, source, target):
        if source == target:
            return ""

        encText = urllib.parse.quote(text)
        data = "source={0}&target={1}&text={2}".format(source, target, encText)
        url = "https://openapi.naver.com/v1/papago/n2mt"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", self.papago_client_id)
        request.add_header("X-Naver-Client-Secret", self.papago_client_secret)
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            print(response_body.decode("utf-8"))
            return response_body.decode("utf-8")
        return ""


translator = TranslatorManager()

translator.Translate_Papago("안녕하세요 평소에 바리스타룰스 커피를 즐겨마시는 사람입니다. 오늘도 평소와 같이 먹으려고 했는데 빨대가 너무 짧은 불량이 들어있어서 먹을 수가 없네요. 윗뚜껑은 잘 까지지도 않구요.. 2천원 날렸네요 아침부터.. 빨대가 아예 손바닥보다 작게 들어있어요. 빨대 불량 잘 체크해주시고 다음부터 또 이럴까봐 바리스타 안먹을거같아요.  가격이 착한 편도 아닌데 퀄리티라도 좋아야하지 않나요..?", "ko", "en")

