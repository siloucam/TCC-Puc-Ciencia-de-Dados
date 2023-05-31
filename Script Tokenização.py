import string
import pandas
import psycopg2
from sqlalchemy import create_engine
import nltk
from nltk.corpus import stopwords as sw
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer, WordNetLemmatizer
import string

""" --- Conexão com o Banco --- """
host = 'localhost'
database = 'BancoDeQuestoes'
user = 'postgres'
password = 'senha23'
port = '5432'
""" ------------------ """


connection = False
try:    
    connectionBD = psycopg2.connect(user = user,
                                  password = password,
                                  host = host,
                                  port = port,
                                  database = database)

    cursorBD = connectionBD.cursor()
    # Print PostgreSQL version
    
    cursorBD.execute("SELECT version();")
    record = cursorBD.fetchone()
    print("You are connected to - ", record,"\n")
          
    engine = create_engine('postgresql://'+user+':'+password+'@'+host+'/'+database)
    
    # Para recuperar dados do banco, utilizar o pandas.read_sql
    # Ex: df = pandas.read_sql("SELECT * FROM public.aula", connectionBD)
    
    # Para recuperar dados do excel, utilizar o pandas.read_excel
    # Ex: df = pandas.read_excel('records.xlsx', sheet_name='Employees')
    
    # Para percorrer a tabela: for index, row in testesGamaGoEnem.iterrows():
        
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    
    df = pandas.read_sql("SELECT * FROM public.questao", connectionBD)
    
    for index, row in df.iterrows():
        texto = row['enunciado_raw']
        texto = texto.translate(str.maketrans("", "", string.punctuation))
        tokens = word_tokenize(texto)
        stopwords = set(sw.words('portuguese'))
        tokens_sem_stopwords = [token for token in tokens if token.lower() not in stopwords]
        tokens_normalizados = [token.lower() for token in tokens_sem_stopwords]
        stemmer = SnowballStemmer('portuguese')
        lemmatizer = WordNetLemmatizer()
        tokens_stemming = [stemmer.stem(token) for token in tokens_normalizados]
        tokens_lematizacao = [lemmatizer.lemmatize(token) for token in tokens_normalizados]
        df.at[index, 'enunciado_token'] = ' '.join(tokens_lematizacao)

    # Lista das colunas que você deseja manter
    colunas_desejadas = ['id', 'ano', 'fonte_id','disciplina_id','enunciado_token']

    # Cria um novo DataFrame com apenas as colunas desejadas
    df_subset = df[colunas_desejadas]

    # Para inserir os dados no banco
    with engine.begin() as conn:
        df_subset.to_sql('questao_token', con=conn, if_exists='replace', method='multi')
        print("Inseriu")
        
    connectionBD.commit()

    
except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)
finally:
    #closing database connection.
    if(connectionBD):
        cursorBD.close()
        connectionBD.close()
        print("PostgreSQL connection is closed")



