import os
import blah
import pdfminer

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams
from pdfminer.layout import LTTextBoxHorizontal, LTChar

import pandas
import psycopg2
from sqlalchemy import create_engine
import numpy

# from pdfminer.high_level import extract_pages

class Element:
  def __init__(self, texto, char):
    self.texto = texto
    self.char = char
    
class Questao:
  def __init__(self, referenciaOriginal, arquivoOrigem):
    self.referenciaOriginal = referenciaOriginal
    self.arquivoOrigem = arquivoOrigem
    self.enunciado = ''
    self.alternativas = []
  def adicionaAlternativa(self,a,letra):
    self.alternativas.append(Alternativa(letra,a))
    
class Alternativa:
    def __init__(self, letra, texto):
        self.letra = letra
        self.enunciado = texto
    
    
"-------------------------PARAMS-------------------------------"
fonteId = 1051
dataCriacao = '2021-01-11 03:00:00'
tratarIdiomasEnem = True
inserir = False
    
questoes = dict([])

print(pdfminer.__version__)  

""" Chama a janela para seleção de um arquivo """
blah_result = blah.gui_fname().decode("utf-8") 
print("Selected file: ")
print(blah_result)

""" Pega o diretório do arquivo selecionado """
directory_index = blah_result.rindex('/')
directory = blah_result[0:directory_index]
print("Directory: ")
print(directory)

""" Pega todos os arquivos do diretório selecionado """
files = os.listdir(directory)

""" Pega os arquivos e separa apenas os que são pdf """
pdffiles = [] #Cria uma lista vazia para adicionar os arquivos que forem pdf 
for file in files:
    # A função find retorna a posição onde se encontra o texto '.pdf', e caso não encontra, retorna -1.
    # Portanto se o resultado for diferente de -1, significa que ela achou o .pdf no nome do arquivo 
    if file.find('.pdf') != -1: 
        pdffiles.append(file)
        
for file in pdffiles:
    print("Processando " + file[0:-3] + "...")

    fin = open(directory + '/' + file, "rb")
    
    elements = []
    
    #Create resource manager
    rsrcmgr = PDFResourceManager()
    # Set parameters for analysis.
    laparams = LAParams()
    # Create a PDF page aggregator object.
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(fin):
        interpreter.process_page(page)
        # receive the LTPage object for the page.
        layout = device.get_result()
        for element in layout:
            if isinstance(element, LTTextBoxHorizontal):
                for text_line in element:
                    char = ''
                    for character in text_line:
                        if isinstance(character, LTChar):
                            char = character
                            break
                    elements.append(Element(text_line.get_text(), char))
    
    #Variaveis para identificação da questão no loop
    dentroDaQuestao = False
    dentroDoEnunciado = False
    fimDoEnunciado = False
    dentroDaAlternativa = False
    questaoAtual = ''
    alternativaAtual = ''
    textoAlternativa = ''
    
    if(file == '2019_1_DIA.__page14.pdf'):
        print("Arquivo bugado")
    
    for element in elements:
        if 'Questão ' in element.texto:
            
            if dentroDaAlternativa:
                questoes.get(questaoAtual).adicionaAlternativa(textoAlternativa,alternativaAtual)
                dentroDaAlternativa = False
            
            questaoAtual = element.texto[0:10]
            print(questaoAtual)
            
            if tratarIdiomasEnem:
                if int(questaoAtual[-2:],10) <= 5:
                    if questaoAtual + ' Inglês' in questoes:
                        print('Espanhol')
                        questaoAtual = questaoAtual + ' Espanhol'
                    else:
                        print('Inglês')
                        questaoAtual = questaoAtual + ' Inglês'
            
            questoes[questaoAtual] = Questao(questaoAtual,file)
            dentroDoEnunciado = True
    
        elif dentroDoEnunciado:
            #verifica se chegou numa alternativa
            if(element.char.fontname == 'BTPMCG+BundesbahnPiStd-1'):
                alternativaAtual = 'A'
                textoAlternativa = element.texto[3:]
                dentroDaAlternativa = True
                dentroDoEnunciado = False
            else:
                questoes[questaoAtual].enunciado = questoes[questaoAtual].enunciado + element.texto
        
        elif dentroDaAlternativa:
            if alternativaAtual == 'A' and element.texto[0:3] == 'B  ':
                questoes.get(questaoAtual).adicionaAlternativa(textoAlternativa,alternativaAtual)
                alternativaAtual = 'B'
                textoAlternativa = element.texto[3:]
            elif alternativaAtual == 'B' and element.texto[0:3] == 'C  ':
                questoes.get(questaoAtual).adicionaAlternativa(textoAlternativa,alternativaAtual)
                alternativaAtual = 'C'
                textoAlternativa = element.texto[3:]
            elif alternativaAtual == 'C' and element.texto[0:3] == 'D  ':
                questoes.get(questaoAtual).adicionaAlternativa(textoAlternativa,alternativaAtual)
                alternativaAtual = 'D'
                textoAlternativa = element.texto[3:]
            elif alternativaAtual == 'D' and element.texto[0:3] == 'E  ':
                questoes.get(questaoAtual).adicionaAlternativa(textoAlternativa,alternativaAtual)
                alternativaAtual = 'E'
                textoAlternativa = element.texto[3:]
            else:
                textoAlternativa = textoAlternativa + element.texto
                textoAlternativa = ' '.join(textoAlternativa.strip().split('\n'))
                textoAlternativa = textoAlternativa.replace('  ', ' ')
                
                if alternativaAtual == 'E':
                    semEspacos = " ".join(element.texto.split())
                    if semEspacos[-1:] == '.':
                        questoes.get(questaoAtual).adicionaAlternativa(textoAlternativa,alternativaAtual)
                        dentroDaAlternativa = False
    
    if dentroDaAlternativa:
        questoes.get(questaoAtual).adicionaAlternativa(textoAlternativa,alternativaAtual)




