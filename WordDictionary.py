import os, json, sys, imp, glob, itertools
import re, nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from konlpy.tag import Okt
from keras.preprocessing.sequence import pad_sequences
from TranslatorManager import TranslatorManager

class WordDictionary:
    def __init__(self):
        self.word_dic = {"_MAX":0}
        self.okt = Okt()
        self.root_dir = 'emotionData'
        self.language = 'ko'
    
    def LoadDictionary(self, language = 'ko'):
        self.language = language
        dic_file = self.root_dir + "/word-dic_{0}.json".format(language)
        if os.path.exists(dic_file):
            with open(dic_file, 'r') as f:
                self.word_dic = json.loads(f.read(), encoding='utf-8')
        else:
            self.register_dic()
            with open(dic_file, 'w') as f:
                f.write(json.dumps(self.word_dic, ensure_ascii=False))


    def Load(self, max_line_cnt, language = 'ko'):
        self.LoadDictionary(language)
        data_file = self.root_dir + "/data_{0}_line_{1}.json".format(max_line_cnt, self.language)
        
        if not os.path.exists(data_file):
            X, Y = self.count_freq(max_line_cnt)
            json.dump({'X':X, 'Y':Y}, open(data_file, 'w'))

        print('WordDictionary load complete!')

    def LoadforLSTM(self, max_len, add_line = 10):
        self.LoadDictionary()
        data_file = self.root_dir + "/lstm_data.json"

        if not os.path.exists(data_file):
            X, Y, X_Length = self.get_data_set(max_len, add_line)
            json.dump({'X':X, 'Y':Y, 'X_Length':X_Length}, open(data_file, 'w'))

        print('WordDictionary load complete!')
    
    def GetDictionaryCnt(self):
        return self.word_dic["_MAX"]

    def CreateEmotionData(self, language = 'ko'):
        with open('data/isear_output_{0}_total.txt'.format(language), 'r') as f:
            lines = f.readlines()
            for line in lines:
                arr = line.split(',')
                name = arr[0]
                cat = arr[2]
                text = arr[1].replace('\n','')
                text = self.pos(text)
                print(text)
                directory_path = self.root_dir + '/' + cat + '_' + language
                if not(os.path.isdir(directory_path)):
                    os.makedirs(os.path.join(directory_path))
                with open(directory_path + "/" + name + ".txt", 'w') as f2:
                    f2.write(text)

    def GetInputData(self, text, prev_language='ko'):
        text = self.pos_with_language(text, prev_language)

        if 'ko' == prev_language:
            translatorManager = TranslatorManager()
            text = translatorManager.Translate(text).text
            print(text)
            

            '''
            words = text.split()
            arr = []
            for word in words:
                word = translatorManager.Translate(word).text
                word = self.pos(word)
                arr.append(word)

            text = (" ".join(arr)).strip()
            '''
        

        cnt = [0 for n in range(self.word_dic["_MAX"])]
        ids = self.text_to_ids(text, False)
        print(ids)
        print(len(cnt))
        for wid in ids:
            cnt[wid] += 1
        return cnt
    def isStopWord(self, word):
        if word[1] in ["Josa", "Eomi", "Punctuation", 'Foreign','Suffix']: return True
        if word[1] == "Noun" and len(word[0]) == 1: return True
        return False

    def pos_with_language(self, text, language):
        r = []

        if language == 'ko':
            malist = self.okt.pos(text)
            print(malist)
            for word in malist:
                if not self.isStopWord(word):
                    r.append(word[0])

        elif language == 'en':
            text = re.sub('[^a-zA-Z]', ' ', text).lower()
            r = text.split()
            stemmer = nltk.stem.PorterStemmer()
            wordnet_lemmatizer = WordNetLemmatizer()
            # Stemming & Lemmatisation
            r = [wordnet_lemmatizer.lemmatize(stemmer.stem(w)) for w in r if not w in stopwords.words('english')]

        rl = (" ".join(r)).lstrip().replace('#', '')
        return rl

    def pos(self, text):
        return self.pos_with_language(text, self.language)

    def LoadISEAR(self, isTranslate):
        file_path = 'data/isear_data.txt'
        output_path = 'data/isear_output_eng.txt'

        translator = TranslatorManager()
        
        f = open(file_path, 'r')
        f2 = open(output_path, 'a')
        lines = f.readlines()
        cnt = 1
        for line in lines:
            arr = line.split('---')
            arr[2] = arr[2].replace('"','').replace('[','').replace(']','').replace('(','').replace(')','').replace(',','')
            if True == isTranslate: arr[2] = translator.Translate(arr[2], dest='ko').text
            f2.writelines('{0},{1},{2}'.format(arr[0],arr[1],arr[2]))
            cnt += 1
        f.close()
        f2.close()

    def text_to_ids(self, text, isAdd = True):
        text = text.strip().lower()
        #words = text.split(" ")
        words = self.pos(text).split(" ")
        
        result = []
        for n in words:
            wid = -1
            n = n.strip()
            if n == "": continue
            if "@" in n: continue
            if "http://" in n: continue
            if not n in self.word_dic:
                if(isAdd):
                    wid = self.word_dic[n] = self.word_dic["_MAX"]
                    self.word_dic["_MAX"] += 1
                    print('Add index/word',wid, n)
            else: 
                wid = self.word_dic[n]
                print('Get index/word',wid, n)
            
            if not wid == -1: result.append(wid)
        return result

    def file_to_ids(self, fname):
        with open(fname, 'r') as f:
            #text = self.pos(f.read())
            text = f.read()
            return self.text_to_ids(str(text))

    def register_dic(self):
        files = glob.glob(self.root_dir+"/*/*.txt")
        for i in files:
            self.file_to_ids(i)

    def count_file_freq(self, fname):
        cnt = [0 for n in range(self.word_dic["_MAX"])]
        with open(fname,'r') as f:
            
            if self.language == 'ko':
                text = self.pos(f.read().strip())
            else:
                text = f.read()
            
            #text = f.read().strip().split()
            ids = self.text_to_ids(text)
            for wid in ids:
                cnt[wid] += 1
        return cnt

    def get_data_set(self, max_len, add_line):
        X = []
        Y = []
        X_Length = []
        cat_names = []
        #max_word_cnt = 0
        for cat in os.listdir(self.root_dir):
            cat_dir = self.root_dir + "/" + cat + "_" + self.language
            if not os.path.isdir(cat_dir): continue
            
            cat_idx = len(cat_names)
            cat_names.append(cat)
            files = glob.glob(cat_dir + "/*.txt")

            cnt_line = 0
            encode = []

            for path in files:
                with open(path,'r') as f:
                    text = f.read().strip()
                    encode.append(self.encode_sentence(text))
                    '''
                    if max_word_cnt < length: 
                        max_word_cnt = length
                    '''
                    cnt_line += 1
                    if cnt_line >= add_line:
                        factorial_list = self.GetFactorialList(encode)
                        for item in factorial_list:
                            X.append(item)
                            Y.append(cat_idx)
                        encode = []
                        cnt_line = 0
        for i in range(len(X)):
            #X[i], seq_length = self.sequence_padding(X[i], max_word_cnt)
            seq_length = len(X[i])
            X_Length.append(seq_length)

        X = pad_sequences(X, maxlen=max_len).tolist()
        return X, Y, X_Length

    def GetFactorialList(self, word_list):
        mypermuatation =  list(itertools.permutations(word_list))
        get_list = []
        ret = []
        for i in range(0, len(mypermuatation)):
            get_list.append([item for item in mypermuatation[i]])

        for i in range(0, len(get_list)):
            add_list = []
            for item in get_list[i]:
                add_list += item
            ret.append(add_list)
        return ret

        

    def encode_sentence(self, text):
        encode = []
        words = self.pos(text)
        for word in words:
            if word in self.word_dic:
                encode.append(self.word_dic[word])
        return encode

    def sequence_padding(self, encode, max_len):
        '''
        seq_length = len(encode)
        print(seq_length)
        for i in range(seq_length,max_word_cnt):
            encode.append(0)
        return encode, seq_length
        '''
        return pad_sequences(encode, maxlen=max_len).tolist()

    def count_freq(self, max_sum_cnt, limit = 0):
        X = []
        Y = []
        max_words = self.word_dic["_MAX"]
        cat_names = []
        for cat in os.listdir(self.root_dir):
            cat_dir = self.root_dir + "/" + cat
            if not os.path.isdir(cat_dir) or not self.language in cat_dir: continue
            
            cat_idx = len(cat_names)
            cat_names.append(cat)
            files = glob.glob(cat_dir + "/*.txt")
            i = 0

            sum_data = []
            sum_cnt = 0
            for path in files:
                cnt = self.count_file_freq(path)
                if len(sum_data) == 0:
                    sum_data = cnt
                else:
                    sum_data = [sum_data[i]+cnt[i] for i in range(len(sum_data))]

                sum_cnt += 1

                if sum_cnt >= max_sum_cnt:
                    X.append(sum_data)
                    Y.append(cat_idx)
                    sum_data = []
                    sum_cnt = 0
                    
                if limit > 0:
                    if i > limit: break
                    i += 1
            if len(sum_data) > 0:
                X.append(sum_data)
                Y.append(cat_idx)


        return X, Y