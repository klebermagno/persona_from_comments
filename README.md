# YouTube Comment Persona Generator

Este produto utiliza 2 serviços externos. Do YouTube e do Namsor.
Dessa forma, é preciso definir as variáveis de ambiente:

* YOUTUBE_DEVELOPER_KEY
* NAMSOR_KEY

## Instalação

1. Crie um ambiente virtual (virtualenv) e ative-o:
```
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

2. Instale as bibliotecas necessárias:
```
pip install -r requirements.txt
```

3. Inicialize o banco de dados:
```
python db_manager.py
```

4. Baixe os corpora NLTK:
```
python -m textblob.download_corpora
```

## Uso via Linha de Comando

```
python main.py <ID_DO_VIDEO>
```

Ao finalizar, será gerado um arquivo chamado "output/Report-<ID_DO_VIDEO>.html".

## Interface Web

Uma interface web está disponível para facilitar o uso:

```
python app.py
```

Acesse a interface no navegador em `http://127.0.0.1:7860/` e:

1. Insira o ID do vídeo do YouTube
2. Clique em "Generate Persona"
3. Visualize o resultado e acesse o relatório completo

Você também pode ver todas as personas já geradas clicando em "List Previous Personas".