# Inserção das questões no banco
connection = False
try:    
    connectionBD = psycopg2.connect(user = "postgres",
                                  password = "senha23",
                                  host = "localhost",
                                  port = "5432",
                                  database = "BancoDeQuestoes")


    cursorBD = connectionBD.cursor()
    # Print PostgreSQL version
    
    cursorBD.execute("SELECT version();")
    record = cursorBD.fetchone()
    print("You are connected to - ", record,"\n")
          
    engine = create_engine('postgresql://postgres:senha23@localhost:5432/BancoDeQuestoes')
    
    # 1. Descobrir qual o ultimo ID utilizado, para questão e para alternativa
    ultimaQuestao = pandas.read_sql('SELECT id FROM public.questao ORDER BY id DESC LIMIT 1;', connectionBD)
    ultimaAlternativa = pandas.read_sql('SELECT id FROM public.alternativa ORDER BY id DESC LIMIT 1;', connectionBD)
        
    proximaQuestao = ultimaQuestao.at[0,'id'] + 1
    proximaAlternativa = ultimaAlternativa.at[0,'id'] + 1
    
    # 2. Monta os DataFrames já com a mesma estrutura do banco
    dfQuestao = pandas.read_sql('SELECT * FROM public.questao LIMIT 0;', connectionBD)
    dfAlternativa = pandas.read_sql('SELECT * FROM public.alternativa LIMIT 0;', connectionBD)
    
    for key, value in questoes.items():
        dfQuestao = dfQuestao.append(dict(zip(dfQuestao.columns,[proximaQuestao,value.enunciado,None,None,None,None,'MULTIPLAESCOLHA',None,'AGUARDANDO_PRIMEIRA_ANALISE',dataCriacao,int(pdffiles[0][0:4], base=10),value.referenciaOriginal,value.arquivoOrigem,fonteId])), ignore_index=True)
        for alternativa in value.alternativas:
            dfAlternativa = dfAlternativa.append(dict(zip(dfAlternativa.columns,[proximaAlternativa,alternativa.enunciado,None,None,None,False,alternativa.letra,proximaQuestao])), ignore_index=True)
            proximaAlternativa += 1
        proximaQuestao += 1
        
    dfQuestao = dfQuestao.set_index('id')  
    dfAlternativa = dfAlternativa.set_index('id')  
        
    if inserir:
        with engine.begin() as conn:
            dfQuestao.to_sql('questao', con=conn, if_exists='append')
            print("Inseriu Questoes")
            dfAlternativa.to_sql('alternativa', con=conn, if_exists='append')
            print("Inseriu Alternativas")
    

    connectionBD.commit()

    
except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)
finally:
    #closing database connection.
    if(connectionBD):
        cursorBD.close()
        connectionBD.close()
        print("PostgreSQL connection is closed")









